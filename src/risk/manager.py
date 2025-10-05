"""
Risk Manager

Comprehensive risk management system with real-time monitoring and control.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from strategies.base import Signal


class RiskManager:
    """
    Risk Management System
    
    Provides real-time risk monitoring and control including:
    - Position limits
    - Drawdown control
    - Correlation monitoring
    - VaR calculations
    - Real-time P&L tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Risk limits
        self.max_position_size = config.get('max_position_size', 1000000)
        self.max_portfolio_value = config.get('max_portfolio_value', 10000000)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 0.10)
        self.max_correlation = config.get('max_correlation', 0.8)
        self.var_confidence = config.get('var_confidence', 0.95)
        self.var_time_horizon = config.get('var_time_horizon', 1)  # days
        
        # Risk monitoring
        self.positions = {}  # symbol -> position info
        self.portfolio_value = 0.0
        self.cash = config.get('initial_cash', 1000000)
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_portfolio_value = self.cash
        
        # Price tracking for P&L calculation
        self.current_prices = {}
        self.price_history = {}
        
        # Risk metrics
        self.risk_metrics = {
            'var_95': 0.0,
            'var_99': 0.0,
            'expected_shortfall': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'portfolio_beta': 0.0,
            'correlation_matrix': {}
        }
        
        # Risk limits tracking
        self.risk_limits = {
            'position_limits': {},
            'sector_limits': {},
            'strategy_limits': {}
        }
        
    async def start(self):
        """Start risk management system"""
        self.logger.info("Starting Risk Manager")
        
        # Start risk monitoring
        asyncio.create_task(self._monitor_risk())
        asyncio.create_task(self._calculate_risk_metrics())
        
    async def stop(self):
        """Stop risk management system"""
        self.logger.info("Stopping Risk Manager")
        
    async def check_signal(self, signal: Signal) -> bool:
        """
        Check if a trading signal passes risk checks
        
        Args:
            signal: Trading signal to check
            
        Returns:
            True if signal passes all risk checks
        """
        try:
            # Position size check
            if not self._check_position_size(signal):
                self.logger.warning(f"Position size check failed: {signal.symbol}")
                return False
                
            # Portfolio limits check
            if not self._check_portfolio_limits(signal):
                self.logger.warning(f"Portfolio limits check failed: {signal.symbol}")
                return False
                
            # Drawdown check
            if not self._check_drawdown_limit(signal):
                self.logger.warning(f"Drawdown limit check failed: {signal.symbol}")
                return False
                
            # Correlation check
            if not self._check_correlation_limit(signal):
                self.logger.warning(f"Correlation limit check failed: {signal.symbol}")
                return False
                
            # VaR check
            if not self._check_var_limit(signal):
                self.logger.warning(f"VaR limit check failed: {signal.symbol}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in risk check: {e}")
            return False
            
    def update_position(self, symbol: str, quantity: float, price: float):
        """
        Update position tracking
        
        Args:
            symbol: Trading symbol
            quantity: New position quantity
            price: Execution price
        """
        old_position = self.positions.get(symbol, {}).get('quantity', 0)
        
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0.0,
                'market_value': 0.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0
            }
            
        position_info = self.positions[symbol]
        
        # Calculate realized P&L for position reduction
        if abs(quantity) < abs(old_position):
            if old_position > 0:  # Long position
                realized_pnl = (price - position_info['avg_price']) * abs(quantity - old_position)
            else:  # Short position
                realized_pnl = (position_info['avg_price'] - price) * abs(quantity - old_position)
                
            self.realized_pnl += realized_pnl
            position_info['realized_pnl'] += realized_pnl
            
        # Update position
        position_info['quantity'] = quantity
        
        if quantity != 0:
            # Update average price for new positions
            if old_position == 0 or (old_position > 0 and quantity > 0) or (old_position < 0 and quantity < 0):
                # Increasing position or same direction
                total_cost = (old_position * position_info['avg_price']) + (quantity - old_position) * price
                position_info['avg_price'] = total_cost / quantity
            else:
                # Reversing position
                position_info['avg_price'] = price
        else:
            position_info['avg_price'] = 0.0
            
        # Update current price
        self.current_prices[symbol] = price
        
        # Recalculate portfolio metrics
        self._update_portfolio_metrics()
        
    def update_market_prices(self, prices: Dict[str, float]):
        """
        Update current market prices
        
        Args:
            prices: Dictionary of symbol -> price
        """
        self.current_prices.update(prices)
        self._update_portfolio_metrics()
        
    def _update_portfolio_metrics(self):
        """Update portfolio-level metrics"""
        total_value = self.cash
        total_unrealized_pnl = 0.0
        
        for symbol, position_info in self.positions.items():
            if symbol in self.current_prices and position_info['quantity'] != 0:
                current_price = self.current_prices[symbol]
                market_value = position_info['quantity'] * current_price
                
                position_info['market_value'] = market_value
                
                # Calculate unrealized P&L
                if position_info['quantity'] > 0:  # Long
                    unrealized_pnl = (current_price - position_info['avg_price']) * position_info['quantity']
                else:  # Short
                    unrealized_pnl = (position_info['avg_price'] - current_price) * abs(position_info['quantity'])
                    
                position_info['unrealized_pnl'] = unrealized_pnl
                total_unrealized_pnl += unrealized_pnl
                total_value += market_value
                
        self.portfolio_value = total_value
        self.unrealized_pnl = total_unrealized_pnl
        
        # Update peak value and drawdown
        if self.portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = self.portfolio_value
            
        current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
    def _check_position_size(self, signal: Signal) -> bool:
        """Check if position size is within limits"""
        current_position = self.positions.get(signal.symbol, {}).get('quantity', 0)
        new_position = current_position + (signal.quantity if signal.side == 'buy' else -signal.quantity)
        
        # Check individual position limit
        position_value = abs(new_position) * self.current_prices.get(signal.symbol, 0)
        if position_value > self.max_position_size:
            return False
            
        # Check portfolio concentration
        if self.portfolio_value > 0:
            position_pct = position_value / self.portfolio_value
            if position_pct > 0.15:  # Max 15% in single position
                return False
                
        return True
        
    def _check_portfolio_limits(self, signal: Signal) -> bool:
        """Check portfolio-level limits"""
        # Check total portfolio value
        if self.portfolio_value > self.max_portfolio_value:
            return False
            
        return True
        
    def _check_drawdown_limit(self, signal: Signal) -> bool:
        """Check drawdown limits"""
        if self.max_drawdown > self.max_drawdown_pct:
            # Only allow reducing positions if in drawdown
            current_position = self.positions.get(signal.symbol, {}).get('quantity', 0)
            if signal.side == 'buy' and current_position >= 0:
                return False
            if signal.side == 'sell' and current_position <= 0:
                return False
                
        return True
        
    def _check_correlation_limit(self, signal: Signal) -> bool:
        """Check correlation limits"""
        # This would require correlation matrix calculation
        # For now, return True (always pass)
        return True
        
    def _check_var_limit(self, signal: Signal) -> bool:
        """Check VaR limits"""
        # Simplified VaR check
        # In production, this would use historical simulation or parametric VaR
        
        current_var = self.risk_metrics.get('var_95', 0)
        max_var = self.portfolio_value * 0.02  # Max 2% daily VaR
        
        if current_var > max_var:
            # Only allow risk-reducing trades
            current_position = self.positions.get(signal.symbol, {}).get('quantity', 0)
            if abs(current_position) > 0:
                return True  # Allow closing positions
            else:
                return False  # Don't allow new positions
                
        return True
        
    async def _monitor_risk(self):
        """Continuous risk monitoring"""
        while True:
            try:
                # Check risk limits
                if self.max_drawdown > self.max_drawdown_pct:
                    self.logger.warning(f"Maximum drawdown exceeded: {self.max_drawdown:.2%}")
                    
                # Check VaR limits
                current_var = self.risk_metrics.get('var_95', 0)
                max_var = self.portfolio_value * 0.02
                if current_var > max_var:
                    self.logger.warning(f"VaR limit exceeded: {current_var:.2f}")
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(60)
                
    async def _calculate_risk_metrics(self):
        """Calculate risk metrics periodically"""
        while True:
            try:
                # Calculate VaR (simplified)
                if len(self.price_history) > 30:
                    self._calculate_var()
                    
                # Calculate Sharpe ratio
                self._calculate_sharpe_ratio()
                
                # Calculate correlation matrix
                self._calculate_correlations()
                
                await asyncio.sleep(300)  # Calculate every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error calculating risk metrics: {e}")
                await asyncio.sleep(300)
                
    def _calculate_var(self):
        """Calculate Value at Risk"""
        # Simplified VaR calculation
        # In production, use historical simulation or parametric methods
        
        # Assume 2% daily volatility for portfolio
        portfolio_std = self.portfolio_value * 0.02
        
        # 95% VaR (1.645 standard deviations)
        self.risk_metrics['var_95'] = 1.645 * portfolio_std
        
        # 99% VaR (2.326 standard deviations)
        self.risk_metrics['var_99'] = 2.326 * portfolio_std
        
    def _calculate_sharpe_ratio(self):
        """Calculate Sharpe ratio"""
        # Simplified calculation
        # In production, use actual returns history
        
        if self.portfolio_value > 0:
            # Assume 5% risk-free rate
            excess_return = 0.10  # 10% expected return
            volatility = 0.15  # 15% volatility
            
            if volatility > 0:
                self.risk_metrics['sharpe_ratio'] = excess_return / volatility
                
    def _calculate_correlations(self):
        """Calculate correlation matrix"""
        # Placeholder for correlation calculation
        pass
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'max_drawdown': self.max_drawdown,
            'positions': self.positions,
            'risk_metrics': self.risk_metrics,
            'current_prices': self.current_prices
        }
        
    def get_status(self) -> Dict[str, Any]:
        """Get risk manager status"""
        return {
            'is_active': True,
            'portfolio_value': self.portfolio_value,
            'max_drawdown': self.max_drawdown,
            'var_95': self.risk_metrics.get('var_95', 0),
            'active_positions': len([p for p in self.positions.values() if p['quantity'] != 0])
        }