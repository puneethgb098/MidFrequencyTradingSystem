#!/usr/bin/env python3
"""
Backtest Example

Comprehensive example showing how to run backtests on different strategies.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.engine import BacktestEngine
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.arbitrage import ArbitrageStrategy
from src.execution.router import SmartOrderRouter
from src.risk.manager import RiskManager


async def run_mean_reversion_backtest():
    """Run backtest on mean reversion strategy"""
    
    print("=== Mean Reversion Strategy Backtest ===")
    
    # Configure backtest
    backtest_config = {
        'initial_capital': 100000,
        'transaction_cost': 0.001,
        'slippage': 0.0005
    }
    
    # Initialize components
    risk_manager = RiskManager({
        'initial_cash': backtest_config['initial_capital'],
        'max_position_size': backtest_config['initial_capital'] * 0.1,
        'max_drawdown_pct': 0.15
    })
    
    order_router = SmartOrderRouter({
        'venues': ['backtest'],
        'transaction_cost': backtest_config['transaction_cost'],
        'slippage': backtest_config['slippage']
    }, risk_manager)
    
    # Create strategy
    strategy = MeanReversionStrategy(
        name='mean_reversion_backtest',
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        config={
            'lookback_period': 20,
            'z_score_threshold': 2.0,
            'position_size': 0.1,
            'max_positions': 5,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.03
        },
        order_router=order_router,
        risk_manager=risk_manager
    )
    
    # Initialize backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Run backtest
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 6, 30)
    
    try:
        results = await engine.run_backtest(
            strategy=strategy,
            symbols=['AAPL', 'GOOGL', 'MSFT'],
            start_date=start_date,
            end_date=end_date,
            frequency='1H'  # Hourly data for better performance
        )
        
        print_backtest_results(results)
        
    except Exception as e:
        print(f"Error running backtest: {e}")


async def run_momentum_backtest():
    """Run backtest on momentum strategy"""
    
    print("\n=== Momentum Strategy Backtest ===")
    
    # Configure backtest
    backtest_config = {
        'initial_capital': 100000,
        'transaction_cost': 0.001,
        'slippage': 0.0005
    }
    
    # Initialize components
    risk_manager = RiskManager({
        'initial_cash': backtest_config['initial_capital'],
        'max_position_size': backtest_config['initial_capital'] * 0.1,
        'max_drawdown_pct': 0.15
    })
    
    order_router = SmartOrderRouter({
        'venues': ['backtest'],
        'transaction_cost': backtest_config['transaction_cost'],
        'slippage': backtest_config['slippage']
    }, risk_manager)
    
    # Create strategy
    strategy = MomentumStrategy(
        name='momentum_backtest',
        symbols=['AMZN', 'TSLA', 'META'],
        config={
            'lookback_period': 10,
            'momentum_threshold': 0.02,
            'position_size': 0.1,
            'max_positions': 3,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.05
        },
        order_router=order_router,
        risk_manager=risk_manager
    )
    
    # Initialize backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Run backtest
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 6, 30)
    
    try:
        results = await engine.run_backtest(
            strategy=strategy,
            symbols=['AMZN', 'TSLA', 'META'],
            start_date=start_date,
            end_date=end_date,
            frequency='1H'
        )
        
        print_backtest_results(results)
        
    except Exception as e:
        print(f"Error running backtest: {e}")


async def run_arbitrage_backtest():
    """Run backtest on arbitrage strategy"""
    
    print("\n=== Arbitrage Strategy Backtest ===")
    
    # Configure backtest
    backtest_config = {
        'initial_capital': 100000,
        'transaction_cost': 0.001,
        'slippage': 0.0005
    }
    
    # Initialize components
    risk_manager = RiskManager({
        'initial_cash': backtest_config['initial_capital'],
        'max_position_size': backtest_config['initial_cash'] * 0.05,  # Smaller positions for arbitrage
        'max_drawdown_pct': 0.10
    })
    
    order_router = SmartOrderRouter({
        'venues': ['backtest'],
        'transaction_cost': backtest_config['transaction_cost'],
        'slippage': backtest_config['slippage']
    }, risk_manager)
    
    # Create strategy
    strategy = ArbitrageStrategy(
        name='arbitrage_backtest',
        symbols=['NVDA', 'AMD', 'CRM', 'ADBE'],
        config={
            'lookback_period': 60,
            'z_score_threshold': 2.0,
            'position_size': 0.05,
            'max_pairs': 5,
            'min_correlation': 0.7
        },
        order_router=order_router,
        risk_manager=risk_manager
    )
    
    # Initialize backtest engine
    engine = BacktestEngine(backtest_config)
    
    # Run backtest
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 6, 30)
    
    try:
        results = await engine.run_backtest(
            strategy=strategy,
            symbols=['NVDA', 'AMD', 'CRM', 'ADBE'],
            start_date=start_date,
            end_date=end_date,
            frequency='1H'
        )
        
        print_backtest_results(results)
        
    except Exception as e:
        print(f"Error running backtest: {e}")


def print_backtest_results(results: Dict[str, Any]):
    """Print formatted backtest results"""
    
    if not results:
        print("No results to display")
        return
        
    # Summary
    summary = results.get('summary', {})
    print(f"\nBacktest Period: {summary.get('start_date', 'N/A')} to {summary.get('end_date', 'N/A')}")
    print(f"Initial Capital: ${summary.get('initial_capital', 0):,.2f}")
    print(f"Final Portfolio Value: ${summary.get('final_portfolio_value', 0):,.2f}")
    print(f"Total Return: {summary.get('total_return', 0):.2%}")
    print(f"Total Trades: {summary.get('total_trades', 0)}")
    print(f"Winning Trades: {summary.get('winning_trades', 0)}")
    print(f"Losing Trades: {summary.get('losing_trades', 0)}")
    print(f"Max Drawdown: {summary.get('max_drawdown', 0):.2%}")
    print(f"Sharpe Ratio: {summary.get('sharpe_ratio', 0):.3f}")
    
    # Performance metrics
    performance = results.get('performance', {})
    if performance:
        print(f"\nDetailed Performance Metrics:")
        print(f"  Annualized Return: {performance.get('annualized_return', 0):.2%}")
        print(f"  Annualized Volatility: {performance.get('annualized_volatility', 0):.2%}")
        print(f"  VaR (95%): {performance.get('var_95', 0):.2%}")
        print(f"  VaR (99%): {performance.get('var_99', 0):.2%}")
        print(f"  Calmar Ratio: {performance.get('calmar_ratio', 0):.3f}")
        print(f"  Sortino Ratio: {performance.get('sortino_ratio', 0):.3f}")
        print(f"  Skewness: {performance.get('skewness', 0):.3f}")
        print(f"  Kurtosis: {performance.get('kurtosis', 0):.3f}")
        
    # Recent trades
    trades = results.get('trades', [])
    if trades:
        print(f"\nRecent Trades (last 5):")
        for i, trade in enumerate(trades[-5:]):
            print(f"  {i+1}. {trade.get('symbol', 'N/A')} - "
                  f"{trade.get('side', 'N/A')} - "
                  f"PnL: ${trade.get('pnl', 0):.2f}")


async def compare_strategies():
    """Compare performance of different strategies"""
    
    print("\n" + "="*60)
    print("STRATEGY COMPARISON")
    print("="*60)
    
    # This would run all backtests and compare results
    # For now, just run individual examples
    await run_mean_reversion_backtest()
    await run_momentum_backtest()
    await run_arbitrage_backtest()
    
    print("\n" + "="*60)
    print("Strategy comparison completed")
    print("="*60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(compare_strategies())