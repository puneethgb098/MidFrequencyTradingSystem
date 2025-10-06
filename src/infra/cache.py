import json
import logging
from typing import Any, Optional, Dict
import redis.asyncio as redis
from datetime import datetime, timedelta

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.logger = logging.getLogger(__name__)
        
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache with optional TTL"""
        try:
            serialized = json.dumps(value, default=str)
            if ttl_seconds:
                await self.redis.setex(key, ttl_seconds, serialized)
            else:
                await self.redis.set(key, serialized)
        except Exception as e:
            self.logger.error(f"Cache set error for {key}: {e}")
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Cache get error for {key}: {e}")
            return None
            
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            self.logger.error(f"Cache delete error for {key}: {e}")
            
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions snapshot"""
        return await self.get("positions:current") or {}
        
    async def set_positions(self, positions: Dict[str, Any]):
        """Set current positions snapshot"""
        await self.set("positions:current", positions, ttl_seconds=300)
        
    async def get_market_data(self, instrument_token: int) -> Optional[Dict[str, Any]]:
        """Get latest market data for instrument"""
        return await self.get(f"market_data:{instrument_token}:latest")
        
    async def set_market_data(self, instrument_token: int, data: Dict[str, Any]):
        """Set latest market data for instrument"""
        await self.set(f"market_data:{instrument_token}:latest", data, ttl_seconds=60)

class PositionCache:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache
        self.logger = logging.getLogger(__name__)
        
    async def update_position(self, instrument_token: int, quantity: int, average_price: float):
        """Update position in cache"""
        positions = await self.cache.get_positions()
        
        key = str(instrument_token)
        if key in positions:
            # Update existing position
            existing_qty = positions[key]['quantity']
            existing_avg = positions[key]['average_price']
            
            new_qty = existing_qty + quantity
            if new_qty != 0:
                new_avg = ((existing_qty * existing_avg) + (quantity * average_price)) / new_qty
                positions[key] = {
                    'quantity': new_qty,
                    'average_price': new_avg,
                    'last_update': datetime.utcnow().isoformat()
                }
            else:
                # Position closed
                del positions[key]
        else:
            # New position
            if quantity != 0:
                positions[key] = {
                    'quantity': quantity,
                    'average_price': average_price,
                    'last_update': datetime.utcnow().isoformat()
                }
                
        await self.cache.set_positions(positions)
        
    async def get_position(self, instrument_token: int) -> Optional[Dict[str, Any]]:
        """Get position for specific instrument"""
        positions = await self.cache.get_positions()
        return positions.get(str(instrument_token))
