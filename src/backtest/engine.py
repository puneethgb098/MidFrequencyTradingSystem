"""
Backtest Engine

Comprehensive backtesting framework for strategy validation and optimization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from strategies.base import Signal
from data.feeds import MarketData
from risk.manager import RiskManager
from execution.router import SmartOrderRouter
from .data import BacktestData
from .metrics import PerformanceMetrics


class BacktestEngine:
    """
    Backtest Engine
    
    Provides comprehensive backtesting capabilities including:
    - Historical data simulation
    - Strategy execution simulation
    - Performance metrics calculation
    - Risk analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Backtest parameters
        self.initial_capital = config.get('initial_capital', 1000000)
        self.transaction_cost = config.get('transaction_cost', 0.001)  # 0.1%
        self.slippage = config.get('slippage', 0.0005)  # 0.05%
        
        # Data and components
        self.data_source = None
        self.strategy = None
        self.risk_manager = None
        self.order_router = None
        
        # Backtest state
        self.current_time = None
        self.portfolio_value = self.initial_capital
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_returns = []
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        
    async def run_backtest(self, 
                          strategy,
                          symbols: List[str],
                          start_date: datetime,
                          end_date: datetime,
                          frequency: str = '1min') -> Dict[str, Any]:
        """
        Run a complete backtest
        
        Args:
            strategy: Trading strategy to test
            symbols: List of trading symbols
            start_date: Backtest start date
            end_date: Backtest end date
            frequency: Data frequency ('1min', '5min', '1H', '1D')
            
        Returns:
            Backtest results dictionary
        """
        self.logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Initialize components
        await self._initialize_components(strategy, symbols)
        
        # Load historical data
        self.data_source = BacktestData(symbols, start_date, end_date, frequency)
        await self.data_source.load_data()
        
        # Run backtest simulation
        results = await self._simulate_trading()
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics()
        
        self.logger.info("Backtest completed")
        
        return {
            'summary': results,
            'performance': performance,
            'trades': self.trades,
            'daily_returns': self.daily_returns
        }
        
    async def _initialize_components(self, strategy, symbols: List[str]):
        """Initialize backtest components"""
        # Initialize risk manager
        risk_config = {
            'initial_cash': self.initial_capital,
            'max_position_size': self.initial_capital * 0.1,  # 10% max position
            'max_drawdown_pct': 0.20,
            'transaction_cost': self.transaction_cost
        }
        self.risk_manager = RiskManager(risk_config)
        
        # Initialize order router
        execution_config = {
            'venues': ['backtest'],
            'transaction_cost': self.transaction_cost,
            'slippage': self.slippage
        }
        self.order_router = SmartOrderRouter(execution_config, self.risk_manager)
        
        # Set strategy components
        strategy.order_router = self.order_router
        strategy.risk_manager = self.risk_manager
        
        self.strategy = strategy
        
    async def _simulate_trading(self) -> Dict[str, Any]:
        """Simulate trading over historical data"""
        self.logger.info("Starting trading simulation")
        
        # Get all market data
        market_data = self.data_source.get_all_data()
        
        # Initialize daily tracking
        current_date = None
        daily_pnl = 0.0
        
        for timestamp, data in market_data.iterrows():
            self.current_time = timestamp
            
            # Handle new day
            if current_date != timestamp.date():
                if current_date is not None:
                    self.daily_returns.append(daily_pnl / self.initial_capital)
                current_date = timestamp.date()
                daily_pnl = 0.0
                
            # Create market data object
            market_data_obj = self._create_market_data(timestamp, data)
            
            # Update market prices
            self._update_market_prices(market_data_obj)
            
            # Process strategy
            await self.strategy.on_market_data(market_data_obj)
            
            # Process any generated signals
            await self._process_signals()
            
            # Update P&L
            daily_pnl += self._calculate_pnl_change()
            
        # Final daily return
        if current_date is not None:
            self.daily_returns.append(daily_pnl / self.initial_capital)
            
        # Generate summary
        return self._generate_summary()
        
    def _create_market_data(self, timestamp: datetime, data: pd.Series) -> Dict[str, MarketData]:
        """Create MarketData objects from backtest data"""
        market_data = {}
        
        for symbol in self.data_source.symbols:
            if f"{symbol}_close" in data:
                market_data[symbol] = MarketData(
                    symbol=symbol,
                    timestamp=timestamp,
                    bid=data.get(f"{symbol}_close", 0) * 0.999,  # Simulate spread
                    ask=data.get(f"{symbol}_close", 0) * 1.001,
                    last=data.get(f"{symbol}_close", 0),
                    volume=int(data.get(f"{symbol}_volume", 0))
                )
                
        return market_data
        
    def _update_market_prices(self, market_data: Dict[str, MarketData]):
        """Update current market prices"""
        for symbol, data in market_data.items():
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(data.last)
            
            # Keep only recent history
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
                
    async def _process_signals(self):
        """Process any signals generated by the strategy"""
        # This would integrate with the strategy's signal generation
        # For now, we'll simulate signal processing
        pass
        
    def _calculate_pnl_change(self) -> float:
        """Calculate P&L change from positions"""
        total_pnl = 0.0
        
        for symbol, position in self.positions.items():
            if position != 0 and symbol in self.price_history:
                current_price = self.price_history[symbol][-1]
                
                # Calculate unrealized P&L
                # This is simplified - in production, track entry prices
                if position > 0:  # Long
                    pnl = position * current_price
                else:  # Short
                    pnl = abs(position) * current_price
                    
                total_pnl += pnl
                
        return total_pnl
        
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate backtest summary"""
        total_return = (self.portfolio_value - self.initial_capital) / self.initial_capital
        
        return {
            'start_date': self.data_source.start_date,
            'end_date': self.data_source.end_date,
            'initial_capital': self.initial_capital,
            'final_portfolio_value': self.portfolio_value,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in self.trades if t.get('pnl', 0) < 0]),
            'max_drawdown': self._calculate_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe_ratio()
        }
        
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        if not self.daily_returns:
            return {}
            
        returns = np.array(self.daily_returns)
        
        metrics = {
            'total_return': (self.portfolio_value - self.initial_capital) / self.initial_capital,
            'annualized_return': np.mean(returns) * 252,  # 252 trading days
            'annualized_volatility': np.std(returns) * np.sqrt(252),
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'max_drawdown': self._calculate_max_drawdown(),
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1),
            'skewness': self._calculate_skewness(returns),
            'kurtosis': self._calculate_kurtosis(returns),
            'calmar_ratio': self._calculate_calmar_ratio(),
            'sortino_ratio': self._calculate_sortino_ratio(returns)
        }
        
        return metrics
        
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        if not self.daily_returns or np.std(self.daily_returns) == 0:
            return 0.0
            
        returns = np.array(self.daily_returns)
        excess_returns = returns - 0.02/252  # 2% risk-free rate
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.daily_returns:
            return 0.0
            
        cumulative_returns = np.cumsum(self.daily_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (peak - cumulative_returns) / (1 + peak)
        
        return np.max(drawdown)
        
    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness of returns"""
        if len(returns) < 3:
            return 0.0
        return ((np.mean((returns - np.mean(returns))**3)) / 
                (np.mean((returns - np.mean(returns))**2)**1.5))
        
    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate kurtosis of returns"""
        if len(returns) < 4:
            return 0.0
        return ((np.mean((returns - np.mean(returns))**4)) / 
                (np.mean((returns - np.mean(returns))**2)**2))
        
    def _calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio"""
        total_return = (self.portfolio_value - self.initial_capital) / self.initial_capital
        max_drawdown = self._calculate_max_drawdown()
        
        if max_drawdown == 0:
            return float('inf')
        return total_return / max_drawdown
        
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        if len(returns) == 0:
            return 0.0
            
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')
            
        downside_deviation = np.sqrt(np.mean(downside_returns**2))
        excess_return = np.mean(returns) - 0.02/252
        
        return excess_return / downside_deviation * np.sqrt(252)
        
    def get_results(self) -> Dict[str, Any]:
        """Get complete backtest results"""
        return {
            'summary': self._generate_summary(),
            'performance': self._calculate_performance_metrics(),
            'trades': self.trades,
            'daily_returns': self.daily_returns,
            'positions': self.positions
        }