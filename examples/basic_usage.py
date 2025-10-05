#!/usr/bin/env python3
"""
Basic Usage Example

Demonstrates how to use the Mid-Frequency Trading System.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import TradingSystem
from src.strategies.factory import StrategyFactory
from src.backtest.engine import BacktestEngine
from src.utils.config import ConfigManager


async def main():
    """
    Main example function showing different ways to use the trading system
    """
    
    # Example 1: Basic Trading System Usage
    print("=== Example 1: Basic Trading System ===")
    await example_basic_trading_system()
    
    print("\n=== Example 2: Strategy Configuration ===")
    await example_strategy_configuration()
    
    print("\n=== Example 3: Backtesting ===")
    await example_backtesting()
    
    print("\n=== Example 4: Risk Management ===")
    await example_risk_management()
    
    print("\nExamples completed!")


async def example_basic_trading_system():
    """Example 1: Basic trading system usage"""
    
    # Initialize trading system
    system = TradingSystem("config/config.example.yaml")
    
    # Initialize all components
    await system.initialize()
    
    # Check system status
    status = system.get_system_status()
    print(f"System Status: {status}")
    
    # You can start the system here
    # await system.start()
    
    # For demo purposes, just show the components
    print(f"Data Feed: {system.data_feed}")
    print(f"Strategies: {list(system.strategies.keys())}")
    print(f"Risk Manager: {system.risk_manager}")


async def example_strategy_configuration():
    """Example 2: Configure and test strategies"""
    
    # Load configuration
    config = ConfigManager("config/config.example.yaml")
    
    # Get strategy configurations
    strategies_config = config.get('strategies', {})
    
    print("Available Strategies:")
    for strategy_name, strategy_config in strategies_config.items():
        print(f"  - {strategy_name}: {strategy_config['symbols']}")
        print(f"    Parameters: {strategy_config['parameters']}")
        
    # Show available strategy types
    available_strategies = StrategyFactory.get_available_strategies()
    print(f"\nStrategy Types: {available_strategies}")


async def example_backtesting():
    """Example 3: Run backtest on a strategy"""
    
    # Create backtest configuration
    backtest_config = {
        'initial_capital': 100000,
        'transaction_cost': 0.001,
        'slippage': 0.0005
    }
    
    # Initialize backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Create a simple mean reversion strategy
    from src.strategies.mean_reversion import MeanReversionStrategy
    from src.execution.router import SmartOrderRouter
    from src.risk.manager import RiskManager
    
    # Mock components for backtest
    risk_manager = RiskManager({'initial_cash': 100000})
    order_router = SmartOrderRouter({'venues': ['backtest']}, risk_manager)
    
    strategy = MeanReversionStrategy(
        name='backtest_mean_reversion',
        symbols=['AAPL', 'GOOGL'],
        config={
            'lookback_period': 20,
            'z_score_threshold': 2.0,
            'position_size': 0.1,
            'max_positions': 5
        },
        order_router=order_router,
        risk_manager=risk_manager
    )
    
    # Run backtest (simplified example)
    print("Backtest configuration:")
    print(f"  Initial Capital: ${backtest_config['initial_capital']}")
    print(f"  Transaction Cost: {backtest_config['transaction_cost']:.2%}")
    print(f"  Strategy: Mean Reversion on {strategy.symbols}")
    
    # In a real scenario, you would run:
    # results = await engine.run_backtest(
    #     strategy=strategy,
    #     symbols=['AAPL', 'GOOGL'],
    #     start_date=datetime(2023, 1, 1),
    #     end_date=datetime(2023, 12, 31)
    # )


async def example_risk_management():
    """Example 4: Risk management features"""
    
    # Create risk manager with custom configuration
    risk_config = {
        'max_position_size': 50000,
        'max_portfolio_value': 500000,
        'max_drawdown_pct': 0.15,
        'var_confidence': 0.95,
        'initial_cash': 100000
    }
    
    risk_manager = RiskManager(risk_config)
    
    # Example risk checks
    from src.strategies.base import Signal
    
    # Create a test signal
    test_signal = Signal(
        symbol='AAPL',
        side='buy',
        quantity=100,
        signal_type='entry',
        confidence=1.0
    )
    
    # Check if signal passes risk management
    # result = await risk_manager.check_signal(test_signal)
    # print(f"Risk check result: {result}")
    
    print("Risk Management Configuration:")
    print(f"  Max Position Size: ${risk_config['max_position_size']:,}")
    print(f"  Max Portfolio Value: ${risk_config['max_portfolio_value']:,}")
    print(f"  Max Drawdown: {risk_config['max_drawdown_pct']:.1%}")
    print(f"  VaR Confidence: {risk_config['var_confidence']:.1%}")


# Additional utility functions
async def monitor_system_status(system: TradingSystem):
    """Monitor system status periodically"""
    while True:
        status = system.get_system_status()
        print(f"[{datetime.now()}] System Status: {status}")
        await asyncio.sleep(60)  # Check every minute


def print_strategy_performance(strategy_name: str, performance: Dict[str, Any]):
    """Print formatted strategy performance"""
    print(f"\n{strategy_name.upper()} STRATEGY PERFORMANCE")
    print("-" * 40)
    print(f"Total Return: {performance.get('total_return', 0):.2%}")
    print(f"Sharpe Ratio: {performance.get('sharpe_ratio', 0):.3f}")
    print(f"Max Drawdown: {performance.get('max_drawdown', 0):.2%}")
    print(f"Total Trades: {performance.get('total_trades', 0)}")
    print(f"Win Rate: {performance.get('win_rate', 0):.2%}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())