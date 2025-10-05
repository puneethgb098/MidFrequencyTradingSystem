"""
Base Strategy Module

Defines the abstract base class for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from data.feeds import MarketData
from execution.router import SmartOrderRouter
from risk.manager import RiskManager


class Signal:
    """Trading signal structure"""
    
    def __init__(self, 
                 symbol: str,
                 side: str,  # 'buy' or 'sell'
                 quantity: float,
                 signal_type: str,  # 'entry', 'exit', 'adjust'
                 confidence: float = 1.0,
                 timestamp: datetime = None,
                 metadata: Dict[str, Any] = None):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.signal_type = signal_type
        self.confidence = confidence
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies
    """
    
    def __init__(self,
                 name: str,
                 symbols: List[str],
                 config: Dict[str, Any],
                 order_router: SmartOrderRouter,
                 risk_manager: RiskManager):
        self.name = name
        self.symbols = symbols
        self.config = config
        self.order_router = order_router
        self.risk_manager = risk_manager
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Strategy state
        self.is_running = False
        self.positions = {}  # Current positions
        self.signals = []    # Recent signals
        self.performance = {}  # Strategy performance metrics
        
        # Data storage
        self.market_data = {}
        self.historical_data = {}
        
    @abstractmethod
    async def on_market_data(self, market_data: Dict[str, MarketData]):
        """
        Process new market data and generate signals
        
        Args:
            market_data: Dictionary of symbol -> MarketData
        """
        pass
        
    @abstractmethod
    def generate_signals(self, data: Dict[str, Any]) -> List[Signal]:
        """
        Generate trading signals based on strategy logic
        
        Args:
            data: Market data and indicators
            
        Returns:
            List of trading signals
        """
        pass
        
    async def execute_signal(self, signal: Signal):
        """
        Execute a trading signal
        
        Args:
            signal: Trading signal to execute
        """
        try:
            # Risk check
            if not await self.risk_manager.check_signal(signal):
                self.logger.warning(f"Signal failed risk check: {signal.to_dict()}")
                return
                
            # Route order
            order_id = await self.order_router.submit_order(
                symbol=signal.symbol,
                side=signal.side,
                quantity=signal.quantity,
                order_type='market',  # Default to market orders
                strategy=self.name,
                metadata=signal.metadata
            )
            
            self.logger.info(f"Executed signal: {signal.to_dict()}, Order ID: {order_id}")
            
            # Update positions
            await self._update_positions(signal)
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            
    async def start(self):
        """Start the strategy"""
        self.logger.info(f"Starting strategy: {self.name}")
        self.is_running = True
        
        # Initialize strategy
        await self._initialize()
        
    async def stop(self):
        """Stop the strategy"""
        self.logger.info(f"Stopping strategy: {self.name}")
        self.is_running = False
        
        # Close all positions
        await self._close_all_positions()
        
    async def _initialize(self):
        """Initialize strategy (override in subclasses)"""
        pass
        
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol, position in self.positions.items():
            if position != 0:
                signal = Signal(
                    symbol=symbol,
                    side='sell' if position > 0 else 'buy',
                    quantity=abs(position),
                    signal_type='exit',
                    metadata={'reason': 'strategy_shutdown'}
                )
                await self.execute_signal(signal)
                
    async def _update_positions(self, signal: Signal):
        """Update position tracking"""
        symbol = signal.symbol
        current_pos = self.positions.get(symbol, 0)
        
        if signal.side == 'buy':
            self.positions[symbol] = current_pos + signal.quantity
        else:
            self.positions[symbol] = current_pos - signal.quantity
            
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status"""
        return {
            'name': self.name,
            'is_running': self.is_running,
            'symbols': self.symbols,
            'positions': self.positions,
            'recent_signals': [s.to_dict() for s in self.signals[-10:]],
            'config': self.config
        }
        
    def add_signal(self, signal: Signal):
        """Add a signal to the recent signals list"""
        self.signals.append(signal)
        # Keep only last 100 signals
        if len(self.signals) > 100:
            self.signals = self.signals[-100:]