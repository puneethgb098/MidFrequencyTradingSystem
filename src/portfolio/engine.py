import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class PositionUpdate(BaseModel):
    instrument_token: int
    quantity_change: int
    price: float
    commission: float = 0.0
    timestamp: datetime

class PortfolioState(BaseModel):
    cash: float
    positions: Dict[int, Dict[str, Any]]  # instrument_token -> position info
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    last_update: datetime

class PortfolioEngine:
    def __init__(self, event_bus, cache, initial_cash: float = 1000000):
        self.event_bus = event_bus
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        
        # Portfolio state
        self.state = PortfolioState(
            cash=initial_cash,
            positions={},
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            total_pnl=0.0,
            last_update=datetime.utcnow()
        )
        
    async def process_fill(self, fill_data: Dict[str, Any]):
        """Process order fill and update portfolio"""
        try:
            instrument_token = fill_data['instrument_token']
            quantity = fill_data['filled_quantity']
            price = fill_data['average_price']
            transaction_type = fill_data['transaction_type']
            
            # Adjust quantity for sell orders
            if transaction_type == 'SELL':
                quantity = -quantity
                
            update = PositionUpdate(
                instrument_token=instrument_token,
                quantity_change=quantity,
                price=price,
                commission=self._calculate_commission(quantity, price),
                timestamp=datetime.utcnow()
            )
            
            await self._update_position(update)
            await self._calculate_pnl()
            await self._publish_portfolio_update()
            
        except Exception as e:
            self.logger.error(f"Error processing fill: {e}")
            
    async def _update_position(self, update: PositionUpdate):
        """Update position based on fill"""
        token = update.instrument_token
        
        if token in self.state.positions:
            # Update existing position
            pos = self.state.positions[token]
            old_qty = pos['quantity']
            old_avg = pos['average_price']
            
            new_qty = old_qty + update.quantity_change
            
            if new_qty == 0:
                # Position closed - calculate realized P&L
                realized_pnl = old_qty * (update.price - old_avg)
                self.state.realized_pnl += realized_pnl
                del self.state.positions[token]
            else:
                # Position modified
                if (old_qty > 0 and update.quantity_change > 0) or (old_qty < 0 and update.quantity_change < 0):
                    # Same direction - update average price
                    new_avg = ((old_qty * old_avg) + (update.quantity_change * update.price)) / new_qty
                else:
                    # Opposite direction - partial close
                    close_qty = min(abs(old_qty), abs(update.quantity_change))
                    realized_pnl = close_qty * (update.price - old_avg) * (1 if old_qty > 0 else -1)
                    self.state.realized_pnl += realized_pnl
                    
                    if abs(new_qty) < abs(old_qty):
                        # Position reduced
                        new_avg = old_avg
                    else:
                        # Position reversed
                        new_avg = update.price
                        
                self.state.positions[token] = {
                    'quantity': new_qty,
                    'average_price': new_avg,
                    'last_update': update.timestamp
                }
        else:
            # New position
            self.state.positions[token] = {
                'quantity': update.quantity_change,
                'average_price': update.price,
                'last_update': update.timestamp
            }
            
        # Update cash
        cash_impact = -(update.quantity_change * update.price) - update.commission
        self.state.cash += cash_impact
        
        # Update cache
        await self.cache.update_position(token, update.quantity_change, update.price)
        
    async def _calculate_pnl(self):
        """Calculate unrealized P&L based on current market prices"""
        unrealized_pnl = 0.0
        
        for token, position in self.state.positions.items():
            # Get current market price
            market_data = await self.cache.get_market_data(token)
            if market_data:
                current_price = market_data['last_price']
                position_pnl = position['quantity'] * (current_price - position['average_price'])
                unrealized_pnl += position_pnl
                
        self.state.unrealized_pnl = unrealized_pnl
        self.state.total_pnl = self.state.realized_pnl + self.state.unrealized_pnl
        self.state.last_update = datetime.utcnow()
        
    async def _publish_portfolio_update(self):
        """Publish portfolio state update"""
        await self.event_bus.publish_risk_event("PORTFOLIO_UPDATE", {
            "cash": self.state.cash,
            "realized_pnl": self.state.realized_pnl,
            "unrealized_pnl": self.state.unrealized_pnl,
            "total_pnl": self.state.total_pnl,
            "position_count": len(self.state.positions),
            "timestamp": self.state.last_update.isoformat()
        })
        
    def _calculate_commission(self, quantity: int, price: float) -> float:
        """Calculate commission and fees"""
        # Zerodha futures commission structure
        turnover = abs(quantity) * price
        brokerage = min(20, turnover * 0.0003)  # Rs 20 or 0.03% whichever is lower
        
        # Add other charges (STT, transaction charges, GST, etc.)
        stt = turnover * 0.0001  # 0.01% on sell side
        transaction_charges = turnover * 0.000019  # NSE transaction charges
        gst = (brokerage + transaction_charges) * 0.18
        
        return brokerage + stt + transaction_charges + gst
        
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        await self._calculate_pnl()
        
        return {
            "cash": self.state.cash,
            "realized_pnl": self.state.realized_pnl,
            "unrealized_pnl": self.state.unrealized_pnl,
            "total_pnl": self.state.total_pnl,
            "positions": self.state.positions,
            "last_update": self.state.last_update.isoformat()
        }
