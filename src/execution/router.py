"""
Smart Order Router

Intelligently routes orders to the best execution venue based on various factors.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from risk.manager import RiskManager


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order structure"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: OrderType
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    timestamp: datetime = None
    strategy: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class SmartOrderRouter:
    """
    Smart Order Router (SOR)
    
    Routes orders to the best execution venue based on:
    - Price improvement
    - Execution probability
    - Venue performance
    - Market conditions
    """
    
    def __init__(self, config: Dict[str, Any], risk_manager: RiskManager):
        self.config = config
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(__name__)
        
        # Venue configurations
        self.venues = config.get('venues', ['simulation'])
        self.venue_weights = config.get('venue_weights', {'simulation': 1.0})
        
        # Order management
        self.active_orders = {}  # order_id -> Order
        self.completed_orders = {}  # order_id -> Order
        self.order_counter = 0
        
        # Performance tracking
        self.venue_performance = {venue: {
            'total_orders': 0,
            'filled_orders': 0,
            'avg_fill_time': 0.0,
            'price_improvement': 0.0
        } for venue in self.venues}
        
    async def start(self):
        """Start the order router"""
        self.logger.info("Starting Smart Order Router")
        
        # Initialize venue connections
        for venue in self.venues:
            await self._initialize_venue(venue)
            
        # Start order monitoring
        asyncio.create_task(self._monitor_orders())
        
    async def stop(self):
        """Stop the order router"""
        self.logger.info("Stopping Smart Order Router")
        
        # Cancel all active orders
        for order in self.active_orders.values():
            await self.cancel_order(order.id)
            
    async def submit_order(self,
                          symbol: str,
                          side: str,
                          quantity: float,
                          order_type: str = 'market',
                          price: Optional[float] = None,
                          stop_price: Optional[float] = None,
                          strategy: str = "",
                          metadata: Dict[str, Any] = None) -> str:
        """
        Submit an order for execution
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: Type of order (market, limit, stop, stop_limit)
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            strategy: Strategy name submitting the order
            metadata: Additional order metadata
            
        Returns:
            Order ID
        """
        # Generate order ID
        self.order_counter += 1
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter}"
        
        # Create order object
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType(order_type),
            price=price,
            stop_price=stop_price,
            strategy=strategy,
            metadata=metadata or {}
        )
        
        # Route to best venue
        venue = await self._select_best_venue(order)
        
        # Submit to venue
        success = await self._submit_to_venue(order, venue)
        
        if success:
            order.status = OrderStatus.SUBMITTED
            self.active_orders[order_id] = order
            self.logger.info(f"Order submitted: {order_id} to {venue}")
        else:
            order.status = OrderStatus.REJECTED
            self.logger.error(f"Order rejected: {order_id}")
            
        return order_id
        
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            True if cancellation successful
        """
        if order_id not in self.active_orders:
            self.logger.warning(f"Order not found: {order_id}")
            return False
            
        order = self.active_orders[order_id]
        
        # Cancel from venue
        success = await self._cancel_from_venue(order)
        
        if success:
            order.status = OrderStatus.CANCELLED
            self.completed_orders[order_id] = order
            del self.active_orders[order_id]
            self.logger.info(f"Order cancelled: {order_id}")
        else:
            self.logger.error(f"Failed to cancel order: {order_id}")
            
        return success
        
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        if order_id in self.active_orders:
            return self.active_orders[order_id]
        elif order_id in self.completed_orders:
            return self.completed_orders[order_id]
        else:
            return None
            
    async def _select_best_venue(self, order: Order) -> str:
        """
        Select the best execution venue for an order
        
        Consider factors like:
        - Current venue performance
        - Order characteristics
        - Market conditions
        """
        # For now, use a simple weighted random selection
        # In production, this would be much more sophisticated
        
        # Calculate venue scores
        venue_scores = {}
        for venue in self.venues:
            base_score = self.venue_weights.get(venue, 1.0)
            
            # Adjust based on performance
            perf = self.venue_performance[venue]
            if perf['total_orders'] > 0:
                fill_rate = perf['filled_orders'] / perf['total_orders']
                base_score *= fill_rate
                
            venue_scores[venue] = base_score
            
        # Select venue with highest score
        best_venue = max(venue_scores, key=venue_scores.get)
        return best_venue
        
    async def _submit_to_venue(self, order: Order, venue: str) -> bool:
        """
        Submit order to a specific venue
        
        Args:
            order: Order to submit
            venue: Venue to submit to
            
        Returns:
            True if submission successful
        """
        try:
            # Simulate order submission
            # In production, this would connect to actual venues
            
            if venue == 'simulation':
                # Simulate order execution
                asyncio.create_task(self._simulate_execution(order))
                return True
            else:
                # Placeholder for real venue connection
                self.logger.warning(f"Venue not implemented: {venue}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting to venue {venue}: {e}")
            return False
            
    async def _simulate_execution(self, order: Order):
        """
        Simulate order execution for testing
        """
        # Simulate execution delay
        await asyncio.sleep(np.random.uniform(0.1, 0.5))
        
        # Simulate partial or full fill
        fill_probability = 0.9  # 90% fill rate
        
        if np.random.random() < fill_probability:
            # Fill the order
            fill_quantity = order.quantity
            if order.order_type == OrderType.LIMIT and order.price:
                fill_price = order.price
            else:
                # Simulate some price improvement
                fill_price = self._get_market_price(order.symbol) * np.random.uniform(0.999, 1.001)
                
            order.filled_quantity = fill_quantity
            order.avg_fill_price = fill_price
            order.status = OrderStatus.FILLED
            
            # Move to completed orders
            self.completed_orders[order.id] = order
            del self.active_orders[order.id]
            
            # Update venue performance
            venue = 'simulation'  # Default venue for simulation
            self.venue_performance[venue]['filled_orders'] += 1
            
            self.logger.info(f"Order filled: {order.id} at {fill_price}")
        else:
            # Order rejected
            order.status = OrderStatus.REJECTED
            self.completed_orders[order.id] = order
            del self.active_orders[order.id]
            
    def _get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        # In a real implementation, this would get the current market price
        # For simulation, return a reasonable price
        return 100.0
        
    async def _monitor_orders(self):
        """Monitor and manage active orders"""
        while True:
            try:
                # Check for order timeouts
                current_time = datetime.now()
                timeout_orders = []
                
                for order_id, order in self.active_orders.items():
                    if (current_time - order.timestamp).seconds > 300:  # 5 minute timeout
                        timeout_orders.append(order_id)
                        
                # Cancel timed out orders
                for order_id in timeout_orders:
                    await self.cancel_order(order_id)
                    
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in order monitoring: {e}")
                await asyncio.sleep(10)
                
    async def _initialize_venue(self, venue: str):
        """Initialize connection to a venue"""
        self.logger.info(f"Initializing venue: {venue}")
        # In production, this would establish actual connections
        
    async def _cancel_from_venue(self, order: Order) -> bool:
        """Cancel order from a venue"""
        # For simulation, just return success
        return True
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get router performance metrics"""
        return {
            'active_orders': len(self.active_orders),
            'completed_orders': len(self.completed_orders),
            'venue_performance': self.venue_performance
        }
        
    def get_status(self) -> Dict[str, Any]:
        """Get router status"""
        return {
            'is_running': True,
            'venues': self.venues,
            'performance': self.get_performance_metrics()
        }