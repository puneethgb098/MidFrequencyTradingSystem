# API Reference

This document provides detailed API documentation for the Mid-Frequency Trading System.

## Table of Contents

1. [Main System API](#main-system-api)
2. [Strategy API](#strategy-api)
3. [Data Feed API](#data-feed-api)
4. [Risk Management API](#risk-management-api)
5. [Execution API](#execution-api)
6. [Backtesting API](#backtesting-api)
7. [Web API](#web-api)

## Main System API

### TradingSystem Class

The main entry point for the trading system.

```python
from src.main import TradingSystem

# Initialize system
system = TradingSystem(config_path="config/config.yaml")

# Initialize components
await system.initialize()

# Start trading
await system.start()

# Stop trading
await system.stop()

# Get system status
status = system.get_system_status()
```

#### Methods

- `__init__(config_path: str)`: Initialize trading system
- `async initialize()`: Initialize all components
- `async start()`: Start the trading system
- `async stop()`: Stop the trading system
- `get_system_status() -> Dict[str, Any]`: Get current system status

#### System Status

```python
{
    'is_running': bool,
    'strategies': Dict[str, Dict],
    'data_feed': Dict[str, Any],
    'risk_metrics': Dict[str, Any]
}
```

## Strategy API

### BaseStrategy Class

Abstract base class for all trading strategies.

```python
from src.strategies.base import BaseStrategy, Signal

class MyStrategy(BaseStrategy):
    async def on_market_data(self, market_data: Dict[str, MarketData]):
        # Process new market data
        pass
        
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        # Generate trading signals
        return []
```

#### Signal Class

```python
signal = Signal(
    symbol='AAPL',
    side='buy',           # 'buy' or 'sell'
    quantity=100,
    signal_type='entry',  # 'entry', 'exit', 'adjust'
    confidence=0.8,
    metadata={'reason': 'oversold'}
)
```

#### Strategy Methods

- `async on_market_data(market_data: Dict[str, MarketData])`: Process market data
- `generate_signals(data: Dict[str, Any]) -> List[Signal]`: Generate signals
- `async execute_signal(signal: Signal)`: Execute trading signal
- `async start()`: Start strategy
- `async stop()`: Stop strategy
- `get_status() -> Dict[str, Any]`: Get strategy status

### StrategyFactory

Factory for creating strategy instances.

```python
from src.strategies.factory import StrategyFactory

# Create strategy
strategy = StrategyFactory.create_strategy(
    'mean_reversion',
    config,
    order_router,
    risk_manager
)

# Get available strategies
available = StrategyFactory.get_available_strategies()
```

## Data Feed API

### MarketData Class

```python
from data.feeds import MarketData

market_data = MarketData(
    symbol='AAPL',
    timestamp=datetime.now(),
    bid=150.0,
    ask=150.05,
    last=150.02,
    volume=1000
)
```

### MarketDataFeed Class

```python
from data.feeds import MarketDataFeed

# Initialize data feed
feed = MarketDataFeed({
    'symbols': ['AAPL', 'GOOGL'],
    'sources': ['yahoo'],
    'update_frequency': 1.0
})

# Start feed
await feed.start()

# Get latest data
data = await feed.get_latest_data()

# Stop feed
await feed.stop()
```

#### Methods

- `async start()`: Start data feed
- `async stop()`: Stop data feed
- `async get_latest_data() -> Dict[str, MarketData]`: Get latest market data
- `get_status() -> Dict[str, Any]`: Get feed status

## Risk Management API

### RiskManager Class

```python
from risk.manager import RiskManager

# Initialize risk manager
risk_manager = RiskManager({
    'max_position_size': 100000,
    'max_drawdown_pct': 0.10,
    'initial_cash': 1000000
})

# Check trading signal
if await risk_manager.check_signal(signal):
    # Signal passes risk checks
    pass
```

#### Methods

- `async check_signal(signal: Signal) -> bool`: Check if signal passes risk checks
- `update_position(symbol: str, quantity: float, price: float)`: Update position tracking
- `update_market_prices(prices: Dict[str, float])`: Update market prices
- `get_metrics() -> Dict[str, Any]`: Get risk metrics
- `get_status() -> Dict[str, Any]`: Get risk manager status

#### Risk Metrics

```python
{
    'portfolio_value': float,
    'cash': float,
    'realized_pnl': float,
    'unrealized_pnl': float,
    'max_drawdown': float,
    'positions': Dict[str, Dict],
    'risk_metrics': {
        'var_95': float,
        'var_99': float,
        'sharpe_ratio': float,
        'max_drawdown': float
    }
}
```

## Execution API

### SmartOrderRouter Class

```python
from execution.router import SmartOrderRouter

# Initialize router
router = SmartOrderRouter({
    'venues': ['simulation'],
    'transaction_cost': 0.001
}, risk_manager)

# Submit order
order_id = await router.submit_order(
    symbol='AAPL',
    side='buy',
    quantity=100,
    order_type='market'
)

# Cancel order
await router.cancel_order(order_id)
```

#### Methods

- `async start()`: Start order router
- `async stop()`: Stop order router
- `async submit_order(**kwargs) -> str`: Submit order
- `async cancel_order(order_id: str) -> bool`: Cancel order
- `get_performance_metrics() -> Dict[str, Any]`: Get router performance

### Order Class

```python
from execution.router import Order, OrderType, OrderStatus

order = Order(
    id='ORDER_123',
    symbol='AAPL',
    side='buy',
    quantity=100,
    order_type=OrderType.MARKET,
    status=OrderStatus.PENDING
)
```

## Backtesting API

### BacktestEngine Class

```python
from backtest.engine import BacktestEngine

# Initialize backtest engine
engine = BacktestEngine({
    'initial_capital': 100000,
    'transaction_cost': 0.001
})

# Run backtest
results = await engine.run_backtest(
    strategy=strategy,
    symbols=['AAPL', 'GOOGL'],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)
```

#### Methods

- `async run_backtest(**kwargs) -> Dict[str, Any]`: Run complete backtest
- `get_results() -> Dict[str, Any]`: Get backtest results

### BacktestData Class

```python
from backtest.data import BacktestData

# Load historical data
data = BacktestData(
    symbols=['AAPL', 'GOOGL'],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

await data.load_data()
```

#### Methods

- `async load_data()`: Load historical data
- `get_next_data() -> Optional[Dict[str, Any]]`: Get next data point
- `get_all_data() -> pd.DataFrame`: Get all data
- `reset()`: Reset data iterator

### PerformanceMetrics Class

```python
from backtest.metrics import PerformanceMetrics

# Calculate metrics
metrics = PerformanceMetrics()
results = metrics.calculate_all_metrics(
    returns=daily_returns,
    trades=trades,
    initial_capital=100000
)
```

#### Methods

- `calculate_all_metrics(**kwargs) -> Dict[str, Any]`: Calculate all metrics
- `calculate_monthly_returns(**kwargs) -> pd.DataFrame`: Calculate monthly returns
- `calculate_rolling_metrics(**kwargs) -> Dict[str, List[float]]`: Calculate rolling metrics
- `generate_performance_report(**kwargs) -> str`: Generate formatted report

## Web API

### REST Endpoints

#### System Status
```http
GET /api/status
```

Response:
```json
{
    "is_running": true,
    "strategies": {
        "mean_reversion": {
            "name": "mean_reversion",
            "is_running": true,
            "symbols": ["AAPL", "GOOGL"]
        }
    },
    "data_feed": {
        "is_running": true,
        "symbols": ["AAPL", "GOOGL"]
    }
}
```

#### Performance Metrics
```http
GET /api/performance
```

Response:
```json
{
    "portfolio_value": 1050000.0,
    "realized_pnl": 25000.0,
    "unrealized_pnl": 25000.0,
    "max_drawdown": 0.023,
    "risk_metrics": {
        "var_95": -0.015,
        "sharpe_ratio": 1.25
    }
}
```

#### Start System
```http
POST /api/start
```

Response:
```json
{
    "status": "success",
    "message": "Trading system started"
}
```

#### Stop System
```http
POST /api/stop
```

Response:
```json
{
    "status": "success",
    "message": "Trading system stopped"
}
```

#### Configuration
```http
GET /api/config
POST /api/config
```

### WebSocket Events

#### Connection
```javascript
const socket = io('http://localhost:8080');

socket.on('connect', () => {
    console.log('Connected to trading system');
});
```

#### Status Updates
```javascript
socket.on('status_update', (data) => {
    console.log('System status:', data);
});
```

#### Performance Updates
```javascript
socket.on('performance_update', (data) => {
    console.log('Performance update:', data);
});
```

#### Subscriptions
```javascript
// Subscribe to status updates
socket.emit('subscribe_status');

// Subscribe to performance updates
socket.emit('subscribe_performance');
```

## Configuration API

### ConfigManager Class

```python
from src.utils.config import ConfigManager

# Load configuration
config = ConfigManager("config/config.yaml")

# Get configuration value
symbols = config.get('data_feed.symbols')

# Set configuration value
config.set('data_feed.update_frequency', 2.0)

# Save configuration
config.save_config()
```

#### Methods

- `get(key: str, default: Any = None) -> Any`: Get configuration value
- `set(key: str, value: Any)`: Set configuration value
- `save_config()`: Save configuration to file
- `get_all() -> Dict[str, Any]`: Get entire configuration

## Utility API

### Logging

```python
from src.utils.logger import setup_logging, get_logger

# Setup logging
logger = setup_logging(config)

# Get logger for specific module
strategy_logger = get_logger('strategies.mean_reversion')
```

### Error Handling

```python
class TradingSystemError(Exception):
    """Base exception for trading system"""
    pass

class RiskLimitExceeded(TradingSystemError):
    """Raised when risk limits are exceeded"""
    pass

class DataFeedError(TradingSystemError):
    """Raised when data feed encounters an error"""
    pass
```

## Examples

### Complete Strategy Implementation

```python
import asyncio
from src.main import TradingSystem

async def main():
    # Initialize system
    system = TradingSystem()
    await system.initialize()
    
    # Start trading
    await system.start()
    
    # Monitor for 1 hour
    await asyncio.sleep(3600)
    
    # Stop trading
    await system.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Strategy

```python
from src.strategies.base import BaseStrategy, Signal

class CustomStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.threshold = 0.02
        
    async def on_market_data(self, market_data):
        for symbol, data in market_data.items():
            if self.should_buy(data):
                signal = Signal(
                    symbol=symbol,
                    side='buy',
                    quantity=100,
                    signal_type='entry'
                )
                await self.execute_signal(signal)
                
    def should_buy(self, data):
        # Your custom logic here
        return data.last < data.bid * (1 - self.threshold)
```

For more examples, see the `examples/` directory.