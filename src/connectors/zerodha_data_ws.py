import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pandas as pd
from kiteconnect import KiteConnect, KiteTicker
from pydantic import BaseModel
import redis.asyncio as redis

class ZerodhaTickData(BaseModel):
    instrument_token: int
    exchange_timestamp: datetime
    process_timestamp: datetime
    last_price: float
    volume: int
    bid_price: float
    bid_quantity: int
    ask_price: float
    ask_quantity: int
    oi: Optional[int] = None
    oi_day_high: Optional[int] = None
    oi_day_low: Optional[int] = None

class ZerodhaDataWebSocket:
    def __init__(self, api_key: str, access_token: str, redis_client: redis.Redis):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.ticker = KiteTicker(api_key, access_token)
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Subscription management
        self.subscribed_tokens = set()
        self.subscription_limit = 3000  # Kite WebSocket limit
        
        # Callbacks
        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_reconnect = self._on_reconnect
        
    async def subscribe_instruments(self, tokens: List[int]):
        """Subscribe to instrument tokens with limit enforcement"""
        if len(self.subscribed_tokens) + len(tokens) > self.subscription_limit:
            raise ValueError(f"Subscription limit exceeded: {self.subscription_limit}")
            
        self.ticker.subscribe(tokens)
        self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
        self.subscribed_tokens.update(tokens)
        
    def _on_ticks(self, ws, ticks):
        """Process incoming tick data and publish to Redis Streams"""
        for tick in ticks:
            try:
                tick_data = ZerodhaTickData(
                    instrument_token=tick['instrument_token'],
                    exchange_timestamp=tick['exchange_timestamp'],
                    process_timestamp=datetime.utcnow(),
                    last_price=tick['last_price'],
                    volume=tick['volume'],
                    bid_price=tick['depth']['buy'][0]['price'] if tick['depth']['buy'] else 0,
                    bid_quantity=tick['depth']['buy'][0]['quantity'] if tick['depth']['buy'] else 0,
                    ask_price=tick['depth']['sell'][0]['price'] if tick['depth']['sell'] else 0,
                    ask_quantity=tick['depth']['sell'][0]['quantity'] if tick['depth']['sell'] else 0,
                    oi=tick.get('oi'),
                    oi_day_high=tick.get('oi_day_high'),
                    oi_day_low=tick.get('oi_day_low')
                )
                
                # Publish to Redis Stream
                asyncio.create_task(self._publish_tick(tick_data))
                
            except Exception as e:
                self.logger.error(f"Error processing tick: {e}")
                
    async def _publish_tick(self, tick_data: ZerodhaTickData):
        """Publish normalized tick data to Redis Stream"""
        stream_key = f"market_data:{tick_data.instrument_token}"
        await self.redis.xadd(
            stream_key,
            tick_data.dict(),
            maxlen=10000  # Retain last 10k ticks per instrument
        )
        
    def _on_connect(self, ws, response):
        self.logger.info("WebSocket connected")
        
    def _on_close(self, ws, code, reason):
        self.logger.warning(f"WebSocket closed: {code} - {reason}")
        
    def _on_error(self, ws, code, reason):
        self.logger.error(f"WebSocket error: {code} - {reason}")
        
    def _on_reconnect(self, ws, attempts_count):
        self.logger.info(f"WebSocket reconnecting: attempt {attempts_count}")
        
    def start(self):
        """Start WebSocket connection"""
        self.ticker.connect(threaded=True)
        
    def stop(self):
        """Stop WebSocket connection"""
        self.ticker.close()
