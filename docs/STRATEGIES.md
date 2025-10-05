# Trading Strategies Documentation

This document provides detailed information about the trading strategies implemented in the Mid-Frequency Trading System.

## Table of Contents

1. [Mean Reversion Strategy](#mean-reversion-strategy)
2. [Momentum Strategy](#momentum-strategy)
3. [Arbitrage Strategy](#arbitrage-strategy)
4. [Strategy Development](#strategy-development)
5. [Strategy Optimization](#strategy-optimization)

## Mean Reversion Strategy

### Overview

The Mean Reversion Strategy is based on the statistical concept that prices tend to revert to their historical mean over time. This strategy identifies when prices deviate significantly from their historical average and takes contrarian positions expecting reversion.

### Algorithm

1. **Calculate Moving Average**: Compute the simple moving average over a lookback period
2. **Calculate Z-Score**: Measure how many standard deviations the current price is from the mean
3. **Generate Signals**:
   - Buy when z-score < -threshold (oversold)
   - Sell when z-score > threshold (overbought)
4. **Risk Management**: Use stop-loss and take-profit levels

### Parameters

- `lookback_period` (default: 20): Number of periods for moving average calculation
- `z_score_threshold` (default: 2.0): Z-score threshold for entry signals
- `position_size` (default: 0.1): Base position size
- `max_positions` (default: 5): Maximum concurrent positions
- `stop_loss_pct` (default: 0.05): Stop loss percentage
- `take_profit_pct` (default: 0.03): Take profit percentage

### Configuration Example

```yaml
strategies:
  mean_reversion:
    symbols: ['AAPL', 'GOOGL', 'MSFT']
    parameters:
      lookback_period: 20
      z_score_threshold: 2.0
      position_size: 0.1
      max_positions: 5
      stop_loss_pct: 0.05
      take_profit_pct: 0.03
```

### Best Practices

- Use on liquid, mean-reverting assets
- Adjust threshold based on asset volatility
- Consider market regime (trending vs. ranging)
- Monitor correlation between positions

## Momentum Strategy

### Overview

The Momentum Strategy follows the principle that assets with strong recent performance tend to continue performing well in the near future. It identifies and rides price trends.

### Algorithm

1. **Calculate Momentum**: Compute price change over lookback period
2. **Filter Signals**: Require minimum momentum threshold
3. **Generate Signals**:
   - Buy when momentum > threshold (strong upward trend)
   - Sell when momentum < -threshold (strong downward trend)
4. **Exit Conditions**: Momentum reversal or profit targets

### Parameters

- `lookback_period` (default: 10): Number of periods for momentum calculation
- `momentum_threshold` (default: 0.02): Minimum momentum for entry
- `position_size` (default: 0.1): Base position size
- `max_positions` (default: 3): Maximum concurrent positions
- `stop_loss_pct` (default: 0.03): Stop loss percentage
- `take_profit_pct` (default: 0.05): Take profit percentage

### Configuration Example

```yaml
strategies:
  momentum:
    symbols: ['AMZN', 'TSLA', 'META']
    parameters:
      lookback_period: 10
      momentum_threshold: 0.02
      position_size: 0.1
      max_positions: 3
      stop_loss_pct: 0.03
      take_profit_pct: 0.05
```

### Best Practices

- Use on trending markets
- Avoid during market transitions
- Consider volatility-adjusted position sizing
- Use trailing stops for profit protection

## Arbitrage Strategy

### Overview

The Arbitrage Strategy identifies pairs of assets that move together and takes contrarian positions when they diverge, expecting the spread to revert to its mean.

### Algorithm

1. **Pair Selection**: Identify highly correlated asset pairs
2. **Calculate Spread**: Compute the price ratio or difference between pairs
3. **Z-Score Calculation**: Measure spread deviation from historical mean
4. **Generate Signals**:
   - Long the underperformer, short the outperformer when spread is wide
   - Exit positions when spread reverts to mean

### Parameters

- `lookback_period` (default: 60): Number of periods for correlation and spread calculation
- `z_score_threshold` (default: 2.0): Z-score threshold for entry signals
- `position_size` (default: 0.05): Base position size (smaller for arbitrage)
- `max_pairs` (default: 5): Maximum number of pairs to trade
- `min_correlation` (default: 0.7): Minimum correlation required for pair selection

### Configuration Example

```yaml
strategies:
  arbitrage:
    symbols: ['NVDA', 'AMD', 'CRM', 'ADBE']
    parameters:
      lookback_period: 60
      z_score_threshold: 2.0
      position_size: 0.05
      max_pairs: 5
      min_correlation: 0.7
```

### Best Practices

- Use on highly correlated assets
- Consider cointegration in addition to correlation
- Monitor for structural breaks in relationships
- Use smaller position sizes due to lower expected returns

## Strategy Development

### Creating a Custom Strategy

To create a custom strategy, inherit from `BaseStrategy`:

```python
from src.strategies.base import BaseStrategy, Signal

class CustomStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_param = self.config.get('custom_param', 1.0)
        
    async def on_market_data(self, market_data):
        """Process new market data"""
        for symbol, data in market_data.items():
            signals = self.generate_signals(symbol, data)
            for signal in signals:
                await self.execute_signal(signal)
                
    def generate_signals(self, symbol, data):
        """Generate trading signals"""
        signals = []
        
        # Your strategy logic here
        if self.should_buy(symbol, data):
            signal = Signal(
                symbol=symbol,
                side='buy',
                quantity=self.calculate_position_size(symbol, data),
                signal_type='entry',
                metadata={'reason': 'custom_logic'}
            )
            signals.append(signal)
            
        return signals
        
    def should_buy(self, symbol, data):
        """Your custom buy logic"""
        return False
        
    def calculate_position_size(self, symbol, data):
        """Calculate position size"""
        return self.position_size
```

### Strategy Registration

Register your custom strategy with the factory:

```python
from src.strategies.factory import StrategyFactory
from src.strategies.my_strategy import CustomStrategy

# Register the strategy
StrategyFactory.register_strategy('custom', CustomStrategy)

# Now you can use it in configuration
strategies:
  custom:
    symbols: ['AAPL']
    parameters:
      custom_param: 1.5
```

### Strategy Testing

Test your strategy thoroughly before deployment:

```python
import pytest
from src.strategies.my_strategy import CustomStrategy

class TestCustomStrategy:
    def test_signal_generation(self):
        strategy = CustomStrategy(
            name='test',
            symbols=['AAPL'],
            config={'custom_param': 1.0},
            order_router=mock_router,
            risk_manager=mock_risk_manager
        )
        
        # Test signal generation logic
        assert strategy.should_buy('AAPL', test_data) == expected_result
```

## Strategy Optimization

### Parameter Optimization

Use the backtesting framework to optimize strategy parameters:

```python
import itertools
from src.backtest.engine import BacktestEngine

# Define parameter ranges
param_combinations = itertools.product(
    range(10, 30, 5),      # lookback_period
    [1.5, 2.0, 2.5],       # z_score_threshold
    [0.05, 0.1, 0.15]      # position_size
)

best_performance = None
best_params = None

for lookback, threshold, size in param_combinations:
    # Create strategy with current parameters
    strategy = MeanReversionStrategy(
        name='optimization',
        symbols=['AAPL'],
        config={
            'lookback_period': lookback,
            'z_score_threshold': threshold,
            'position_size': size
        },
        order_router=router,
        risk_manager=risk_manager
    )
    
    # Run backtest
    engine = BacktestEngine(config)
    results = await engine.run_backtest(strategy, ['AAPL'], start_date, end_date)
    
    # Track best performance
    sharpe = results['performance']['sharpe_ratio']
    if best_performance is None or sharpe > best_performance:
        best_performance = sharpe
        best_params = (lookback, threshold, size)
```

### Walk-Forward Analysis

Implement walk-forward analysis for more robust optimization:

```python
async def walk_forward_analysis(strategy_class, symbols, config):
    """Perform walk-forward analysis"""
    results = []
    
    # Define training and testing periods
    periods = [
        (train_start_1, train_end_1, test_start_1, test_end_1),
        (train_start_2, train_end_2, test_start_2, test_end_2),
        # ... more periods
    ]
    
    for train_start, train_end, test_start, test_end in periods:
        # Optimize on training period
        best_params = await optimize_parameters(
            strategy_class, symbols, config, 
            train_start, train_end
        )
        
        # Test on testing period
        test_results = await run_backtest(
            strategy_class, symbols, best_params,
            test_start, test_end
        )
        
        results.append({
            'period': (test_start, test_end),
            'parameters': best_params,
            'performance': test_results['performance']
        })
        
    return results
```

### Risk-Adjusted Optimization

Optimize for risk-adjusted returns rather than just returns:

```python
def risk_adjusted_objective(returns, drawdown, volatility):
    """Calculate risk-adjusted performance score"""
    # Sharpe ratio
    sharpe = (np.mean(returns) - 0.02) / np.std(returns)
    
    # Penalize large drawdowns
    drawdown_penalty = max(0, drawdown - 0.10) * 10
    
    # Penalize high volatility
    vol_penalty = max(0, volatility - 0.30) * 5
    
    return sharpe - drawdown_penalty - vol_penalty
```

## Strategy Monitoring

### Performance Metrics

Monitor key performance metrics for each strategy:

- **Total Return**: Overall strategy performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Trade Duration**: Typical holding period

### Risk Metrics

Monitor risk metrics to ensure strategies stay within limits:

- **VaR (95%)**: Value at Risk
- **Expected Shortfall**: Average loss beyond VaR
- **Position Concentration**: Risk from large positions
- **Correlation Risk**: Risk from correlated positions

### Real-time Monitoring

Use the web dashboard to monitor strategy performance in real-time:

```python
# WebSocket monitoring
socket.on('strategy_update', (data) => {
    update_strategy_display(data);
});
```

## Common Strategy Patterns

### Trend Following

```python
class TrendFollowingStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Use moving average crossover
        short_ma = self.calculate_ma(data, self.short_period)
        long_ma = self.calculate_ma(data, self.long_period)
        
        if short_ma > long_ma and not self.in_position:
            return [self.create_buy_signal()]
        elif short_ma < long_ma and self.in_position:
            return [self.create_sell_signal()]
        
        return []
```

### Mean Reversion with Volatility Filter

```python
class VolatilityFilteredMeanReversion(BaseStrategy):
    def generate_signals(self, data):
        # Only trade when volatility is low
        current_vol = self.calculate_volatility(data)
        if current_vol > self.volatility_threshold:
            return []
            
        # Standard mean reversion logic
        z_score = self.calculate_z_score(data)
        if z_score < -self.threshold:
            return [self.create_buy_signal()]
        elif z_score > self.threshold:
            return [self.create_sell_signal()]
            
        return []
```

### Multi-factor Strategy

```python
class MultiFactorStrategy(BaseStrategy):
    def generate_signals(self, data):
        signals = []
        
        # Factor 1: Value
        if self.value_factor(data) > self.value_threshold:
            signals.append('value_buy')
            
        # Factor 2: Momentum
        if self.momentum_factor(data) > self.momentum_threshold:
            signals.append('momentum_buy')
            
        # Factor 3: Quality
        if self.quality_factor(data) > self.quality_threshold:
            signals.append('quality_buy')
            
        # Combine factors
        if len(signals) >= self.min_factors:
            return [self.create_combined_signal(signals)]
            
        return []
```

## Strategy Best Practices

1. **Robustness Testing**: Test strategies on different market conditions
2. **Parameter Stability**: Ensure parameters work across different periods
3. **Transaction Costs**: Always account for realistic transaction costs
4. **Market Impact**: Consider the impact of your trades on prices
5. **Risk Management**: Always use proper risk controls
6. **Monitoring**: Continuously monitor strategy performance
7. **Documentation**: Document all strategy logic and assumptions

## Performance Benchmarks

Typical performance expectations for mid-frequency strategies:

- **Sharpe Ratio**: 1.0 - 2.0 (good), > 2.0 (excellent)
- **Maximum Drawdown**: < 10% (conservative), < 20% (aggressive)
- **Win Rate**: 45% - 65% for mean reversion, 35% - 55% for momentum
- **Profit Factor**: > 1.5 (good), > 2.0 (excellent)

Note: These are general guidelines and actual performance depends on market conditions, strategy implementation, and risk management.