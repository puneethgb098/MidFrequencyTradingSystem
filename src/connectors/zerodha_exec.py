import asyncio
import logging
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel
import redis.asyncio as redis
from kiteconnect import KiteConnect

class OrderStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ZerodhaOrder(BaseModel):
    client_order_id: str
    broker_order_id: Optional[str] = None
    instrument_token: int
    quantity: int
    price: float
    order_type: str  # MIS, CNC, NRML
    transaction_type: str  # BUY, SELL
    product: str  # MIS, CNC, NRML
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: float = 0.0
    timestamp: datetime
    update_timestamp: Optional[datetime] = None

class ZerodhaExecutionGateway:
    def __init__(self, api_key: str, access_token: str, redis_client: redis.Redis):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Order tracking
        self.pending_orders: Dict[str, ZerodhaOrder] = {}
        
        # WebSocket for order updates
        from kiteconnect import KiteTicker
        self.ticker = KiteTicker(api_key, access_token)
        self.ticker.on_order_update = self._on_order_update
        
    async def submit_order(self, order: ZerodhaOrder) -> str:
        """Submit order to Zerodha with idempotent handling"""
        try:
            # Check for duplicate client order ID
            if order.client_order_id in self.pending_orders:
                existing_order = self.pending_orders[order.client_order_id]
                if existing_order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                    return existing_order.broker_order_id
                    
            # Submit to Zerodha
            response = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NFO,  # For index futures
                tradingsymbol=self._get_trading_symbol(order.instrument_token),
                transaction_type=order.transaction_type,
                quantity=order.quantity,
                product=order.product,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=order.price,
                tag=order.client_order_id  # For tracking
            )
            
            order.broker_order_id = response['order_id']
            order.status = OrderStatus.OPEN
            self.pending_orders[order.client_order_id] = order
            
            # Publish order event
            await self._publish_order_event("ORDER_SUBMITTED", order)
            
            return response['order_id']
            
        except Exception as e:
            self.logger.error(f"Order submission failed: {e}")
            order.status = OrderStatus.REJECTED
            await self._publish_order_event("ORDER_REJECTED", order)
            raise
            
    async def cancel_order(self, client_order_id: str) -> bool:
        """Cancel pending order"""
        if client_order_id not in self.pending_orders:
            return False
            
        order = self.pending_orders[client_order_id]
        if not order.broker_order_id:
            return False
            
        try:
            self.kite.cancel_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order.broker_order_id
            )
            
            order.status = OrderStatus.CANCELLED
            await self._publish_order_event("ORDER_CANCELLED", order)
            return True
            
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {e}")
            return False
            
    def _on_order_update(self, ws, data):
        """Handle real-time order updates from WebSocket"""
        try:
            order_id = data.get('order_id')
            client_order_id = data.get('tag')  # Our client order ID
            
            if client_order_id in self.pending_orders:
                order = self.pending_orders[client_order_id]
                
                # Update order status
                if data['status'] == 'COMPLETE':
                    order.status = OrderStatus.COMPLETE
                    order.filled_quantity = data['filled_quantity']
                    order.average_price = data['average_price']
                elif data['status'] == 'CANCELLED':
                    order.status = OrderStatus.CANCELLED
                elif data['status'] == 'REJECTED':
                    order.status = OrderStatus.REJECTED
                    
                order.update_timestamp = datetime.utcnow()
                
                # Publish update
                asyncio.create_task(
                    self._publish_order_event("ORDER_UPDATED", order)
                )
                
        except Exception as e:
            self.logger.error(f"Error processing order update: {e}")
            
    async def _publish_order_event(self, event_type: str, order: ZerodhaOrder):
        """Publish order events to Redis Stream"""
        await self.redis.xadd(
            "order_events",
            {
                "event_type": event_type,
                "client_order_id": order.client_order_id,
                "broker_order_id": order.broker_order_id or "",
                "status": order.status.value,
                "filled_quantity": order.filled_quantity,
                "average_price": order.average_price,
                "timestamp": order.update_timestamp.isoformat() if order.update_timestamp else ""
            },
            maxlen=50000
        )
        
    def _get_trading_symbol(self, instrument_token: int) -> str:
        """Convert instrument token to trading symbol"""
        # This would typically use Kite's instruments list
        # Simplified for demonstration
        instruments = self.kite.instruments("NFO")
        for instrument in instruments:
            if instrument['instrument_token'] == instrument_token:
                return instrument['tradingsymbol']
        raise ValueError(f"Unknown instrument token: {instrument_token}")
