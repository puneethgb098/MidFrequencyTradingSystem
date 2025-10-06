import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import uuid

class OrderState(Enum):
    PENDING_RISK = "PENDING_RISK"
    PENDING_SUBMIT = "PENDING_SUBMIT" 
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILL = "PARTIAL_FILL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class OrderRequest(BaseModel):
    client_order_id: str
    strategy_id: str
    instrument_token: int
    quantity: int
    price: float
    order_type: str
    transaction_type: str
    time_in_force: str = "DAY"
    
class Order(BaseModel):
    client_order_id: str
    broker_order_id: Optional[str] = None
    strategy_id: str
    instrument_token: int
    quantity: int
    price: float
    order_type: str
    transaction_type: str
    time_in_force: str
    state: OrderState
    filled_quantity: int = 0
    average_price: float = 0.0
    created_at: datetime
    updated_at: datetime
    
class OrderManagementSystem:
    def __init__(self, risk_gate, execution_gateway, event_bus, db_connection):
        self.risk_gate = risk_gate
        self.execution_gateway = execution_gateway
        self.event_bus = event_bus
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
        
        # Order tracking
        self.active_orders: Dict[str, Order] = {}
        
    async def submit_order(self, order_request: OrderRequest) -> str:
        """Submit order through OMS pipeline"""
        
        # Create order object
        order = Order(
            client_order_id=order_request.client_order_id,
            strategy_id=order_request.strategy_id,
            instrument_token=order_request.instrument_token,
            quantity=order_request.quantity,
            price=order_request.price,
            order_type=order_request.order_type,
            transaction_type=order_request.transaction_type,
            time_in_force=order_request.time_in_force,
            state=OrderState.PENDING_RISK,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.active_orders[order.client_order_id] = order
        
        try:
            # Step 1: Risk check
            risk_result = await self.risk_gate.check_order(order_request.dict())
            
            if not risk_result.passed:
                order.state = OrderState.REJECTED
                await self._update_order_state(order, f"Risk rejected: {risk_result.message}")
                return order.client_order_id
                
            # Step 2: Submit to execution gateway
            order.state = OrderState.PENDING_SUBMIT
            await self._update_order_state(order, "Passed risk checks, submitting to broker")
            
            # Convert to execution format
            zerodha_order = self._convert_to_zerodha_order(order)
            broker_order_id = await self.execution_gateway.submit_order(zerodha_order)
            
            order.broker_order_id = broker_order_id
            order.state = OrderState.SUBMITTED
            await self._update_order_state(order, f"Submitted to broker: {broker_order_id}")
            
            # Persist to database
            await self._persist_order(order)
            
            return order.client_order_id
            
        except Exception as e:
            self.logger.error(f"Order submission failed: {e}")
            order.state = OrderState.FAILED
            await self._update_order_state(order, f"Submission failed: {str(e)}")
            return order.client_order_id
            
    async def cancel_order(self, client_order_id: str) -> bool:
        """Cancel order"""
        if client_order_id not in self.active_orders:
            return False
            
        order = self.active_orders[client_order_id]
        
        if order.state not in [OrderState.SUBMITTED, OrderState.PARTIAL_FILL]:
            return False
            
        try:
            success = await self.execution_gateway.cancel_order(client_order_id)
            if success:
                order.state = OrderState.CANCELLED
                await self._update_order_state(order, "Order cancelled")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {e}")
            return False
            
    async def handle_execution_update(self, update: Dict[str, Any]):
        """Handle execution updates from broker"""
        client_order_id = update.get('client_order_id')
        
        if client_order_id not in self.active_orders:
            self.logger.warning(f"Received update for unknown order: {client_order_id}")
            return
            
        order = self.active_orders[client_order_id]
        
        # Update order based on execution status
        if update['status'] == 'COMPLETE':
            order.state = OrderState.FILLED
            order.filled_quantity = update['filled_quantity']
            order.average_price = update['average_price']
        elif update['status'] == 'PARTIAL':
            order.state = OrderState.PARTIAL_FILL
            order.filled_quantity = update['filled_quantity']
            order.average_price = update['average_price']
        elif update['status'] == 'CANCELLED':
            order.state = OrderState.CANCELLED
        elif update['status'] == 'REJECTED':
            order.state = OrderState.REJECTED
            
        order.updated_at = datetime.utcnow()
        
        await self._update_order_state(order, f"Execution update: {update['status']}")
        await self._persist_order(order)
        
        # Clean up completed orders
        if order.state in [OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED]:
            del self.active_orders[client_order_id]
            
    async def _update_order_state(self, order: Order, message: str):
        """Update order state and publish event"""
        await self.event_bus.publish_order_event("ORDER_STATE_UPDATE", {
            "client_order_id": order.client_order_id,
            "broker_order_id": order.broker_order_id,
            "state": order.state.value,
            "message": message,
            "filled_quantity": order.filled_quantity,
            "average_price": order.average_price
        })
        
    def _convert_to_zerodha_order(self, order: Order):
        """Convert OMS order to Zerodha format"""
        from src.connectors.zerodha_exec import ZerodhaOrder
        
        return ZerodhaOrder(
            client_order_id=order.client_order_id,
            instrument_token=order.instrument_token,
            quantity=order.quantity,
            price=order.price,
            order_type=order.order_type,
            transaction_type=order.transaction_type,
            product="MIS",  # Intraday for futures
            timestamp=order.created_at
        )
        
    async def _persist_order(self, order: Order):
        """Persist order to database"""
        # Implementation would depend on your database setup
        # This is a placeholder for PostgreSQL integration
        pass
