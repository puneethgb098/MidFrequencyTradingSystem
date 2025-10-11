import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import redis.asyncio as redis


class OrderBookService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

    async def get_latest_tick(self, instrument_token: int) -> Optional[Dict[str, Any]]:
        """Get the latest tick data for an instrument"""
        try:
            stream_key = f"market_data:{instrument_token}"
            messages = await self.redis.xrevrange(stream_key, count=1)

            if not messages:
                return None

            msg_id, fields = messages[0]

            # Parse the tick data
            tick_data = self._parse_tick_data(fields)
            tick_data['msg_id'] = msg_id.decode() if isinstance(msg_id, bytes) else msg_id

            return tick_data

        except Exception as e:
            self.logger.error(f"Error fetching latest tick for {instrument_token}: {e}")
            return None

    async def get_historical_ticks(
        self,
        instrument_token: int,
        count: int = 100,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get historical tick data for an instrument"""
        try:
            stream_key = f"market_data:{instrument_token}"

            if start_time and end_time:
                messages = await self.redis.xrange(stream_key, start_time, end_time, count=count)
            elif end_time:
                messages = await self.redis.xrevrange(stream_key, end_time, '-', count=count)
            else:
                messages = await self.redis.xrevrange(stream_key, count=count)

            ticks = []
            for msg_id, fields in messages:
                tick_data = self._parse_tick_data(fields)
                tick_data['msg_id'] = msg_id.decode() if isinstance(msg_id, bytes) else msg_id
                ticks.append(tick_data)

            return ticks

        except Exception as e:
            self.logger.error(f"Error fetching historical ticks for {instrument_token}: {e}")
            return []

    async def get_order_book(self, instrument_token: int) -> Optional[Dict[str, Any]]:
        """Get current Level 5 order book for an instrument"""
        tick = await self.get_latest_tick(instrument_token)

        if not tick:
            return None

        try:
            # Parse Level 5 depth data
            bid_prices = json.loads(tick.get('bid_prices', '[]'))
            bid_quantities = json.loads(tick.get('bid_quantities', '[]'))
            ask_prices = json.loads(tick.get('ask_prices', '[]'))
            ask_quantities = json.loads(tick.get('ask_quantities', '[]'))

            # Calculate cumulative volumes
            bid_cumulative = self._calculate_cumulative_volumes(bid_quantities)
            ask_cumulative = self._calculate_cumulative_volumes(ask_quantities)

            # Build bid and ask levels
            bids = []
            for i in range(len(bid_prices)):
                bids.append({
                    'level': i + 1,
                    'price': bid_prices[i],
                    'quantity': bid_quantities[i],
                    'cumulative': bid_cumulative[i]
                })

            asks = []
            for i in range(len(ask_prices)):
                asks.append({
                    'level': i + 1,
                    'price': ask_prices[i],
                    'quantity': ask_quantities[i],
                    'cumulative': ask_cumulative[i]
                })

            # Calculate spread and imbalance metrics
            spread = ask_prices[0] - bid_prices[0] if bid_prices and ask_prices else 0
            spread_pct = (spread / bid_prices[0] * 100) if bid_prices and bid_prices[0] > 0 else 0

            total_bid_qty = sum(bid_quantities)
            total_ask_qty = sum(ask_quantities)
            imbalance = (total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty) if (total_bid_qty + total_ask_qty) > 0 else 0

            return {
                'instrument_token': instrument_token,
                'timestamp': tick.get('process_timestamp'),
                'last_price': float(tick.get('last_price', 0)),
                'volume': int(tick.get('volume', 0)),
                'bids': bids,
                'asks': asks,
                'spread': spread,
                'spread_pct': spread_pct,
                'imbalance': imbalance,
                'depth_level': int(tick.get('depth_level', 1))
            }

        except Exception as e:
            self.logger.error(f"Error building order book for {instrument_token}: {e}")
            return None

    async def get_price_history(self, instrument_token: int, count: int = 100) -> Dict[str, Any]:
        """Get price history for charting (best bid/ask over time)"""
        ticks = await self.get_historical_ticks(instrument_token, count=count)

        timestamps = []
        bid_prices = []
        ask_prices = []
        last_prices = []
        volumes = []

        for tick in reversed(ticks):
            try:
                timestamps.append(tick.get('process_timestamp'))
                bid_prices.append(float(tick.get('bid_price', 0)))
                ask_prices.append(float(tick.get('ask_price', 0)))
                last_prices.append(float(tick.get('last_price', 0)))
                volumes.append(int(tick.get('volume', 0)))
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid tick data: {e}")
                continue

        return {
            'instrument_token': instrument_token,
            'timestamps': timestamps,
            'bid_prices': bid_prices,
            'ask_prices': ask_prices,
            'last_prices': last_prices,
            'volumes': volumes
        }

    async def get_multiple_instruments(self, instrument_tokens: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get latest data for multiple instruments"""
        result = {}
        for token in instrument_tokens:
            tick = await self.get_latest_tick(token)
            if tick:
                result[token] = tick

        return result

    def _parse_tick_data(self, fields: Dict) -> Dict[str, Any]:
        """Parse tick data from Redis stream fields"""
        parsed = {}
        for key, value in fields.items():
            key_str = key.decode() if isinstance(key, bytes) else key
            value_str = value.decode() if isinstance(value, bytes) else value

            # Try to convert to appropriate type
            try:
                if key_str in ['bid_prices', 'bid_quantities', 'ask_prices', 'ask_quantities']:
                    parsed[key_str] = value_str
                elif key_str in ['instrument_token', 'volume', 'bid_quantity', 'ask_quantity', 'oi', 'oi_day_high', 'oi_day_low', 'depth_level']:
                    parsed[key_str] = int(value_str) if value_str else 0
                elif key_str in ['last_price', 'bid_price', 'ask_price']:
                    parsed[key_str] = float(value_str) if value_str else 0.0
                else:
                    parsed[key_str] = value_str
            except (ValueError, TypeError):
                parsed[key_str] = value_str

        return parsed

    def _calculate_cumulative_volumes(self, quantities: List[int]) -> List[int]:
        """Calculate cumulative volumes for order book levels"""
        cumulative = []
        total = 0
        for qty in quantities:
            total += qty
            cumulative.append(total)
        return cumulative
