"""
Strategy Configuration and Screening System
Allows users to define custom strategies and screen stocks against them
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

class EntryCondition(Enum):
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    SMA_CROSS_UP = "sma_cross_up"
    SMA_CROSS_DOWN = "sma_cross_down"
    PRICE_ABOVE_SMA = "price_above_sma"
    PRICE_BELOW_SMA = "price_below_sma"
    MACD_BULLISH = "macd_bullish"
    MACD_BEARISH = "macd_bearish"
    BB_LOWER_TOUCH = "bb_lower_touch"
    BB_UPPER_TOUCH = "bb_upper_touch"
    BREAKOUT_HIGH = "breakout_high"
    BREAKDOWN_LOW = "breakdown_low"
    VOLUME_SPIKE = "volume_spike"
    CANDLESTICK_PATTERN = "candlestick_pattern"

class ExitCondition(Enum):
    RSI_REVERSION = "rsi_reversion"
    SMA_CROSS_OPPOSITE = "sma_cross_opposite"
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    TIME_EXIT = "time_exit"
    TRAILING_STOP = "trailing_stop"

@dataclass
class StrategyConfig:
    """User-defined strategy configuration"""
    id: str
    name: str
    description: str
    
    # Entry rules (ALL must be true for entry)
    entry_conditions: List[Dict[str, Any]] = field(default_factory=list)
    # Example: [{"type": "rsi_oversold", "period": 14, "threshold": 30}]
    
    # Exit rules (ANY can trigger exit)
    exit_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Risk management
    stop_loss_type: str = "atr"  # atr, fixed_percent, support
    stop_loss_value: float = 2.0  # 2x ATR or 2%
    
    position_size_type: str = "fixed"  # fixed, kelly, volatility
    position_size_value: float = 0.1  # 10% of portfolio
    
    # Time constraints
    max_holding_days: int = 10
    
    # Filters
    min_win_rate: float = 0.5
    min_sharpe: float = 0.5
    min_trades: int = 10
    
    # Scoring weights
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "win_rate": 0.4,
        "sharpe": 0.3,
        "profit_factor": 0.2,
        "recency": 0.1
    })

# Built-in Strategy Templates
BUILTIN_STRATEGIES = {
    "mean_reversion": StrategyConfig(
        id="mean_reversion",
        name="Mean Reversion",
        description="Buy oversold stocks (RSI < 30), sell when RSI > 70 or price hits upper Bollinger Band",
        entry_conditions=[
            {"type": "rsi_oversold", "period": 14, "threshold": 30},
            {"type": "price_below_sma", "period": 20},
            {"type": "volume_spike", "threshold": 1.0}
        ],
        exit_conditions=[
            {"type": "rsi_reversion", "threshold": 70},
            {"type": "bb_upper_touch"},
            {"type": "time_exit", "days": 10}
        ],
        stop_loss_type="atr",
        stop_loss_value=2.0,
        max_holding_days=10,
        min_win_rate=0.55,
        min_sharpe=0.8
    ),
    
    "trend_following": StrategyConfig(
        id="trend_following",
        name="Trend Following",
        description="Follow the trend - buy when SMA 20 crosses above SMA 50 with MACD confirmation",
        entry_conditions=[
            {"type": "sma_cross_up", "fast": 20, "slow": 50},
            {"type": "macd_bullish"},
            {"type": "volume_spike", "threshold": 1.2}
        ],
        exit_conditions=[
            {"type": "sma_cross_opposite"},
            {"type": "time_exit", "days": 20}
        ],
        stop_loss_type="atr",
        stop_loss_value=3.0,
        max_holding_days=20,
        min_win_rate=0.50,
        min_sharpe=1.0
    ),
    
    "breakout_momentum": StrategyConfig(
        id="breakout_momentum",
        name="Breakout Momentum",
        description="Buy on breakouts above resistance with volume confirmation",
        entry_conditions=[
            {"type": "breakout_high", "lookback": 20},
            {"type": "volume_spike", "threshold": 1.5}
        ],
        exit_conditions=[
            {"type": "profit_target", "percent": 5.0},
            {"type": "time_exit", "days": 5}
        ],
        stop_loss_type="fixed_percent",
        stop_loss_value=2.0,
        max_holding_days=5,
        min_win_rate=0.50,
        min_sharpe=0.6
    ),
    
    "rsi_divergence": StrategyConfig(
        id="rsi_divergence",
        name="RSI Divergence",
        description="Buy on bullish RSI divergence (price lower low, RSI higher low)",
        entry_conditions=[
            {"type": "rsi_divergence_bullish", "lookback": 14},
            {"type": "rsi_oversold", "period": 14, "threshold": 40}
        ],
        exit_conditions=[
            {"type": "rsi_reversion", "threshold": 60},
            {"type": "time_exit", "days": 15}
        ],
        stop_loss_type="atr",
        stop_loss_value=2.5,
        max_holding_days=15,
        min_win_rate=0.55,
        min_sharpe=0.7
    ),
    
    "golden_cross": StrategyConfig(
        id="golden_cross",
        name="Golden Cross",
        description="Long-term trend following - buy on SMA 50 crossing above SMA 200",
        entry_conditions=[
            {"type": "sma_cross_up", "fast": 50, "slow": 200}
        ],
        exit_conditions=[
            {"type": "sma_cross_opposite"},
            {"type": "time_exit", "days": 60}
        ],
        stop_loss_type="atr",
        stop_loss_value=4.0,
        max_holding_days=60,
        min_win_rate=0.55,
        min_sharpe=1.2
    ),
    
    "earnings_momentum": StrategyConfig(
        id="earnings_momentum",
        name="Post-Earnings Momentum",
        description="Capture momentum after earnings announcements",
        entry_conditions=[
            {"type": "price_above_sma", "period": 20},
            {"type": "volume_spike", "threshold": 2.0},
            {"type": "macd_bullish"}
        ],
        exit_conditions=[
            {"type": "profit_target", "percent": 8.0},
            {"type": "time_exit", "days": 10}
        ],
        stop_loss_type="fixed_percent",
        stop_loss_value=3.0,
        max_holding_days=10,
        min_win_rate=0.52,
        min_sharpe=0.8
    )
}

def get_strategy_template(strategy_id: str) -> Optional[StrategyConfig]:
    """Get a strategy template by ID"""
    return BUILTIN_STRATEGIES.get(strategy_id)

def get_all_strategy_templates() -> List[StrategyConfig]:
    """Get all available strategy templates"""
    return list(BUILTIN_STRATEGIES.values())

def save_custom_strategy(strategy: StrategyConfig) -> bool:
    """Save a custom strategy to database"""
    from app.db.session import engine
    from sqlalchemy import text
    
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO gold.strategy_templates 
                (id, name, description, config_json, created_at, is_builtin)
                VALUES (:id, :name, :description, :config, NOW(), FALSE)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    config_json = EXCLUDED.config_json,
                    updated_at = NOW()
            """), {
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "config": json.dumps({
                    "entry_conditions": strategy.entry_conditions,
                    "exit_conditions": strategy.exit_conditions,
                    "stop_loss_type": strategy.stop_loss_type,
                    "stop_loss_value": strategy.stop_loss_value,
                    "position_size_type": strategy.position_size_type,
                    "position_size_value": strategy.position_size_value,
                    "max_holding_days": strategy.max_holding_days,
                    "min_win_rate": strategy.min_win_rate,
                    "min_sharpe": strategy.min_sharpe,
                    "min_trades": strategy.min_trades,
                    "score_weights": strategy.score_weights
                })
            })
            conn.commit()
        return True
    except Exception as e:
        print(f"Error saving strategy: {e}")
        return False

