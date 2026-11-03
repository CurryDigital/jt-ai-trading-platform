from sqlalchemy import create_engine, event, Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, Boolean, ARRAY, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import datetime
import os
import boto3
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def get_hkt_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

# RDS Configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "aitrading")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # If empty, uses IAM auth
DB_REGION = os.getenv("DB_REGION", "ap-southeast-1")

def get_auth_token():
    """Get RDS IAM auth token or use password from env"""
    if DB_PASSWORD:
        return DB_PASSWORD
    try:
        client = boto3.client('rds', region_name=DB_REGION)
        return client.generate_db_auth_token(DBHostname=DB_HOST, Port=DB_PORT, DBUsername=DB_USER)
    except Exception as e:
        print(f"Warning: Could not generate IAM auth token: {e}")
        return None

def get_connection():
    """Create database connection using psycopg2"""
    password = get_auth_token()
    if not password:
        raise ValueError("No database password available. Set DB_PASSWORD in .env or ensure IAM auth is configured.")
    
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=password,
        database=DB_NAME, sslmode='require', connect_timeout=5,
        options='-c search_path=aitrading_schema,bronze,silver,gold,consumption -c timezone=Asia/Hong_Kong'
    )

# Build connection string for SQLAlchemy
if DB_PASSWORD:
    # Direct connection with password + SSL required + timeouts
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require&connect_timeout=5"
else:
    # Use IAM auth with creator function
    connection_string = f"postgresql://{DB_USER}@{DB_HOST}/{DB_NAME}?sslmode=require&connect_timeout=5"

# Create engine with hardened connection-pool configuration.
# When RDS is unreachable we want fast failure, not queue saturation.
engine_kwargs = dict(
    pool_size=6,           # accommodate 4 persistent singletons + 2 for API
    max_overflow=4,        # burst capacity for concurrent API requests
    pool_timeout=10,       # allow time for pool recovery under load
    pool_recycle=1800,     # recycle every 30 min (IAM token TTL)
    pool_pre_ping=True,    # drop stale connections before checkout
    echo=False,
    connect_args={"connect_timeout": 5},  # fail fast at TCP level
)

if DB_PASSWORD:
    engine = create_engine(connection_string, **engine_kwargs)
else:
    engine = create_engine(
        connection_string,
        creator=get_connection,
        **engine_kwargs,
    )

# --- Runaway-query guardrails (incident t_96e90169, 2026-11-03) -----------
# Client aborts do NOT cancel server-side queries for sync (threadpool)
# routes — the request keeps running to completion and the PG backend keeps
# executing. The DB itself must therefore bound statement runtime:
#   * statement_timeout 8s sits under the frontend's 10s abort, so a runaway
#     query errors fast (SQLSTATE 57014) instead of accumulating into a
#     pile-up that saturates RDS.
#   * idle_in_transaction_session_timeout reclaims connections whose client
#     vanished mid-transaction.
# Applied on every new DBAPI connection (covers both the password DSN path
# and the IAM `creator` path above). A session that legitimately needs a
# longer budget can override locally with `SET statement_timeout = ...`.
DB_STATEMENT_TIMEOUT_MS = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "8000"))
DB_IDLE_TX_TIMEOUT_MS = int(os.getenv("DB_IDLE_TX_TIMEOUT_MS", "30000"))

@event.listens_for(engine, "connect")
def _set_session_timeouts(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(f"SET statement_timeout = {DB_STATEMENT_TIMEOUT_MS}")
        cursor.execute(
            f"SET idle_in_transaction_session_timeout = {DB_IDLE_TX_TIMEOUT_MS}"
        )
    finally:
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- BRONZE SCHEMA ---
class RawStockData(Base):
    __tablename__ = "raw_stock_data"
    __table_args__ = {"schema": "bronze"}
    date = Column(DateTime, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), index=True)
    open = Column(Float); high = Column(Float); low = Column(Float); close = Column(Float); volume = Column(Float)
    ingested_at = Column(DateTime, default=get_hkt_now)

