"""
Performance Metrics Module

Calculates comprehensive performance metrics for backtesting results.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from scipy import stats
import logging


class PerformanceMetrics:
    """
    Performance Metrics Calculator
    
    Provides comprehensive performance analysis including:
    - Risk-adjusted returns
    - Drawdown analysis
    - Statistical significance tests
    - Benchmark comparisons
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_all_metrics(self, 
                            returns: List[float],
                            trades: List[Dict[str, Any]],
                            initial_capital: float,
                            benchmark_returns: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Calculate all performance metrics
        
        Args:
            returns: List of daily returns
            trades: List of trade data
            initial_capital: Initial capital amount
            benchmark_returns: Optional benchmark returns for comparison
            
        Returns:
            Dictionary with all performance metrics
        """
        if not returns:
            return {}
            
        returns_array = np.array(returns)
        
        metrics = {
            'basic_metrics': self._calculate_basic_metrics(returns_array, initial_capital),
            'risk_metrics': self._calculate_risk_metrics(returns_array),
            'trade_metrics': self._calculate_trade_metrics(trades),
            'statistical_tests': self._calculate_statistical_tests(returns_array),
            'benchmark_metrics': {}
        }
        
        if benchmark_returns:
            metrics['benchmark_metrics'] = self._calculate_benchmark_metrics(
                returns_array, np.array(benchmark_returns)
            )
            
        return metrics
        
    def _calculate_basic_metrics(self, returns: np.ndarray, initial_capital: float) -> Dict[str, float]:
        """Calculate basic performance metrics"""
        total_return = np.prod(1 + returns) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
        annualized_volatility = np.std(returns) * np.sqrt(252)
        
        # Calculate final portfolio value
        final_value = initial_capital * (1 + total_return)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': (annualized_return - 0.02) / annualized_volatility if annualized_volatility > 0 else 0,
            'final_portfolio_value': final_value,
            'profit_loss': final_value - initial_capital,
            'profit_loss_percentage': total_return
        }
        
    def _calculate_risk_metrics(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate risk-related metrics"""
        # VaR calculations
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Expected Shortfall (Conditional VaR)
        es_95 = np.mean(returns[returns <= var_95])
        es_99 = np.mean(returns[returns <= var_99])
        
        # Maximum Drawdown
        cumulative_returns = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # Calmar Ratio
        annualized_return = (1 + np.prod(1 + returns) - 1) ** (252 / len(returns)) - 1
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2)) if len(downside_returns) > 0 else 0
        sortino_ratio = (annualized_return - 0.02) / (downside_deviation * np.sqrt(252)) if downside_deviation > 0 else float('inf')
        
        # Skewness and Kurtosis
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall_95': es_95,
            'expected_shortfall_99': es_99,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'downside_deviation': downside_deviation
        }
        
    def _calculate_trade_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate trade-related metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'average_win': 0,
                'average_loss': 0,
                'profit_factor': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'average_trade_duration': 0
            }
            
        # Calculate P&L for each trade
        trade_pnl = []
        winning_trades = []
        losing_trades = []
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            trade_pnl.append(pnl)
            
            if pnl > 0:
                winning_trades.append(pnl)
            else:
                losing_trades.append(pnl)
                
        total_trades = len(trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        average_win = np.mean(winning_trades) if winning_trades else 0
        average_loss = np.mean(losing_trades) if losing_trades else 0
        
        profit_factor = (sum(winning_trades) / abs(sum(losing_trades))) if losing_trades else float('inf')
        
        # Trade duration
        durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # hours
                durations.append(duration)
                
        average_duration = np.mean(durations) if durations else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'largest_win': max(winning_trades) if winning_trades else 0,
            'largest_loss': min(losing_trades) if losing_trades else 0,
            'average_trade_duration': average_duration
        }
        
    def _calculate_statistical_tests(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate statistical significance tests"""
        # Jarque-Bera test for normality
        jb_stat, jb_pvalue = stats.jarque_bera(returns)
        
        # Ljung-Box test for autocorrelation (simplified)
        # In practice, use statsmodels for proper implementation
        
        # One-sample t-test for mean return
        t_stat, t_pvalue = stats.ttest_1samp(returns, 0)
        
        return {
            'jarque_bera_statistic': jb_stat,
            'jarque_bera_pvalue': jb_pvalue,
            'returns_normal': jb_pvalue > 0.05,
            't_statistic': t_stat,
            't_pvalue': t_pvalue,
            'mean_return_significant': t_pvalue < 0.05
        }
        
    def _calculate_benchmark_metrics(self, strategy_returns: np.ndarray, benchmark_returns: np.ndarray) -> Dict[str, float]:
        """Calculate metrics relative to benchmark"""
        # Align returns
        min_length = min(len(strategy_returns), len(benchmark_returns))
        strategy_returns = strategy_returns[:min_length]
        benchmark_returns = benchmark_returns[:min_length]
        
        # Beta calculation
        covariance = np.cov(strategy_returns, benchmark_returns)[0, 1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
        
        # Alpha calculation (CAPM)
        strategy_mean = np.mean(strategy_returns)
        benchmark_mean = np.mean(benchmark_returns)
        alpha = strategy_mean - beta * benchmark_mean
        
        # Tracking error
        excess_returns = strategy_returns - benchmark_returns
        tracking_error = np.std(excess_returns) * np.sqrt(252)
        
        # Information ratio
        information_ratio = (np.mean(excess_returns) * 252) / tracking_error if tracking_error > 0 else 0
        
        # Correlation
        correlation = np.corrcoef(strategy_returns, benchmark_returns)[0, 1]
        
        # R-squared
        r_squared = correlation ** 2
        
        return {
            'beta': beta,
            'alpha': alpha,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'correlation': correlation,
            'r_squared': r_squared
        }
        
    def calculate_monthly_returns(self, returns: List[float], dates: List[datetime]) -> pd.DataFrame:
        """
        Calculate monthly returns
        
        Args:
            returns: List of daily returns
            dates: List of corresponding dates
            
        Returns:
            DataFrame with monthly returns
        """
        df = pd.DataFrame({
            'date': dates,
            'return': returns
        })
        
        df.set_index('date', inplace=True)
        
        # Calculate monthly returns
        monthly_returns = df['return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        return monthly_returns.to_frame('monthly_return')
        
    def calculate_rolling_metrics(self, returns: List[float], window: int = 30) -> Dict[str, List[float]]:
        """
        Calculate rolling performance metrics
        
        Args:
            returns: List of returns
            window: Rolling window size
            
        Returns:
            Dictionary of rolling metrics
        """
        returns_array = np.array(returns)
        
        rolling_metrics = {
            'rolling_return': [],
            'rolling_volatility': [],
            'rolling_sharpe': []
        }
        
        for i in range(window, len(returns_array)):
            window_returns = returns_array[i-window:i]
            
            # Rolling return
            rolling_return = np.prod(1 + window_returns) - 1
            rolling_metrics['rolling_return'].append(rolling_return)
            
            # Rolling volatility
            rolling_vol = np.std(window_returns) * np.sqrt(252)
            rolling_metrics['rolling_volatility'].append(rolling_vol)
            
            # Rolling Sharpe ratio
            rolling_sharpe = (np.mean(window_returns) * 252 - 0.02) / rolling_vol if rolling_vol > 0 else 0
            rolling_metrics['rolling_sharpe'].append(rolling_sharpe)
            
        return rolling_metrics
        
    def generate_performance_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate a formatted performance report
        
        Args:
            metrics: Performance metrics dictionary
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("TRADING SYSTEM PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Basic Metrics
        basic = metrics.get('basic_metrics', {})
        report.append("BASIC METRICS:")
        report.append(f"Total Return: {basic.get('total_return', 0):.2%}")
        report.append(f"Annualized Return: {basic.get('annualized_return', 0):.2%}")
        report.append(f"Annualized Volatility: {basic.get('annualized_volatility', 0):.2%}")
        report.append(f"Sharpe Ratio: {basic.get('sharpe_ratio', 0):.3f}")
        report.append(f"Final Portfolio Value: ${basic.get('final_portfolio_value', 0):,.2f}")
        report.append("")
        
        # Risk Metrics
        risk = metrics.get('risk_metrics', {})
        report.append("RISK METRICS:")
        report.append(f"Maximum Drawdown: {risk.get('max_drawdown', 0):.2%}")
        report.append(f"VaR (95%): {risk.get('var_95', 0):.2%}")
        report.append(f"VaR (99%): {risk.get('var_99', 0):.2%}")
        report.append(f"Expected Shortfall (95%): {risk.get('expected_shortfall_95', 0):.2%}")
        report.append(f"Calmar Ratio: {risk.get('calmar_ratio', 0):.3f}")
        report.append(f"Sortino Ratio: {risk.get('sortino_ratio', 0):.3f}")
        report.append("")
        
        # Trade Metrics
        trades = metrics.get('trade_metrics', {})
        report.append("TRADE METRICS:")
        report.append(f"Total Trades: {trades.get('total_trades', 0)}")
        report.append(f"Winning Trades: {trades.get('winning_trades', 0)}")
        report.append(f"Losing Trades: {trades.get('losing_trades', 0)}")
        report.append(f"Win Rate: {trades.get('win_rate', 0):.2%}")
        report.append(f"Profit Factor: {trades.get('profit_factor', 0):.3f}")
        report.append("")
        
        # Benchmark Metrics
        benchmark = metrics.get('benchmark_metrics', {})
        if benchmark:
            report.append("BENCHMARK METRICS:")
            report.append(f"Beta: {benchmark.get('beta', 0):.3f}")
            report.append(f"Alpha: {benchmark.get('alpha', 0):.3f}")
            report.append(f"Information Ratio: {benchmark.get('information_ratio', 0):.3f}")
            report.append(f"Correlation: {benchmark.get('correlation', 0):.3f}")
            report.append("")
            
        report.append("=" * 60)
        
        return "\n".join(report)