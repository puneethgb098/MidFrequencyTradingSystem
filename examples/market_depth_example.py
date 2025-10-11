import asyncio
import os
from datetime import datetime
import redis.asyncio as redis
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.connectors.zerodha_data_ws import ZerodhaDataWebSocket
from src.services.order_book_service import OrderBookService

load_dotenv()


async def main():
    print("=" * 60)
    print("Market Depth Example - Level 5 Order Book")
    print("=" * 60)

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = await redis.from_url(redis_url)
    print(f"\nConnected to Redis: {redis_url}")

    api_key = os.getenv('ZERODHA_API_KEY')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    if not api_key or not access_token:
        print("\nError: Missing Zerodha credentials")
        print("Please set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN in .env file")
        return

    print("\n1. Configuring depth levels for instruments...")

    depth_config = {
        256265: 5,
        260105: 5,
        256521: 1,
        260361: 1
    }
    print("   - Nifty Current (256265): Level 5")
    print("   - BankNifty Current (260105): Level 5")
    print("   - Nifty Next (256521): Level 1")
    print("   - BankNifty Next (260361): Level 1")

    ws = ZerodhaDataWebSocket(
        api_key=api_key,
        access_token=access_token,
        redis_client=redis_client,
        depth_config=depth_config
    )

    print("\n2. Subscribing to instruments...")

    level_5_instruments = [256265, 260105]
    level_1_instruments = [256521, 260361]

    await ws.subscribe_instruments(level_5_instruments, depth_level=5)
    await ws.subscribe_instruments(level_1_instruments, depth_level=1)

    ws.start()
    print("   WebSocket connected and streaming data...")

    await asyncio.sleep(5)
    print("\n3. Fetching order book data...")

    order_book_service = OrderBookService(redis_client)

    for token in level_5_instruments:
        print(f"\n   Instrument Token: {token}")

        order_book = await order_book_service.get_order_book(token)

        if order_book:
            print(f"   Last Price: {order_book['last_price']:.2f}")
            print(f"   Spread: {order_book['spread']:.2f} ({order_book['spread_pct']:.3f}%)")
            print(f"   Imbalance: {order_book['imbalance']:.2%}")
            print(f"   Depth Level: {order_book['depth_level']}")

            print("\n   Bids (Level 5):")
            for bid in order_book['bids']:
                print(f"      L{bid['level']}: {bid['price']:.2f} x {bid['quantity']:,} (Cumulative: {bid['cumulative']:,})")

            print("\n   Asks (Level 5):")
            for ask in order_book['asks']:
                print(f"      L{ask['level']}: {ask['price']:.2f} x {ask['quantity']:,} (Cumulative: {ask['cumulative']:,})")
        else:
            print(f"   No data available yet")

    print("\n4. Fetching price history for charting...")
    history = await order_book_service.get_price_history(256265, count=10)

    if history['timestamps']:
        print(f"\n   Recent price data (last {len(history['timestamps'])} ticks):")
        for i in range(min(5, len(history['timestamps']))):
            print(f"      {history['timestamps'][i]}: Bid={history['bid_prices'][i]:.2f}, "
                  f"Ask={history['ask_prices'][i]:.2f}, Last={history['last_prices'][i]:.2f}")

    print("\n5. Demonstrating dynamic depth level changes...")

    ws.set_depth_level(256521, 5)
    print("   Changed Nifty Next (256521) from Level 1 to Level 5")

    await asyncio.sleep(3)

    order_book = await order_book_service.get_order_book(256521)
    if order_book:
        print(f"   New depth level: {order_book['depth_level']}")
        print(f"   Bids available: {len(order_book['bids'])}")
        print(f"   Asks available: {len(order_book['asks'])}")

    print("\n6. Performance metrics...")

    multiple_data = await order_book_service.get_multiple_instruments([256265, 260105, 256521, 260361])
    print(f"   Fetched data for {len(multiple_data)} instruments simultaneously")

    for token, data in multiple_data.items():
        print(f"      Token {token}: Last Price = {data.get('last_price', 'N/A')}")

    print("\n" + "=" * 60)
    print("Example completed. WebSocket will continue running...")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        while True:
            await asyncio.sleep(10)

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Latest data:")
            for token in [256265, 260105]:
                order_book = await order_book_service.get_order_book(token)
                if order_book:
                    print(f"   {token}: Last={order_book['last_price']:.2f}, "
                          f"Spread={order_book['spread']:.2f}, "
                          f"Imbalance={order_book['imbalance']:+.2%}")

    except KeyboardInterrupt:
        print("\n\nStopping...")
        ws.stop()
        await redis_client.close()
        print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