# --- SILVER SCHEMA ---
class HistoricalStockData(Base):
    __tablename__ = "historical_stock_data"
    __table_args__ = {"schema": "silver"}
    date = Column(DateTime, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), index=True)
    open = Column(Float); high = Column(Float); low = Column(Float); close = Column(Float); volume = Column(Float)
    returns = Column(Float)

# --- GOLD SCHEMA ---
class StockMetrics(Base):
    __tablename__ = "stock_metrics"
    __table_args__ = {"schema": "gold"}
    date = Column(DateTime, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), index=True)
    sector = Column(String(50))
    rsi_14 = Column(Float); pe_ratio_ttm = Column(Float); prophet_forecast = Column(Float)

class KeyEntitiesConfig(Base):
    __tablename__ = "llm_key_entities_config"
    __table_args__ = {"schema": "gold"}
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    name = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)

# --- CONSUMPTION SCHEMA ---
class GlobalState(Base):
    __tablename__ = "global_state"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True)
    value = Column(Text)
    category = Column(String(50))
    rationale = Column(Text)
    estimates = Column(JSON)

class StrategyThreshold(Base):
    __tablename__ = "strategy_thresholds"
    __table_args__ = {"schema": "gold"}
    id = Column(Integer, primary_key=True)
    horizon = Column(String(20), unique=True) # 1D, 1W, 1M
    target_pct = Column(Float)
    win_criteria_days = Column(Integer)
    is_active = Column(Boolean, default=True)

class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = {"schema": "consumption"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_date = Column(DateTime, default=get_hkt_now)
    ticker = Column(String(20), index=True)
    asset_class = Column(String(20)) # STOCK, FX, CRYPTO, COMMODITY
    quantity = Column(Float); buy_price = Column(Float); current_price = Column(Float); win_loss = Column(String(20))
    est_1d = Column(String(20)); est_7d = Column(String(20)); est_1m = Column(String(20))
    analysis = Column(JSON); status = Column(String(20), default="held")

class ConsumptionStock(Base):
    __tablename__ = "stock"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20)); market = Column(String(10)); horizon = Column(String(20))
    close_price = Column(Float); daily_change = Column(Float)
    final_score = Column(Float)
    est_1d = Column(String(20)); est_7d = Column(String(20)); est_1m = Column(String(20))
    stop_loss = Column(String(20)); rr_ratio = Column(String(20)); vol_category = Column(String(10))
    signal_age = Column(String(20)); sparkline = Column(JSON); confidence_drivers = Column(JSON)
    metrics = Column(JSON); logic_summary = Column(Text); logic_badges = Column(JSON); trad_confidence = Column(Float); swarm_confidence = Column(Float)
    win_rate = Column(Float); strategy_tags = Column(JSON)
    candlestick_pattern = Column(String(100))

class ConsumptionMarket(Base):
    __tablename__ = "market"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    sector = Column(String); ticker = Column(String(20)); name = Column(String)
    edge_score = Column(String); est_1d = Column(String); est_1m = Column(String)
    market_mood = Column(String); contrarian_buy_signal = Column(Text); swarm_conclusion = Column(Text)

class ConsumptionFx(Base):
    __tablename__ = "fx"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(String(20)); action = Column(String(10)); confidence = Column(Float)
    close_price = Column(Float); daily_change = Column(Float)
    est_1h = Column(String); est_1d = Column(String); est_7d = Column(String); est_1m = Column(String)
    stop_loss = Column(String(20)); rr_ratio = Column(String(20)); vol_category = Column(String(10))
    signal_age = Column(String(20)); sparkline = Column(JSON); reasoning = Column(Text); drivers = Column(JSON); logic_badges = Column(JSON); confidence_drivers = Column(JSON); trad_confidence = Column(Float); swarm_confidence = Column(Float)
    win_rate = Column(Float); strategy_tags = Column(JSON)
    candlestick_pattern = Column(String(100))

