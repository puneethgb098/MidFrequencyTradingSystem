"""
Arbitrage Strategy

Implements statistical arbitrage and pairs trading strategies.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from scipy import stats

from .base import BaseStrategy, Signal
from data.feeds import MarketData


class ArbitrageStrategy(BaseStrategy):
    """
    Statistical Arbitrage Strategy
    
    This strategy identifies pairs of assets that move together and
    takes contrarian positions when they diverge.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Strategy parameters
        self.lookback_period = self.config.get('lookback_period', 60)
        self.z_score_threshold = self.config.get('z_score_threshold', 2.0)
        self.position_size = self.config.get('position_size', 0.05)
        self.max_pairs = self.config.get('max_pairs', 5)
        self.min_correlation = self.config.get('min_correlation', 0.7)
        
        # Data storage
        self.price_history = {symbol: [] for symbol in self.symbols}
        self.pairs = []  # List of correlated pairs
        self.spread_history = {}  # Historical spread data for pairs
        self.current_spreads = {}  # Current spread values
        
        # Initialize pairs
        self._initialize_pairs()
        
    def _initialize_pairs(self):
        """Initialize trading pairs from symbols"""
        # Create all possible pairs from symbols
        for i in range(len(self.symbols)):
            for j in range(i + 1, len(self.symbols)):
                pair = (self.symbols[i], self.symbols[j])
                self.pairs.append(pair)
                self.spread_history[pair] = []
                
    async def on_market_data(self, market_data: Dict[str, MarketData]):
        """
        Process new market data and generate signals
        """
        if not self.is_running:
            return
            
        # Update price history
        for symbol, data in market_data.items():
            if symbol in self.symbols:
                self.price_history[symbol].append(data.last)
                
                # Keep only recent data
                if len(self.price_history[symbol]) > self.lookback_period * 2:
                    self.price_history[symbol] = self.price_history[symbol][-self.lookback_period * 2:]
                    
        # Generate signals if we have enough data
        if all(len(history) >= self.lookback_period for history in self.price_history.values()):
            signals = self.generate_signals(market_data)
            
            for signal in signals:
                self.add_signal(signal)
                await self.execute_signal(signal)
                
    def generate_signals(self, market_data: Dict[str, MarketData]) -> List[Signal]:
        """
        Generate arbitrage signals for correlated pairs
        """
        signals = []
        
        # Update spreads for all pairs
        self._update_spreads()
        
        # Generate signals for each pair
        for pair in self.pairs:
            pair_signals = self._generate_pair_signals(pair, market_data)
            signals.extend(pair_signals)
            
        return signals
        
    def _update_spreads(self):
        """Calculate and update spread values for all pairs"""
        for pair in self.pairs:
            symbol1, symbol2 = pair
            
            if (len(self.price_history[symbol1]) >= self.lookback_period and 
                len(self.price_history[symbol2]) >= self.lookback_period):
                
                # Get recent prices
                prices1 = np.array(self.price_history[symbol1][-self.lookback_period:])
                prices2 = np.array(self.price_history[symbol2][-self.lookback_period:])
                
                # Calculate correlation
                correlation = np.corrcoef(prices1, prices2)[0, 1]
                
                # Only trade highly correlated pairs
                if abs(correlation) >= self.min_correlation:
                    # Calculate spread (log ratio)
                    spread = np.log(prices1 / prices2)
                    
                    # Calculate z-score of spread
                    spread_mean = np.mean(spread)
                    spread_std = np.std(spread)
                    
                    if spread_std > 0:
                        current_spread = spread[-1]
                        z_score = (current_spread - spread_mean) / spread_std
                        
                        self.current_spreads[pair] = {
                            'spread': current_spread,
                            'z_score': z_score,
                            'correlation': correlation,
                            'mean': spread_mean,
                            'std': spread_std
                        }
                        
                        # Store in history
                        self.spread_history[pair].append({
                            'timestamp': datetime.now(),
                            'spread': current_spread,
                            'z_score': z_score
                        })
                        
                        # Keep only recent history
                        if len(self.spread_history[pair]) > self.lookback_period:
                            self.spread_history[pair] = self.spread_history[pair][-self.lookback_period:]
                            
    def _generate_pair_signals(self, pair: Tuple[str, str], market_data: Dict[str, MarketData]) -> List[Signal]:
        """Generate signals for a specific pair"""
        signals = []
        
        if pair not in self.current_spreads:
            return signals
            
        spread_data = self.current_spreads[pair]
        z_score = spread_data['z_score']
        symbol1, symbol2 = pair
        
        # Check current positions
        pos1 = self.positions.get(symbol1, 0)
        pos2 = self.positions.get(symbol2, 0)
        
        # Count active pairs
        active_pairs = self._count_active_pairs()
        
        # Entry signals
        if pos1 == 0 and pos2 == 0 and active_pairs < self.max_pairs:
            
            # Spread is too wide - expect mean reversion
            if z_score > self.z_score_threshold:
                # Long the underperformer, short the outperformer
                signals.extend([
                    Signal(
                        symbol=symbol1,
                        side='buy',
                        quantity=self._calculate_position_size(symbol1, market_data),
                        signal_type='entry',
                        confidence=min(z_score / self.z_score_threshold, 2.0),
                        metadata={
                            'strategy': 'arbitrage',
                            'pair': pair,
                            'z_score': z_score,
                            'reason': 'spread_wide_long_underperformer'
                        }
                    ),
                    Signal(
                        symbol=symbol2,
                        side='sell',
                        quantity=self._calculate_position_size(symbol2, market_data),
                        signal_type='entry',
                        confidence=min(z_score / self.z_score_threshold, 2.0),
                        metadata={
                            'strategy': 'arbitrage',
                            'pair': pair,
                            'z_score': z_score,
                            'reason': 'spread_wide_short_outperformer'
                        }
                    )
                ])
                
            elif z_score < -self.z_score_threshold:
                # Long the underperformer, short the outperformer
                signals.extend([
                    Signal(
                        symbol=symbol1,
                        side='sell',
                        quantity=self._calculate_position_size(symbol1, market_data),
                        signal_type='entry',
                        confidence=min(abs(z_score) / self.z_score_threshold, 2.0),
                        metadata={
                            'strategy': 'arbitrage',
                            'pair': pair,
                            'z_score': z_score,
                            'reason': 'spread_wide_short_underperformer'
                        }
                    ),
                    Signal(
                        symbol=symbol2,
                        side='buy',
                        quantity=self._calculate_position_size(symbol2, market_data),
                        signal_type='entry',
                        confidence=min(abs(z_score) / self.z_score_threshold, 2.0),
                        metadata={
                            'strategy': 'arbitrage',
                            'pair': pair,
                            'z_score': z_score,
                            'reason': 'spread_wide_long_outperformer'
                        }
                    )
                ])
                
        # Exit signals for existing positions
        elif (pos1 != 0 or pos2 != 0) and abs(z_score) < 0.5:
            # Spread has reverted to mean - exit positions
            if pos1 != 0:
                signals.append(Signal(
                    symbol=symbol1,
                    side='sell' if pos1 > 0 else 'buy',
                    quantity=abs(pos1),
                    signal_type='exit',
                    confidence=0.9,
                    metadata={
                        'strategy': 'arbitrage',
                        'pair': pair,
                        'z_score': z_score,
                        'reason': 'spread_reverted_to_mean'
                    }
                ))
                
            if pos2 != 0:
                signals.append(Signal(
                    symbol=symbol2,
                    side='sell' if pos2 > 0 else 'buy',
                    quantity=abs(pos2),
                    signal_type='exit',
                    confidence=0.9,
                    metadata={
                        'strategy': 'arbitrage',
                        'pair': pair,
                        'z_score': z_score,
                        'reason': 'spread_reverted_to_mean'
                    }
                ))
                
        return signals
        
    def _count_active_pairs(self) -> int:
        """Count number of active arbitrage pairs"""
        active_count = 0
        
        for pair in self.pairs:
            symbol1, symbol2 = pair
            pos1 = self.positions.get(symbol1, 0)
            pos2 = self.positions.get(symbol2, 0)
            
            if pos1 != 0 or pos2 != 0:
                active_count += 1
                
        return active_count
        
    def _calculate_position_size(self, symbol: str, market_data: Dict[str, MarketData]) -> float:
        """Calculate position size for arbitrage"""
        base_size = self.position_size
        
        # In arbitrage, we want smaller positions due to lower expected returns
        # but higher probability of success
        return base_size * 0.5
        
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status with additional metrics"""
        base_status = super().get_status()
        base_status.update({
            'active_pairs': self._count_active_pairs(),
            'current_spreads': self.current_spreads,
            'pairs_analyzed': len(self.pairs),
            'price_history_lengths': {
                symbol: len(history) 
                for symbol, history in self.price_history.items()
            }
        })
        return base_status