def load_custom_strategies() -> List[StrategyConfig]:
    """Load custom strategies from database"""
    from app.db.session import engine
    from sqlalchemy import text
    
    strategies = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, description, config_json 
                FROM gold.strategy_templates 
                WHERE is_builtin = FALSE
            """))
            for row in result:
                config = json.loads(row.config_json)
                strategies.append(StrategyConfig(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    **config
                ))
    except Exception as e:
        print(f"Error loading strategies: {e}")
    
    return strategies

# Database schema for strategy templates
STRATEGY_TEMPLATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS gold.strategy_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    config_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_builtin BOOLEAN DEFAULT FALSE
);

-- Insert built-in strategies
INSERT INTO gold.strategy_templates (id, name, description, config_json, is_builtin) VALUES
('mean_reversion', 'Mean Reversion', 'Buy oversold, sell on reversion', 
 '{"entry_conditions": [{"type": "rsi_oversold", "period": 14, "threshold": 30}], "exit_conditions": [{"type": "rsi_reversion", "threshold": 70}]}', TRUE),
('trend_following', 'Trend Following', 'Follow SMA crossovers',
 '{"entry_conditions": [{"type": "sma_cross_up", "fast": 20, "slow": 50}], "exit_conditions": [{"type": "sma_cross_opposite"}]}', TRUE)
ON CONFLICT (id) DO NOTHING;
"""
