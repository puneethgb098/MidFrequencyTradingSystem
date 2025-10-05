"""
Backtesting Framework

Provides comprehensive backtesting capabilities for strategy validation.
"""

from .engine import BacktestEngine
from .data import BacktestData
from .metrics import PerformanceMetrics

__all__ = ['BacktestEngine', 'BacktestData', 'PerformanceMetrics']