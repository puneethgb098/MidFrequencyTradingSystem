# Market Depth Feature - Level 5 Order Book

## Overview

The Mid-Frequency Trading System now supports Level 5 order book data extraction and real-time visualization. This enhancement provides deep market insights through comprehensive bid/ask depth analysis, enabling more sophisticated trading strategies.

## Features

### 1. Multi-Level Order Book Data

- **Level 1**: Best bid/ask prices and quantities
- **Level 5**: Complete 5-level market depth with:
  - All bid prices and quantities (5 levels)
  - All ask prices and quantities (5 levels)
  - Cumulative volumes at each level
  - Market imbalance metrics
  - Spread analysis

### 2. Configurable Depth Levels

Configure different depth levels per instrument for optimal performance:

```yaml
# config/live_config.yaml
market_depth:
  level_5_instruments: [256265, 260105]  # Full depth for key instruments
  default_depth_level: 1  # Level 1 for others
  stream_maxlen_level_1: 10000
  stream_maxlen_level_5: 5000
```

### 3. Real-Time Visualization

Web dashboard with dual-panel layout:

- **Price Chart**: Live streaming of best bid/ask and last traded price
- **Order Book Table**: 5-level depth with visual depth bars
- **Market Metrics**: Spread, imbalance, volume, and more
- **WebSocket Updates**: Real-time streaming at 1-second intervals

### 4. REST API Endpoints

#### Get Market Data for Multiple Instruments
```
GET /api/market_data?tokens=256265,260105
```

Response:
```json
{
  "256265": {
    "instrument_token": 256265,
    "last_price": 18500.50,
    "bid_price": 18500.00,
    "ask_price": 18501.00,
    "volume": 1234567
  }
}
```

#### Get Level 5 Order Book
```
GET /api/order_book/256265
```

Response:
```json
{
  "instrument_token": 256265,
  "last_price": 18500.50,
  "bids": [
    {"level": 1, "price": 18500.00, "quantity": 150, "cumulative": 150},
    {"level": 2, "price": 18499.50, "quantity": 200, "cumulative": 350},
    ...
  ],
  "asks": [
    {"level": 1, "price": 18501.00, "quantity": 125, "cumulative": 125},
    {"level": 2, "price": 18501.50, "quantity": 175, "cumulative": 300},
    ...
  ],
  "spread": 1.00,
  "spread_pct": 0.005,
  "imbalance": 0.15
}
```

#### Get Price History
```
GET /api/price_history/256265?count=100
```

Response:
```json
{
  "instrument_token": 256265,
  "timestamps": ["2025-10-11T10:30:00", ...],
  "bid_prices": [18500.00, ...],
  "ask_prices": [18501.00, ...],
  "last_prices": [18500.50, ...]
}
```

### 5. WebSocket Subscriptions

#### Subscribe to Order Book Updates
```javascript
socket.emit('subscribe_order_book', {
    instrument_token: 256265
});

socket.on('order_book_update', (data) => {
    console.log('Order book:', data);
});
```

#### Subscribe to Price Chart Updates
```javascript
socket.emit('subscribe_price_chart', {
    instrument_token: 256265
});

socket.on('price_update', (data) => {
    console.log('Price:', data);
});
```

## Architecture

### Data Flow

```
Zerodha WebSocket → ZerodhaDataWebSocket → Redis Streams
                                              ↓
                                       OrderBookService
                                              ↓
                                    REST API / WebSocket
                                              ↓
                                      Web Dashboard
```

### Components

1. **ZerodhaDataWebSocket** (`src/connectors/zerodha_data_ws.py`)
   - Connects to Kite Connect WebSocket
   - Processes tick data with configurable depth levels
   - Publishes to Redis streams with optimized maxlen

2. **OrderBookService** (`src/services/order_book_service.py`)
   - Retrieves order book data from Redis
   - Calculates metrics (spread, imbalance, cumulative volumes)
   - Provides historical data for charting

3. **Web Dashboard** (`web/app.py`, `web/templates/market_depth.html`)
   - REST endpoints for data access
   - WebSocket handlers for real-time updates
   - Interactive visualization with Chart.js

## Usage Examples

### Basic Usage