class ConsumptionCommodity(Base):
    __tablename__ = "commodities"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String); ticker = Column(String(20)); action = Column(String(10))
    close_price = Column(Float); daily_change = Column(Float)
    est_1d = Column(String); est_7d = Column(String); est_1m = Column(String)
    stop_loss = Column(String(20)); rr_ratio = Column(String(20)); vol_category = Column(String(10))
    sparkline = Column(JSON); reasoning = Column(Text); logic_badges = Column(JSON); confidence_drivers = Column(JSON); trad_confidence = Column(Float); swarm_confidence = Column(Float)
    win_rate = Column(Float); strategy_tags = Column(JSON)
    candlestick_pattern = Column(String(100))

class ConsumptionCrypto(Base):
    __tablename__ = "crypto"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset = Column(String); ticker = Column(String(20)); action = Column(String(10))
    close_price = Column(Float); daily_change = Column(Float)
    est_1d = Column(String(20)); est_7d = Column(String(20)); est_1m = Column(String(20))
    sparkline = Column(JSON); reasoning = Column(Text)
    trad_confidence = Column(Float); swarm_confidence = Column(Float)
    # Crypto Native Institutional Metrics
    mvrv_z_score = Column(Float)
    nvt_ratio = Column(Float)
    fear_greed_index = Column(Integer)
    funding_rate = Column(Float)
    gas_price_gwei = Column(Float)
    hash_rate_th_s = Column(Float)
    win_rate = Column(Float); strategy_tags = Column(JSON)
    candlestick_pattern = Column(String(100))

class ConsumptionContrarian(Base):
    __tablename__ = "contrarian"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20)); signal_text = Column(Text)
    est_1d = Column(String); est_7d = Column(String); est_1m = Column(String)

class SwarmLog(Base):
    __tablename__ = "swarm_logs"
    __table_args__ = {"schema": "consumption"}
    timestamp = Column(DateTime, default=get_hkt_now, primary_key=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), index=True); consensus = Column(JSON)

class QuantStrategy(Base):
    __tablename__ = "quant_strategies"
    __table_args__ = {"schema": "gold"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    target_ticker = Column(String(20))
    is_active = Column(Boolean, default=True)
    params = Column(JSON) # e.g. {"rsi_low": 30, "rsi_high": 70, "lot_size": 100}
    win_rate_target = Column(Float)
    stop_loss_pct = Column(Float)
    take_profit_pct = Column(Float)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    current_pnl = Column(Float, default=0.0)
    equity_curve = Column(JSON) # Array of history points

# NEW: Strategy Registry - canonical source of truth from DE
class StrategyRegistry(Base):
    __tablename__ = "strategy_registry"
    __table_args__ = {"schema": "gold"}
    strategy_id = Column(String(100), primary_key=True)
    name = Column(String(200))
    asset_class = Column(String(50))
    universe_tickers = Column(ARRAY(String))
    frequency = Column(String(50))
    execution_mode = Column(String(50))
    status = Column(String(50))
    sharpe_oos = Column(DECIMAL(10,4))
    max_drawdown_oos = Column(DECIMAL(10,4))
    trade_count_oos = Column(Integer)
    win_rate_oos = Column(DECIMAL(10,4))
    conviction_score = Column(DECIMAL(10,2))
    assigned_capital = Column(DECIMAL(15,2))
    in_market_capital = Column(DECIMAL(15,2))
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    deployed_at = Column(DateTime)
    last_signal_at = Column(DateTime)
    retired_at = Column(DateTime)
    retirement_reason = Column(Text)
    signal_logic = Column(Text)
    exit_logic = Column(Text)
    signal_file_path = Column(String(500))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class AgentActivity(Base):
    __tablename__ = "agent_activity"
    __table_args__ = {"schema": "gold"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), index=True)  # e.g. qr_research, qr_etl, qr_qa, scrum_master
    strategy_id = Column(String(10), nullable=True)  # FK to strategy_registry
    action = Column(String(50))  # e.g. REVIEW, APPROVE, COMMENT, SIGNAL, VALIDATE
    message = Column(Text)
    meta_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=get_hkt_now)

class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = {"schema": "consumption"}
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=get_hkt_now)
    ticker = Column(String(20))
    side = Column(String(10)) # BUY, SELL
    price = Column(Float)
    quantity = Column(Float)
    total_value = Column(Float)
    pnl = Column(Float)
    strategy = Column(String(50))
