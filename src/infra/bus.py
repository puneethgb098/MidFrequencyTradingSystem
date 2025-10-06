import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import redis.asyncio as redis
from datetime import datetime

class RedisStreamBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.logger = logging.getLogger(__name__)
        self.consumers: Dict[str, Callable] = {}
        self.running = False
        
    async def publish(self, stream: str, data: Dict[str, Any], maxlen: int = 10000):
        """Publish event to Redis Stream"""
        try:
            await self.redis.xadd(stream, data, maxlen=maxlen)
        except Exception as e:
            self.logger.error(f"Failed to publish to {stream}: {e}")
            
    async def subscribe(self, stream: str, consumer_group: str, consumer_name: str, 
                      callback: Callable, start_id: str = ">"):
        """Subscribe to Redis Stream with consumer group"""
        try:
            # Create consumer group if it doesn't exist
            try:
                await self.redis.xgroup_create(stream, consumer_group, id="0", mkstream=True)
            except redis.RedisError:
                pass  # Group already exists
                
            while self.running:
                try:
                    # Read from stream
                    messages = await self.redis.xreadgroup(
                        consumer_group, consumer_name, {stream: start_id}, count=10, block=1000
                    )
                    
                    for stream_name, msgs in messages:
                        for msg_id, fields in msgs:
                            try:
                                await callback(msg_id, fields)
                                # Acknowledge message
                                await self.redis.xack(stream, consumer_group, msg_id)
                            except Exception as e:
                                self.logger.error(f"Error processing message {msg_id}: {e}")
                                
                except redis.RedisError as e:
                    self.logger.error(f"Redis error in consumer: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Subscription error: {e}")
            
    async def start(self):
        """Start the message bus"""
        self.running = True
        
    async def stop(self):
        """Stop the message bus"""
        self.running = False
        await self.redis.close()

class EventBus:
    def __init__(self, redis_bus: RedisStreamBus):
        self.redis_bus = redis_bus
        self.logger = logging.getLogger(__name__)
        
    async def publish_market_data(self, instrument_token: int, tick_data: Dict[str, Any]):
        """Publish market data event"""
        await self.redis_bus.publish(
            f"market_data:{instrument_token}",
            {**tick_data, "event_type": "TICK", "timestamp": datetime.utcnow().isoformat()}
        )
        
    async def publish_signal(self, strategy_name: str, signal_data: Dict[str, Any]):
        """Publish trading signal"""
        await self.redis_bus.publish(
            "trading_signals",
            {**signal_data, "strategy": strategy_name, "timestamp": datetime.utcnow().isoformat()}
        )
        
    async def publish_risk_event(self, event_type: str, risk_data: Dict[str, Any]):
        """Publish risk management event"""
        await self.redis_bus.publish(
            "risk_events",
            {**risk_data, "event_type": event_type, "timestamp": datetime.utcnow().isoformat()}
        )
        
    async def publish_order_event(self, event_type: str, order_data: Dict[str, Any]):
        """Publish order execution event"""
        await self.redis_bus.publish(
            "order_events",
            {**order_data, "event_type": event_type, "timestamp": datetime.utcnow().isoformat()}
        )
