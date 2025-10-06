# Mid-Frequency Trading System

A production-ready, modular algorithmic trading system built in Python for mid-frequency trading strategies. The system provides a comprehensive framework for market data processing, strategy execution, risk management, and portfolio optimization.

## 🏗️ System Architecture

The system implements a microservices-based architecture with asynchronous processing capabilities, designed for scalability and real-time performance.

### Core Components

- **Data Layer**: Real-time market data ingestion and processing
- **Strategy Engine**: Pluggable trading strategy framework with factory pattern
- **Risk Management**: Dual-layer risk controls (portfolio-level and pre-trade)
- **Execution Engine**: Smart order routing with venue connectivity
- **Order Management System**: Comprehensive order lifecycle management
- **Portfolio Management**: Real-time position tracking and P&L calculation
- **Backtesting Framework**: Historical strategy validation and optimization
- **Infrastructure Services**: Logging, configuration, and system monitoring

## 📁 Repository Structure

```
MidFrequencyTradingSystem/
├── src/                          # Core trading system source code
│   ├── backtest/                # Backtesting engine and utilities
│   ├── connectors/              # Market data and broker connectors
│   ├── data/                    # Market data processing and feeds
│   ├── execution/               # Order execution and smart routing
│   ├── infra/                   # Infrastructure and system services
│   ├── oms/                     # Order Management System
│   ├── portfolio/               # Portfolio management and tracking
│   ├── risk/                    # Risk management framework
│   ├── risk_gate/               # Pre-trade risk validation
│   ├── services/                # System services and utilities
│   ├── strategies/              # Trading strategy implementations
│   ├── utils/                   # Common utilities and helpers
│   └── main.py                  # System entry point and orchestrator
├── config/                      # Configuration files
├── docs/                        # Documentation
├── examples/                    # Usage examples and tutorials
├── tests/                       # Unit and integration tests
├── web/                         # Web dashboard and monitoring
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Container definition
├── Makefile                     # Build and deployment scripts
└── requirements.txt             # Python dependencies
```

## 🚀 Key Features

### Trading Capabilities
- **Multiple Strategy Support**: Mean reversion, momentum, statistical arbitrage
- **Dynamic Strategy Loading**: Runtime strategy instantiation and management
- **Multi-Asset Support**: Equities, futures, options trading
- **Real-time Signal Generation**: Low-latency strategy execution

### Risk Management
- **Pre-trade Validation**: Order-level risk checks via RiskGate
- **Portfolio Risk Monitoring**: Real-time exposure and correlation analysis
- **Dynamic Position Sizing**: Volatility-adjusted position management
- **Drawdown Controls**: Automated position reduction during adverse conditions

### Execution Features
- **Smart Order Routing**: Intelligent venue selection and order splitting
- **Execution Algorithms**: TWAP, VWAP, and custom execution strategies
- **Slippage Optimization**: Market impact minimization
- **Fill Quality Analytics**: Execution performance monitoring

### System Infrastructure
- **Asynchronous Architecture**: High-performance async/await processing
- **Modular Design**: Pluggable components for easy extension
- **Configuration Management**: YAML-based system configuration
- **Comprehensive Logging**: Structured logging with multiple output formats
- **Docker Support**: Containerized deployment with docker-compose

## 🛠️ Installation and Setup

### Prerequisites
- Python 3.8+ with asyncio support
- Docker and docker-compose (optional)
- Market data subscriptions (for live trading)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/puneethgb098/MidFrequencyTradingSystem.git
cd MidFrequencyTradingSystem
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the system**
```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your specific settings
```

4. **Run the system**
```bash
python src/main.py
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Or use the Makefile
make docker-build
make docker-run
```

## 📊 Configuration

The system uses YAML configuration files for all components:

### Core Configuration Sections

- **Data Feeds**: Market data sources and connection parameters
- **Strategies**: Strategy parameters and risk limits
- **Risk Management**: Portfolio limits and correlation thresholds
- **Execution**: Venue connections and routing rules
- **Logging**: Log levels and output destinations

### Example Configuration

```yaml
# Market Data Configuration
data_feed:
  provider: "alphavantage"  # or "iex", "quandl"
  api_key: "your_api_key"
  symbols: ["AAPL", "GOOGL", "MSFT"]
  update_frequency: 1000  # milliseconds

# Strategy Configuration
strategies:
  mean_reversion:
    enabled: true
    lookback_period: 20
    z_score_threshold: 2.0
    max_position_size: 10000

# Risk Management
risk_management:
  max_portfolio_value: 1000000
  max_single_position: 50000
  max_correlation: 0.7
  max_drawdown: 0.15
```

## 🔧 Usage Examples

### Basic Strategy Implementation

```python
from src.strategies.base import BaseStrategy
from src.utils.config import ConfigManager

class CustomMeanReversion(BaseStrategy):
    def __init__(self, config, order_router, risk_manager):
        super().__init__(config, order_router, risk_manager)
        self.lookback = config.get('lookback_period', 20)

    async def on_market_data(self, market_data):
        # Implement your trading logic here
        signal = self.calculate_z_score(market_data)
        if abs(signal) > self.config.get('threshold', 2.0):
            await self.place_order(signal, market_data.symbol)
```

### System Monitoring

```python
from src.main import TradingSystem

# Initialize and start system
system = TradingSystem("config/config.yaml")
await system.initialize()
await system.start()

# Get system status
status = system.get_system_status()
print(f"System running: {status['is_running']}")
print(f"Active strategies: {len(status['strategies'])}")
```

## 🎯 Strategy Development

The system provides a flexible framework for developing custom trading strategies:

### Strategy Base Class
All strategies inherit from `BaseStrategy` which provides:
- Market data handling
- Order placement interface
- Risk management integration
- Performance tracking

### Available Strategy Types
- **Mean Reversion**: Z-score based entry/exit signals
- **Momentum**: Moving average and breakout strategies  
- **Statistical Arbitrage**: Pairs trading and cointegration
- **Market Making**: Bid-ask spread capture strategies

## 📈 Performance Monitoring

### Real-time Metrics
- P&L tracking and attribution
- Risk metrics (VaR, drawdown, Sharpe ratio)
- Execution quality analysis
- System latency monitoring

### Web Dashboard
Access the monitoring dashboard at `http://localhost:8080` when running:
- Real-time position monitoring
- Strategy performance charts
- Risk limit alerts
- System health indicators

## 🔒 Risk Management Framework

### Pre-trade Controls (RiskGate)
- Order size validation
- Position limit checks
- Correlation analysis
- Liquidity requirements

### Portfolio-level Risk (RiskManager)
- Real-time exposure calculation
- Dynamic hedging recommendations
- Stress testing and scenario analysis
- Regulatory compliance checks

## 🧪 Testing and Backtesting

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python -m pytest tests/test_strategies.py -v
```

### Backtesting Framework
```python
from src.backtest.engine import BacktestEngine

engine = BacktestEngine("config/backtest.yaml")
results = engine.run_backtest(
    start_date="2023-01-01",
    end_date="2023-12-31",
    strategies=["mean_reversion", "momentum"]
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add unit tests for new functionality
- Update documentation for API changes
- Ensure all tests pass before submitting


