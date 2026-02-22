"""
FX Streaming Service - Phase 1.1
Real-time FX tick streaming from IBKR with 5-second bar aggregation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import time

from ib_insync import IB, Forex, Ticker
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_hkt_now

logger = logging.getLogger(__name__)

@dataclass
class FXTick:
    """Single FX tick data"""
    timestamp: datetime
    ticker: str
    bid: float
    ask: float
    source: str = 'IBKR'
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0
    
    @property
    def spread_bps(self) -> float:
        mid = self.mid
        if mid == 0:
            return 0
        return (self.ask - self.bid) / mid * 10000.0


@dataclass
class FXBar5S:
    """5-second aggregated bar"""
    bucket: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float
    spread_avg_bps: float
    spread_min_bps: float
    spread_max_bps: float
    tick_count: int
    source: str = 'IBKR'


class FXBarAggregator:
    """Aggregate ticks into 5-second bars"""
    
    def __init__(self):
        self.ticks_buffer: Dict[str, list] = defaultdict(list)
        self.last_bar_time: Dict[str, datetime] = {}
        self.bar_interval = 5  # seconds
        
    def add_tick(self, tick: FXTick) -> Optional[FXBar5S]:
        """Add tick and return bar if bucket is complete"""
        ticker = tick.ticker
        
        # Determine which bucket this tick belongs to
        bucket = tick.timestamp.replace(
            microsecond=0,
            second=(tick.timestamp.second // self.bar_interval) * self.bar_interval
        )
        
        # Check if we need to close the previous bucket
        if ticker in self.last_bar_time and self.last_bar_time[ticker] != bucket:
            # Close previous bar
            prev_bar = self._create_bar(ticker, self.last_bar_time[ticker])
            self.ticks_buffer[ticker] = [tick]  # Start new bucket
            self.last_bar_time[ticker] = bucket
            return prev_bar
        
        # Add to current bucket
        self.ticks_buffer[ticker].append(tick)
        self.last_bar_time[ticker] = bucket
        return None
    
    def _create_bar(self, ticker: str, bucket: datetime) -> Optional[FXBar5S]:
        """Create 5-second bar from buffer"""
        ticks = self.ticks_buffer.get(ticker, [])
        if not ticks:
            return None
        
        mids = [t.mid for t in ticks]
        bids = [t.bid for t in ticks]
        asks = [t.ask for t in ticks]
        spreads = [t.spread_bps for t in ticks]
        
        return FXBar5S(
            bucket=bucket,
            ticker=ticker,
            open=mids[0],
            high=max(mids),
            low=min(mids),
            close=mids[-1],
            bid_open=bids[0],
            bid_high=max(bids),
            bid_low=min(bids),
            bid_close=bids[-1],
            ask_open=asks[0],
            ask_high=max(asks),
            ask_low=min(asks),
            ask_close=asks[-1],
            spread_avg_bps=sum(spreads) / len(spreads),
            spread_min_bps=min(spreads),
            spread_max_bps=max(spreads),
            tick_count=len(ticks)
        )
    
    def force_close_all(self) -> list:
        """Force close all pending bars (for shutdown)"""
        bars = []
        for ticker in list(self.ticks_buffer.keys()):
            if ticker in self.last_bar_time:
                bar = self._create_bar(ticker, self.last_bar_time[ticker])
                if bar:
                    bars.append(bar)
        self.ticks_buffer.clear()
        self.last_bar_time.clear()
        return bars


class FXStreamingService:
    """
    FX Streaming Service - Real-time tick data from IBKR
    
    Features:
    - Connects to IB Gateway/TWS
    - Subscribes to major FX pairs
    - Stores ticks to database
    - Aggregates 5-second bars
    - Handles disconnections gracefully
    
    IB Gateway Ports:
    - 4001 = LIVE trading (real money)
    - 4002 = PAPER trading (simulated)
    """
    
    # Major pairs for Phase 1.1
    FX_PAIRS = ['EURUSD', 'USDJPY', 'GBPUSD']
    
    # Spread alert thresholds (in basis points)
    SPREAD_THRESHOLDS = {
        'EURUSD': 3.0,  # 0.3 pips
        'USDJPY': 3.0,
        'GBPUSD': 5.0,  # 0.5 pips
    }
    
    # Default: 52.74.14.181:4002 (paper trading)
    # To switch to live: change port to 4001
    def __init__(self, host='52.74.14.181', port=4002, client_id=2):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.is_connected = False
        self.aggregator = FXBarAggregator()
        self.tickers: Dict[str, Ticker] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self._callbacks: list[Callable[[FXBar5S], None]] = []
        self._shutdown = False
        self._aggregator_task = None
        
    def register_bar_callback(self, callback: Callable[[FXBar5S], None]):
        """Register callback for new 5s bars"""
        self._callbacks.append(callback)
        
    async def connect(self) -> bool:
        """Connect to IB Gateway"""
        try:
            logger.info(f"Connecting to IB Gateway at {self.host}:{self.port}...")
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id, timeout=10)
            self.is_connected = True
            logger.info("✅ FX Streaming: Connected to IB Gateway")
            self._log_status('IBKR', 'CONNECTED')
            return True
        except Exception as e:
            logger.error(f"❌ FX Streaming: Connection failed - {e}")
            self._log_status('IBKR', 'DISCONNECTED', message=str(e))
            return False
    
    async def subscribe_pairs(self):
        """Subscribe to FX pairs"""
        for pair in self.FX_PAIRS:
            try:
                contract = Forex(pair)
                self.ib.qualifyContracts(contract)
                
                # Request market data
                ticker = self.ib.reqMktData(contract, '', False, False)
                ticker.updateEvent += self._on_tick(pair)
                self.tickers[pair] = ticker
                
                logger.info(f"✅ Subscribed to {pair}")
                self._log_status('SUBSCRIPTION', 'ACTIVE', ticker=pair)
            except Exception as e:
                logger.error(f"❌ Failed to subscribe to {pair}: {e}")
                self._log_status('SUBSCRIPTION', 'FAILED', ticker=pair, message=str(e))
    
    def _on_tick(self, pair: str):
        """Create tick handler for a pair"""
        def handler(ticker: Ticker):
            if self._shutdown:
                return
            
            # Check if we have valid bid/ask
            if ticker.bid is None or ticker.ask is None:
                return
            
            # Create tick
            tick = FXTick(
                timestamp=get_hkt_now(),
                ticker=pair,
                bid=ticker.bid,
                ask=ticker.ask
            )
            
            # Store tick to database (async fire-and-forget)
            asyncio.create_task(self._store_tick(tick))
            
            # Add to aggregator
            bar = self.aggregator.add_tick(tick)
            if bar:
                # New bar completed
                asyncio.create_task(self._process_bar(bar))
            
            # Check spread alert
            self._check_spread_alert(tick)
        
        return handler
    
    async def _store_tick(self, tick: FXTick):
        """Store tick to database"""
        try:
            db = SessionLocal()
            db.execute(text("""
                INSERT INTO gold.fx_ticks (timestamp, ticker, bid, ask, source)
                VALUES (:ts, :ticker, :bid, :ask, :source)
            """), {
                'ts': tick.timestamp,
                'ticker': tick.ticker,
                'bid': tick.bid,
                'ask': tick.ask,
                'source': tick.source
            })
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to store tick: {e}")
    
    async def _process_bar(self, bar: FXBar5S):
        """Process completed 5s bar"""
        try:
            # Store bar to database
            db = SessionLocal()
            db.execute(text("""
                INSERT INTO gold.fx_bars_5s (
                    bucket, ticker, open, high, low, close,
                    bid_open, bid_high, bid_low, bid_close,
                    ask_open, ask_high, ask_low, ask_close,
                    spread_avg_bps, spread_min_bps, spread_max_bps,
                    tick_count, source
                ) VALUES (
                    :bucket, :ticker, :open, :high, :low, :close,
                    :bid_open, :bid_high, :bid_low, :bid_close,
                    :ask_open, :ask_high, :ask_low, :ask_close,
                    :spread_avg, :spread_min, :spread_max,
                    :tick_count, :source
                )
                ON CONFLICT (bucket, ticker) DO UPDATE SET
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    bid_close = EXCLUDED.bid_close,
                    ask_close = EXCLUDED.ask_close,
                    spread_avg_bps = EXCLUDED.spread_avg_bps,
                    tick_count = EXCLUDED.tick_count
            """), {
                'bucket': bar.bucket,
                'ticker': bar.ticker,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'bid_open': bar.bid_open,
                'bid_high': bar.bid_high,
                'bid_low': bar.bid_low,
                'bid_close': bar.bid_close,
                'ask_open': bar.ask_open,
                'ask_high': bar.ask_high,
                'ask_low': bar.ask_low,
                'ask_close': bar.ask_close,
                'spread_avg': bar.spread_avg_bps,
                'spread_min': bar.spread_min_bps,
                'spread_max': bar.spread_max_bps,
                'tick_count': bar.tick_count,
                'source': bar.source
            })
            db.commit()
            db.close()
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(bar)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.debug(f"5s bar: {bar.ticker} @ {bar.bucket} - Close: {bar.close:.5f}, Ticks: {bar.tick_count}")
            
        except Exception as e:
            logger.error(f"Failed to process bar: {e}")
    
    def _check_spread_alert(self, tick: FXTick):
        """Check if spread is abnormally wide"""
        threshold = self.SPREAD_THRESHOLDS.get(tick.ticker, 5.0)
        
        if tick.spread_bps > threshold:
            # Rate limit alerts (1 per minute per pair)
            now = get_hkt_now()
            last_alert = self.last_alert_time.get(tick.ticker)
            if last_alert and (now - last_alert).seconds < 60:
                return
            
            self.last_alert_time[tick.ticker] = now
            
            # Log alert
            try:
                db = SessionLocal()
                db.execute(text("""
                    INSERT INTO gold.fx_alerts (ticker, alert_type, spread_bps, threshold_bps, message)
                    VALUES (:ticker, 'WIDE_SPREAD', :spread, :threshold, :msg)
                """), {
                    'ticker': tick.ticker,
                    'spread': tick.spread_bps,
                    'threshold': threshold,
                    'msg': f"Spread {tick.spread_bps:.2f} bps exceeds threshold {threshold:.2f} bps"
                })
                db.commit()
                db.close()
                logger.warning(f"🚨 Spread Alert: {tick.ticker} - {tick.spread_bps:.2f} bps")
            except Exception as e:
                logger.error(f"Failed to log alert: {e}")
    
    def _log_status(self, service: str, status: str, ticker: str = None, message: str = None):
        """Log service status to database"""
        try:
            db = SessionLocal()
            db.execute(text("""
                INSERT INTO gold.fx_streaming_status (service, status, ticker, message)
                VALUES (:service, :status, :ticker, :msg)
            """), {
                'service': service,
                'status': status,
                'ticker': ticker,
                'msg': message
            })
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log status: {e}")
    
    async def run(self):
        """Main service loop"""
        if not await self.connect():
            logger.error("FX Streaming: Failed to connect, retrying in 30s...")
            await asyncio.sleep(30)
            return await self.run()
        
        await self.subscribe_pairs()
        
        # Keep running until shutdown
        while not self._shutdown:
            if not self.ib.isConnected():
                logger.warning("FX Streaming: IBKR disconnected, reconnecting...")
                self._log_status('IBKR', 'RECONNECTING')
                if await self.connect():
                    await self.subscribe_pairs()
            await asyncio.sleep(5)
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("FX Streaming: Shutting down...")
        self._shutdown = True
        
        # Close pending bars
        bars = self.aggregator.force_close_all()
        for bar in bars:
            await self._process_bar(bar)
        
        # Disconnect
        if self.ib.isConnected():
            self.ib.disconnect()
        
        self._log_status('IBKR', 'DISCONNECTED', message='Service shutdown')
        logger.info("FX Streaming: Shutdown complete")


# Global instance
fx_streaming_service = FXStreamingService()
