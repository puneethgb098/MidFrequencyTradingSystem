"""
Strategy Factory

Creates strategy instances based on configuration.
"""

from typing import Dict, Any

from .base import BaseStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy
from .arbitrage import ArbitrageStrategy


class StrategyFactory:
    """
    Factory class for creating trading strategies
    """
    
    _strategies = {
        'mean_reversion': MeanReversionStrategy,
        'momentum': MomentumStrategy,
        'arbitrage': ArbitrageStrategy,
    }
    
    @classmethod
    def create_strategy(cls,
                       strategy_name: str,
                       config: Dict[str, Any],
                       order_router,
                       risk_manager) -> BaseStrategy:
        """
        Create a strategy instance
        
        Args:
            strategy_name: Name of the strategy type
            config: Strategy configuration
            order_router: Order routing component
            risk_manager: Risk management component
            
        Returns:
            Strategy instance
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_name}")
            
        strategy_class = cls._strategies[strategy_name]
        
        return strategy_class(
            name=strategy_name,
            symbols=config.get('symbols', []),
            config=config.get('parameters', {}),
            order_router=order_router,
            risk_manager=risk_manager
        )
        
    @classmethod
    def register_strategy(cls, name: str, strategy_class):
        """Register a new strategy type"""
        cls._strategies[name] = strategy_class
        
    @classmethod
    def get_available_strategies(cls) -> list:
        """Get list of available strategy types"""
        return list(cls._strategies.keys())