```python
import asyncio
import redis.asyncio as redis
from src.connectors.zerodha_data_ws import ZerodhaDataWebSocket
from src.services.order_book_service import OrderBookService

async def main():
    redis_client = await redis.from_url('redis://localhost:6379')

    # Configure depth levels
    depth_config = {
        256265: 5,  # Level 5 for Nifty
        260105: 5,  # Level 5 for BankNifty
        256521: 1   # Level 1 for others
    }

    # Initialize WebSocket
    ws = ZerodhaDataWebSocket(
        api_key='your_api_key',
        access_token='your_access_token',
        redis_client=redis_client,
        depth_config=depth_config
    )

    # Subscribe to instruments
    await ws.subscribe_instruments([256265, 260105], depth_level=5)
    await ws.subscribe_instruments([256521], depth_level=1)

    ws.start()

    # Access order book data
    service = OrderBookService(redis_client)
    order_book = await service.get_order_book(256265)

    print(f"Spread: {order_book['spread']:.2f}")
    print(f"Imbalance: {order_book['imbalance']:.2%}")

asyncio.run(main())
```

### Dynamic Depth Level Changes

```python
# Change depth level for an instrument at runtime
ws.set_depth_level(256521, 5)  # Upgrade to Level 5
```

### Running the Example

```bash
python examples/market_depth_example.py
```

## Web Dashboard

### Accessing the Market Depth Page

1. Start the web server:
   ```bash
   python web/app.py
   ```

2. Navigate to: `http://localhost:8080/market_depth`

3. Enter an instrument token (e.g., 256265 for Nifty Futures)

4. Click "Load Order Book" to view the current state

5. Click "Auto Refresh" to enable real-time streaming updates

### Dashboard Features

- **Live Price Chart**: Shows bid/ask/last price movement over time
- **Order Book Table**: 5-level depth with color-coded bid/ask rows
- **Visual Depth Bars**: Graphical representation of quantity at each level
- **Market Metrics**: Real-time spread, imbalance, and volume data
- **Auto-Refresh Mode**: Continuous WebSocket updates every second

## Performance Optimization

### Redis Stream Configuration

The system uses different maxlen values based on depth level:

- **Level 1**: 10,000 ticks retained (lower data volume)
- **Level 5**: 5,000 ticks retained (higher data volume)

This ensures Redis memory usage remains optimal while maintaining sufficient historical data.

### Selective Depth Configuration

Only enable Level 5 depth for instruments you actively trade:

```yaml
market_depth:
  level_5_instruments: [256265, 260105]  # Only key instruments
  default_depth_level: 1  # Everything else uses Level 1
```

This approach:
- Reduces Redis memory usage
- Minimizes network bandwidth
- Maintains real-time performance
- Focuses resources on critical instruments

## Error Handling

The system includes comprehensive error handling:

1. **Missing Depth Data**: Returns Level 1 data if Level 5 unavailable
2. **Redis Connection Issues**: Logs errors and continues processing
3. **Invalid Instrument Tokens**: Returns appropriate error messages
4. **WebSocket Reconnection**: Automatic reconnection with exponential backoff

## Integration with Trading Strategies

Use order book imbalance in trading signals:

```python
async def check_order_book_signal(instrument_token):
    service = OrderBookService(redis_client)
    order_book = await service.get_order_book(instrument_token)

    if order_book['imbalance'] > 0.3:  # Strong bid pressure
        return 'BUY_SIGNAL'
    elif order_book['imbalance'] < -0.3:  # Strong ask pressure
        return 'SELL_SIGNAL'

    return 'NEUTRAL'
```

## Configuration Reference

### Environment Variables

```bash
REDIS_URL=redis://localhost:6379
ZERODHA_API_KEY=your_api_key
ZERODHA_ACCESS_TOKEN=your_access_token
```

### YAML Configuration

```yaml
market_depth:
  level_5_instruments: [256265, 260105]
  default_depth_level: 1
  stream_maxlen_level_1: 10000
  stream_maxlen_level_5: 5000
```

## Troubleshooting

### No Data Available

1. Check Redis connection: `redis-cli ping`
2. Verify WebSocket is running: Check logs for "WebSocket connected"
3. Confirm instrument subscription: Look for "Subscribed to N instruments"

### Slow Performance

1. Reduce number of Level 5 instruments
2. Increase Redis stream maxlen values
3. Adjust WebSocket update frequency
4. Check network latency to Zerodha servers

### Incorrect Depth Level

1. Verify configuration in `config/live_config.yaml`
2. Check `depth_config` passed to `ZerodhaDataWebSocket`
3. Use `set_depth_level()` to update at runtime

## Future Enhancements

- [ ] Order book heatmap visualization
- [ ] Depth analysis alerts (spread widening, imbalance shifts)
- [ ] Historical depth data analysis
- [ ] Machine learning models using depth features
- [ ] Multi-instrument depth correlation analysis

## Support

For issues or questions:
1. Check logs in `logs/trading_system.log`
2. Review configuration in `config/live_config.yaml`
3. Run the example script to verify setup
4. Consult the main documentation in `docs/`
