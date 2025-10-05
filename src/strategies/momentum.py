"""
Momentum Strategy

Implements a momentum-based trading strategy using technical indicators.
"""

import numpy as np
from typing import Dict, List
from datetime import datetime

from .base import BaseStrategy, Signal
from data.feeds import MarketData


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy
    
    This strategy identifies assets with strong price momentum and
    takes positions in the direction of the trend.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Strategy parameters
        self.lookback_period = self.config.get('lookback_period', 10)
        self.momentum_threshold = self.config.get('momentum_threshold', 0.02)
        self.position_size = self.config.get('position_size', 0.1)
        self.max_positions = self.config.get('max_positions', 3)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.03)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.05)
        
        # Data storage
        self.price_history = {symbol: [] for symbol in self.symbols}
        self.momentum_scores = {}
        
    async def on_market_data(self, market_data: Dict[str, MarketData]):
        """
        Process new market data and generate signals
        """
        if not self.is_running:
            return
            
        for symbol, data in market_data.items():
            if symbol not in self.symbols:
                continue
                
            # Update price history
            self.price_history[symbol].append(data.last)
            
            # Keep only recent data
            if len(self.price_history[symbol]) > self.lookback_period * 2:
                self.price_history[symbol] = self.price_history[symbol][-self.lookback_period * 2:]
                
            # Generate signals if we have enough data
            if len(self.price_history[symbol]) >= self.lookback_period:
                signals = self.generate_signals(symbol, data)
                
                for signal in signals:
                    self.add_signal(signal)
                    await self.execute_signal(signal)
                    
    def generate_signals(self, symbol: str, current_data: MarketData) -> List[Signal]:
        """
        Generate momentum-based signals
        """
        signals = []
        
        # Get price series
        prices = np.array(self.price_history[symbol])
        
        # Calculate momentum score
        momentum_score = self._calculate_momentum(prices)
        self.momentum_scores[symbol] = momentum_score
        
        # Current position
        current_position = self.positions.get(symbol, 0)
        
        # Entry signals
        if current_position == 0 and len([p for p in self.positions.values() if p != 0]) < self.max_positions:
            
            # Strong upward momentum - buy signal
            if momentum_score > self.momentum_threshold:
                signal = Signal(
                    symbol=symbol,
                    side='buy',
                    quantity=self._calculate_position_size(symbol, current_data),
                    signal_type='entry',
                    confidence=min(momentum_score / self.momentum_threshold, 2.0),
                    metadata={
                        'strategy': 'momentum',
                        'momentum_score': momentum_score,
                        'reason': 'strong_upward_momentum'
                    }
                )
                signals.append(signal)
                
            # Strong downward momentum - sell signal
            elif momentum_score < -self.momentum_threshold:
                signal = Signal(
                    symbol=symbol,
                    side='sell',
                    quantity=self._calculate_position_size(symbol, current_data),
                    signal_type='entry',
                    confidence=min(abs(momentum_score) / self.momentum_threshold, 2.0),
                    metadata={
                        'strategy': 'momentum',
                        'momentum_score': momentum_score,
                        'reason': 'strong_downward_momentum'
                    }
                )
                signals.append(signal)
                
        # Exit signals for existing positions
        else:
            entry_price = self._get_entry_price(symbol)
            pnl_pct = (current_data.last - entry_price) / entry_price if entry_price else 0
            
            # Momentum reversal - exit position
            if (current_position > 0 and momentum_score < -0.005) or \
               (current_position < 0 and momentum_score > 0.005):
                signal = Signal(
                    symbol=symbol,
                    side='sell' if current_position > 0 else 'buy',
                    quantity=abs(current_position),
                    signal_type='exit',
                    confidence=0.9,
                    metadata={
                        'strategy': 'momentum',
                        'momentum_score': momentum_score,
                        'reason': 'momentum_reversal'
                    }
                )
                signals.append(signal)
                
            # Take profit
            elif (current_position > 0 and pnl_pct > self.take_profit_pct) or \
                 (current_position < 0 and pnl_pct < -self.take_profit_pct):
                signal = Signal(
                    symbol=symbol,
                    side='sell' if current_position > 0 else 'buy',
                    quantity=abs(current_position),
                    signal_type='exit',
                    confidence=1.0,
                    metadata={
                        'strategy': 'momentum',
                        'reason': 'take_profit',
                        'pnl_pct': pnl_pct
                    }
                )
                signals.append(signal)
                
            # Stop loss
            elif (current_position > 0 and pnl_pct < -self.stop_loss_pct) or \
                 (current_position < 0 and pnl_pct > self.stop_loss_pct):
                signal = Signal(
                    symbol=symbol,
                    side='sell' if current_position > 0 else 'buy',
                    quantity=abs(current_position),
                    signal_type='exit',
                    confidence=1.0,
                    metadata={
                        'strategy': 'momentum',
                        'reason': 'stop_loss',
                        'pnl_pct': pnl_pct
                    }
                )
                signals.append(signal)
                
        return signals
        
    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """
        Calculate momentum score
        
        Returns:
            Momentum score (positive for upward, negative for downward)
        """
        if len(prices) < self.lookback_period + 1:
            return 0.0
            
        # Calculate returns over lookback period
        current_price = prices[-1]
        past_price = prices[-self.lookback_period - 1]
        
        # Momentum as percentage change
        momentum = (current_price - past_price) / past_price
        
        # Apply smoothing (optional)
        if len(prices) >= self.lookback_period * 2:
            # Use exponential moving average of momentum
            recent_prices = prices[-self.lookback_period:]
            returns = np.diff(recent_prices) / recent_prices[:-1]
            
            if len(returns) > 0:
                # Simple average of recent returns
                avg_return = np.mean(returns)
                momentum = 0.7 * momentum + 0.3 * avg_return * self.lookback_period
                
        return momentum
        
    def _calculate_position_size(self, symbol: str, market_data: MarketData) -> float:
        """Calculate position size based on momentum strength"""
        base_size = self.position_size
        
        # Adjust size based on momentum strength
        momentum = self.momentum_scores.get(symbol, 0)
        momentum_factor = min(abs(momentum) / self.momentum_threshold, 2.0)
        
        return base_size * momentum_factor
        
    def _get_entry_price(self, symbol: str) -> float:
        """Get the entry price for a position"""
        # In a real implementation, this would track entry prices
        # For now, return the current price as a placeholder
        if symbol in self.price_history and len(self.price_history[symbol]) > 0:
            return self.price_history[symbol][-1]
        return market_data.last if 'market_data' in locals() else 100.0
        
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status with additional metrics"""
        base_status = super().get_status()
        base_status.update({
            'momentum_scores': self.momentum_scores,
            'price_history_lengths': {
                symbol: len(history) 
                for symbol, history in self.price_history.items()
            }
        })
        return base_status