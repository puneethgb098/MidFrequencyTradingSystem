import asyncio
import logging
import os
from src.connectors.zerodha_data_ws import ZerodhaDataWebSocket
from src.infra.bus import RedisStreamBus, EventBus
from src.infra.cache import RedisCache
import redis.asyncio as redis

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Configuration
    kite_api_key = os.getenv('KITE_API_KEY')
    kite_access_token = os.getenv('KITE_ACCESS_TOKEN')
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Initialize components
    redis_client = redis.from_url(redis_url)
    redis_bus = RedisStreamBus(redis_url)
    event_bus = EventBus(redis_bus)
    cache = RedisCache(redis_url)
    
    # Initialize Zerodha WebSocket
    zerodha_ws = ZerodhaDataWebSocket(kite_api_key, kite_access_token, redis_client)
    
    # Subscribe to NIFTY and BANKNIFTY futures
    # These token IDs would come from Kite instruments list
    nifty_tokens = [256265, 256521]  # Example: Current and next month NIFTY futures
    banknifty_tokens = [260105, 260361]  # Example: Current and next month BANKNIFTY futures
    
    all_tokens = nifty_tokens + banknifty_tokens
    
    try:
        logger.info("Starting market data service...")
        await redis_bus.start()
        
        # Subscribe to instruments
        await zerodha_ws.subscribe_instruments(all_tokens)
        zerodha_ws.start()
        
        logger.info(f"Subscribed to {len(all_tokens)} instruments")
        
        # Keep service running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down market data service...")
        zerodha_ws.stop()
        await redis_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
