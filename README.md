# Mid-Frequency Trading System

A comprehensive, production-ready mid-frequency trading system built in Python with end-to-end functionality for real-world applications.

## 🏗️ System Architecture

The system follows a modular architecture with the following core components:

### Data Layer
- **Market Data Feeds**: Real-time data ingestion from multiple sources
- **Feed Handlers**: Normalization and processing of market data
- **Real-time Market Data Bus**: High-performance data distribution

### Strategy Layer  
- **Strategy/Signal Generation**: Mid-frequency trading algorithms
- **Model/Strategy Selector**: Dynamic strategy allocation
- **Parameter/Config Store**: Strategy configuration management

### Risk Management
- **Pre-trade Risk & Compliance**: Real-time risk assessment
- **Toxicity/Profit Analyzers**: Market impact analysis
- **RiskGate**: Comprehensive risk monitoring

### Execution Layer
- **Smart Order Router (SOR)**: Intelligent order routing
- **Execution Algorithms**: Advanced execution strategies
- **Venue Connectivity**: Exchange/ECN integrations

### Research & Analytics
- **Backtesting Framework**: Strategy validation and optimization
- **Post-trade Analytics**: Transaction cost analysis
- **Online Optimization**: Real-time strategy tuning

## 🚀 Features

- **Real-time Data Processing**: High-throughput market data handling
- **Multiple Strategy Support**: Mean reversion, momentum, arbitrage strategies
- **Advanced Risk Management**: Position sizing, drawdown control, correlation monitoring
- **Smart Order Routing**: Optimal execution across multiple venues
- **Comprehensive Backtesting**: Historical strategy validation
- **Performance Monitoring**: Real-time P&L, risk metrics, and system health
- **Web Dashboard**: Interactive monitoring and control interface

## 📁 Repository Structure

```
midfreq-trading-system/
├── src/                    # Core trading system
│   ├── data/              # Data handling components
│   ├── strategies/        # Trading strategies
│   ├── risk/              # Risk management
│   ├── execution/         # Order execution
│   ├── backtest/          # Backtesting framework
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── tests/                 # Unit tests
├── examples/              # Usage examples
├── web/                   # Web dashboard
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/midfreq-trading-system.git
cd midfreq-trading-system

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

## 📊 Quick Start

### 1. Start the Market Data Feed
```python
from src.data.feeds import MarketDataFeed

feed = MarketDataFeed(symbols=['AAPL', 'GOOGL', 'MSFT'])
feed.start()
```

### 2. Configure and Run Strategy
```python
from src.strategies.mean_reversion import MeanReversionStrategy
from src.execution.router import SmartOrderRouter

strategy = MeanReversionStrategy(
    symbols=['AAPL', 'GOOGL'],
    lookback_period=20,
    z_score_threshold=2.0
)

router = SmartOrderRouter()
system = TradingSystem(strategy, router)
system.run()
```

### 3. Monitor Performance
```bash
# Start web dashboard
cd web
python app.py
```

## 🔧 Configuration

The system uses YAML configuration files for all settings:

- **Market Data**: Data sources, symbols, update frequencies
- **Strategies**: Strategy parameters, risk limits
- **Execution**: Venue connections, order routing rules
- **Risk Management**: Position limits, drawdown controls

## 📈 Strategy Examples

### Mean Reversion Strategy
- Z-score based entry/exit signals
- Dynamic position sizing
- Correlation-adjusted signals

### Momentum Strategy  
- Moving average crossovers
- Relative strength ranking
- Volatility-adjusted returns

### Statistical Arbitrage
- Pairs trading with cointegration
- Cross-sectional momentum
- Factor-based selection

## 🛡️ Risk Management

- **Position Sizing**: Kelly criterion, volatility targeting
- **Drawdown Control**: Maximum drawdown limits
- **Correlation Monitoring**: Portfolio correlation analysis
- **Real-time P&L**: Mark-to-market accounting

## 📊 Performance Analytics

- **Transaction Cost Analysis**: Slippage, market impact
- **Risk Metrics**: Sharpe ratio, VaR, maximum drawdown
- **Execution Quality**: Fill rates, timing analysis
- **Strategy Attribution**: P&L decomposition

## 🔍 Monitoring & Alerting

The web dashboard provides:
- Real-time P&L and position monitoring
- System health and latency metrics
- Risk limit monitoring and alerts
- Strategy performance tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading financial instruments involves substantial risk. Past performance does not guarantee future results. Always conduct thorough testing and risk assessment before deploying with real capital.