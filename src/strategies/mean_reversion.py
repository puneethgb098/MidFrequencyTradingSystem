"""
Mean Reversion Strategy

Implements a statistical mean reversion trading strategy with dynamic position sizing.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta

from .base import BaseStrategy, Signal
from data.feeds import MarketData
from indicators.technical import SMA, ZScore, BollingerBands


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy
    
    This strategy identifies when prices deviate significantly from their
    historical mean and takes contrarian positions expecting reversion.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Strategy parameters
        self.lookback_period = self.config.get('lookback_period', 20)
        self.z_score_threshold = self.config.get('z_score_threshold', 2.0)
        self.position_size = self.config.get('position_size', 0.1)
        self.max_positions = self.config.get('max_positions', 5)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.05)
        self.take_profit_pct = self.config.get('take_profit_pct', 0.03)
        
        # Technical indicators
        self.sma = SMA(period=self.lookback_period)
        self.zscore = ZScore(period=self.lookback_period)
        self.bbands = BollingerBands(period=self.lookback_period, std_dev=2.0)
        
        # Data storage
        self.price_history = {symbol: [] for symbol in self.symbols}
        self.indicators_cache = {}
        
    async def _initialize(self):
        """Initialize strategy with historical data"""
        self.logger.info("Initializing Mean Reversion Strategy")
        
        # Load historical data for indicator calculation
        for symbol in self.symbols:
            # In a real implementation, this would fetch from a data provider
            self.price_history[symbol] = []
            
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
        Generate mean reversion signals
        """
        signals = []
        
        # Get price series
        prices = np.array(self.price_history[symbol])
        
        # Calculate indicators
        sma_value = self.sma.calculate(prices)
        zscore_value = self.zscore.calculate(prices)
        bb_upper, bb_lower = self.bbands.calculate(prices)
        
        # Store indicators for monitoring
        self.indicators_cache[symbol] = {
            'sma': sma_value,
            'zscore': zscore_value,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'current_price': current_data.last
        }
        
        # Current position
        current_position = self.positions.get(symbol, 0)
        
        # Entry signals
        if current_position == 0 and len([p for p in self.positions.values() if p != 0]) < self.max_positions:
            
            # Oversold condition - buy signal
            if zscore_value < -self.z_score_threshold:
                signal = Signal(
                    symbol=symbol,
                    side='buy',
                    quantity=self._calculate_position_size(symbol, current_data),
                    signal_type='entry',
                    confidence=min(abs(zscore_value) / self.z_score_threshold, 2.0),
                    metadata={
                        'strategy': 'mean_reversion',
                        'zscore': zscore_value,
                        'sma': sma_value,
                        'reason': 'oversold'
                    }
                )
                signals.append(signal)
                
            # Overbought condition - sell signal
            elif zscore_value > self.z_score_threshold:
                signal = Signal(
                    symbol=symbol,
                    side='sell',
                    quantity=self._calculate_position_size(symbol, current_data),
                    signal_type='entry',
                    confidence=min(abs(zscore_value) / self.z_score_threshold, 2.0),
                    metadata={
                        'strategy': 'mean_reversion',
                        'zscore': zscore_value,
                        'sma': sma_value,
                        'reason': 'overbought'
                    }
                )
                signals.append(signal)
                
        # Exit signals for existing positions
        else:
            entry_price = self._get_entry_price(symbol)
            pnl_pct = (current_data.last - entry_price) / entry_price if entry_price else 0
            
            # Take profit
            if (current_position > 0 and pnl_pct > self.take_profit_pct) or \
               (current_position < 0 and pnl_pct < -self.take_profit_pct):
                signal = Signal(
                    symbol=symbol,
                    side='sell' if current_position > 0 else 'buy',
                    quantity=abs(current_position),
                    signal_type='exit',
                    confidence=1.0,
                    metadata={
                        'strategy': 'mean_reversion',
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
                        'strategy': 'mean_reversion',
                        'reason': 'stop_loss',
                        'pnl_pct': pnl_pct
                    }
                )
                signals.append(signal)
                
            # Mean reversion - exit when price returns to mean
            elif abs(zscore_value) < 0.5:  # Price has reverted to mean
                signal = Signal(
                    symbol=symbol,
                    side='sell' if current_position > 0 else 'buy',
                    quantity=abs(current_position),
                    signal_type='exit',
                    confidence=0.8,
                    metadata={
                        'strategy': 'mean_reversion',
                        'reason': 'reversion_to_mean',
                        'zscore': zscore_value
                    }
                )
                signals.append(signal)
                
        return signals
        
    def _calculate_position_size(self, symbol: str, market_data: MarketData) -> float:
        """
        Calculate position size based on volatility and risk parameters
        """
        # Basic position sizing - in production, this would be more sophisticated
        base_size = self.position_size
        
        # Adjust for volatility (simplified)
        if symbol in self.price_history and len(self.price_history[symbol]) > 10:
            prices = np.array(self.price_history[symbol][-10:])
            volatility = np.std(np.diff(np.log(prices)))
            
            # Reduce size for high volatility
            if volatility > 0.02:  # 2% daily volatility
                base_size *= 0.5
                
        return base_size
        
    def _get_entry_price(self, symbol: str) -> float:
        """Get the entry price for a position"""
        # In a real implementation, this would track entry prices
        # For now, return the current price as a placeholder
        if symbol in self.indicators_cache:
            return self.indicators_cache[symbol]['current_price']
        return 0.0
        
    def get_indicators(self, symbol: str) -> Dict[str, float]:
        """Get current indicator values for a symbol"""
        return self.indicators_cache.get(symbol, {})
        
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status with additional metrics"""
        base_status = super().get_status()
        base_status.update({
            'indicators': self.indicators_cache,
            'price_history_lengths': {
                symbol: len(history) 
                for symbol, history in self.price_history.items()
            }
        })
        return base_status