# User Guide

This guide will help you understand and use the Mid-Frequency Trading System effectively.

## Table of Contents

1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Configuration](#configuration)
4. [Running Strategies](#running-strategies)
5. [Monitoring](#monitoring)
6. [Backtesting](#backtesting)
7. [Risk Management](#risk-management)
8. [Troubleshooting](#troubleshooting)

## System Overview

The Mid-Frequency Trading System is a comprehensive platform for developing, testing, and deploying algorithmic trading strategies. It includes:

- **Data Layer**: Real-time market data ingestion and processing
- **Strategy Layer**: Multiple trading strategy implementations
- **Risk Management**: Comprehensive risk controls and monitoring
- **Execution Layer**: Smart order routing and execution algorithms
- **Backtesting**: Historical strategy validation and optimization
- **Web Dashboard**: Real-time monitoring and control interface

## Getting Started

### Quick Start

1. **Start the System**
   ```bash
   python src/main.py
   ```

2. **Access Web Dashboard**
   ```bash
   cd web
   python app.py
   ```
   Then open http://localhost:8080 in your browser

3. **Run Examples**
   ```bash
   python examples/basic_usage.py
   ```

### Basic Commands

```bash
# Start trading system
python -m src.main

# Run backtest
python examples/backtest_example.py

# Start web dashboard
cd web && python app.py

# Run tests
pytest tests/
```

## Configuration

### Main Configuration File

The system uses `config/config.yaml` for all settings. Key sections:

#### Market Data
```yaml
data_feed:
  symbols: ['AAPL', 'GOOGL', 'MSFT']  # Trading symbols
  sources: ['yahoo']                  # Data sources
  update_frequency: 1.0              # Update interval in seconds
```

#### Strategies
```yaml
strategies:
  mean_reversion:
    symbols: ['AAPL', 'GOOGL']
    parameters:
      lookback_period: 20
      z_score_threshold: 2.0
```

#### Risk Management
```yaml
risk_management:
  max_position_size: 100000
  max_drawdown_pct: 0.10
  initial_cash: 1000000
```

### Environment Variables

You can override configuration using environment variables:

```bash
export TRADING_SYSTEM_INITIAL_CASH=500000
export TRADING_SYSTEM_MAX_DRAWDOWN=0.05
```

## Running Strategies

### Available Strategies

1. **Mean Reversion**: Buys oversold, sells overbought assets
2. **Momentum**: Follows price trends and momentum
3. **Arbitrage**: Exploits price relationships between assets

### Starting a Strategy

```python
from src.main import TradingSystem

async def start_trading():
    system = TradingSystem()
    await system.initialize()
    await system.start()
```

### Strategy Configuration

Each strategy has configurable parameters:

#### Mean Reversion
- `lookback_period`: Number of periods for mean calculation
- `z_score_threshold`: Z-score threshold for entry/exit
- `position_size`: Size of each position
- `max_positions`: Maximum number of concurrent positions

#### Momentum
- `momentum_threshold`: Minimum momentum for entry
- `stop_loss_pct`: Stop loss percentage
- `take_profit_pct`: Take profit percentage

#### Arbitrage
- `min_correlation`: Minimum correlation for pair trading
- `max_pairs`: Maximum number of pairs to trade

## Monitoring

### Web Dashboard

The web dashboard provides real-time monitoring:

- **Portfolio Value**: Current portfolio value and P&L
- **Active Positions**: Current open positions
- **Strategy Performance**: Performance metrics for each strategy
- **Risk Metrics**: VaR, drawdown, and other risk measures
- **System Log**: Real-time system events and alerts

### API Endpoints

```bash
# Get system status
curl http://localhost:8080/api/status

# Get performance metrics
curl http://localhost:8080/api/performance

# Get strategy information
curl http://localhost:8080/api/strategies
```

### Monitoring Commands

```bash
# Check system logs
tail -f logs/trading_system.log

# Monitor system resources
htop

# Check network connections
netstat -an | grep 8080
```

## Backtesting

### Running a Backtest

```python
from src.backtest.engine import BacktestEngine
from datetime import datetime

async def run_backtest():
    engine = BacktestEngine({
        'initial_capital': 100000,
        'transaction_cost': 0.001
    })
    
    results = await engine.run_backtest(
        strategy=my_strategy,
        symbols=['AAPL', 'GOOGL'],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    print(f"Total Return: {results['summary']['total_return']:.2%}")
```

### Backtest Parameters

- `initial_capital`: Starting capital amount
- `transaction_cost`: Trading costs as percentage
- `slippage`: Expected slippage as percentage
- `data_frequency`: Data frequency (1min, 5min, 1H, 1D)

### Performance Metrics

The system calculates comprehensive performance metrics:

- **Total Return**: Overall strategy return
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

## Risk Management

### Risk Controls

The system includes multiple risk management features:

1. **Position Limits**: Maximum position size per asset
2. **Portfolio Limits**: Maximum total portfolio value
3. **Drawdown Limits**: Maximum acceptable drawdown
4. **VaR Limits**: Value at Risk calculations
5. **Correlation Limits**: Maximum correlation between positions

### Risk Metrics

- **VaR (95%)**: 95% Value at Risk
- **Expected Shortfall**: Average loss beyond VaR threshold
- **Maximum Drawdown**: Largest historical drawdown
- **Sharpe Ratio**: Risk-adjusted return
- **Beta**: Market sensitivity

### Risk Configuration

```yaml
risk_management:
  max_position_size: 100000      # Max position per asset
  max_portfolio_value: 10000000  # Max total portfolio
  max_drawdown_pct: 0.10         # Max drawdown allowed
  var_confidence: 0.95           # VaR confidence level
  max_correlation: 0.8           # Max correlation between assets
```

## Troubleshooting

### Common Issues

1. **Data Feed Problems**
   - Check internet connection
   - Verify symbol availability
   - Review API limits

2. **Strategy Not Trading**
   - Check risk limits
   - Verify market data
   - Review strategy parameters

3. **Performance Issues**
   - Monitor CPU usage
   - Check memory consumption
   - Review log files

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: 'DEBUG'
```

### Performance Optimization

1. **Reduce Update Frequency**: Increase `update_frequency` in config
2. **Limit Symbols**: Reduce number of trading symbols
3. **Optimize Strategies**: Review strategy complexity
4. **Database**: Use PostgreSQL for better performance

## Advanced Features

### Custom Strategies

Create your own strategies by inheriting from `BaseStrategy`:

```python
from src.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    async def on_market_data(self, market_data):
        # Your strategy logic here
        pass
        
    def generate_signals(self, data):
        # Generate trading signals
        return []
```

### Database Integration

Configure database for persistent storage:

```yaml
database:
  type: 'postgresql'
  connection_string: 'postgresql://user:pass@localhost/trading_db'
```

### Notifications

Set up email notifications:

```yaml
notifications:
  enabled: true
  email:
    smtp_server: 'smtp.gmail.com'
    username: 'your_email@gmail.com'
    password: 'your_app_password'
    recipients: ['recipient@example.com']
```

## Best Practices

1. **Start Small**: Begin with paper trading
2. **Test Thoroughly**: Use backtesting before live trading
3. **Monitor Closely**: Watch system performance and risk metrics
4. **Keep Logs**: Maintain detailed logs for debugging
5. **Update Regularly**: Keep dependencies and strategies updated
6. **Risk Management**: Always use proper risk controls

## Support

- **Documentation**: Check `docs/` directory
- **Examples**: Review `examples/` directory
- **Issues**: Report bugs on GitHub
- **Community**: Join discussions on GitHub