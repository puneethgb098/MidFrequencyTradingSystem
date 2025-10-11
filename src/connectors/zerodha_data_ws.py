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
    bid_prices: List[float] = []
    bid_quantities: List[int] = []
    ask_prices: List[float] = []
    ask_quantities: List[int] = []
    oi: Optional[int] = None
    oi_day_high: Optional[int] = None
    oi_day_low: Optional[int] = None
    depth_level: int = 1

class ZerodhaDataWebSocket:
    def __init__(self, api_key: str, access_token: str, redis_client: redis.Redis, depth_config: Optional[Dict[int, int]] = None):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.ticker = KiteTicker(api_key, access_token)
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # Subscription management
        self.subscribed_tokens = set()
        self.subscription_limit = 3000  # Kite WebSocket limit

        # Depth configuration: {instrument_token: depth_level}
        # depth_level: 1 for Level 1, 5 for Level 5 (full depth)
        self.depth_config = depth_config or {}
        
        # Callbacks
        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_reconnect = self._on_reconnect
        
    async def subscribe_instruments(self, tokens: List[int], depth_level: int = 1):
        """Subscribe to instrument tokens with limit enforcement and depth configuration

        Args:
            tokens: List of instrument tokens to subscribe
            depth_level: 1 for Level 1 (best bid/ask), 5 for Level 5 (full depth)
        """
        if len(self.subscribed_tokens) + len(tokens) > self.subscription_limit:
            raise ValueError(f"Subscription limit exceeded: {self.subscription_limit}")

        # Update depth configuration for these tokens
        for token in tokens:
            self.depth_config[token] = depth_level

        self.ticker.subscribe(tokens)
        self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
        self.subscribed_tokens.update(tokens)

        self.logger.info(f"Subscribed to {len(tokens)} instruments with depth level {depth_level}")

    def set_depth_level(self, instrument_token: int, depth_level: int):
        """Update depth level for a specific instrument

        Args:
            instrument_token: Instrument token
            depth_level: 1 for Level 1, 5 for Level 5
        """
        if depth_level not in [1, 5]:
            raise ValueError("depth_level must be 1 or 5")
        self.depth_config[instrument_token] = depth_level
        self.logger.info(f"Set depth level {depth_level} for instrument {instrument_token}")
        
    def _on_ticks(self, ws, ticks):
        """Process incoming tick data and publish to Redis Streams"""
        for tick in ticks:
            try:
                instrument_token = tick['instrument_token']
                depth_level = self.depth_config.get(instrument_token, 1)

                # Extract depth data based on configuration
                buy_depth = tick.get('depth', {}).get('buy', [])
                sell_depth = tick.get('depth', {}).get('sell', [])

                # Extract all 5 levels if available and configured
                bid_prices = []
                bid_quantities = []
                ask_prices = []
                ask_quantities = []

                if depth_level == 5 and buy_depth and sell_depth:
                    # Extract up to 5 levels of depth
                    for i in range(min(5, len(buy_depth))):
                        bid_prices.append(buy_depth[i].get('price', 0.0))
                        bid_quantities.append(buy_depth[i].get('quantity', 0))

                    for i in range(min(5, len(sell_depth))):
                        ask_prices.append(sell_depth[i].get('price', 0.0))
                        ask_quantities.append(sell_depth[i].get('quantity', 0))

                # Best bid/ask (Level 1)
                best_bid_price = buy_depth[0]['price'] if buy_depth else 0
                best_bid_qty = buy_depth[0]['quantity'] if buy_depth else 0
                best_ask_price = sell_depth[0]['price'] if sell_depth else 0
                best_ask_qty = sell_depth[0]['quantity'] if sell_depth else 0

                tick_data = ZerodhaTickData(
                    instrument_token=instrument_token,
                    exchange_timestamp=tick['exchange_timestamp'],
                    process_timestamp=datetime.utcnow(),
                    last_price=tick['last_price'],
                    volume=tick['volume'],
                    bid_price=best_bid_price,
                    bid_quantity=best_bid_qty,
                    ask_price=best_ask_price,
                    ask_quantity=best_ask_qty,
                    bid_prices=bid_prices,
                    bid_quantities=bid_quantities,
                    ask_prices=ask_prices,
                    ask_quantities=ask_quantities,
                    oi=tick.get('oi'),
                    oi_day_high=tick.get('oi_day_high'),
                    oi_day_low=tick.get('oi_day_low'),
                    depth_level=depth_level
                )

                # Publish to Redis Stream
                asyncio.create_task(self._publish_tick(tick_data))

            except Exception as e:
                self.logger.error(f"Error processing tick for {tick.get('instrument_token', 'unknown')}: {e}")
                
    async def _publish_tick(self, tick_data: ZerodhaTickData):
        """Publish normalized tick data to Redis Stream"""
        stream_key = f"market_data:{tick_data.instrument_token}"

        # Convert tick data to dict and serialize lists properly
        tick_dict = tick_data.dict()

        # Redis streams require string values, convert lists to JSON
        for key in ['bid_prices', 'bid_quantities', 'ask_prices', 'ask_quantities']:
            if key in tick_dict and tick_dict[key]:
                tick_dict[key] = json.dumps(tick_dict[key])
            else:
                tick_dict[key] = json.dumps([])

        # Convert datetime objects to ISO format strings
        for key in ['exchange_timestamp', 'process_timestamp']:
            if key in tick_dict and isinstance(tick_dict[key], datetime):
                tick_dict[key] = tick_dict[key].isoformat()

        # Adjust maxlen based on depth level for performance
        maxlen = 5000 if tick_data.depth_level == 5 else 10000

        await self.redis.xadd(
            stream_key,
            tick_dict,
            maxlen=maxlen
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
