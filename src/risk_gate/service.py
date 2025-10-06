import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum

class RiskViolationType(Enum):
    POSITION_LIMIT = "POSITION_LIMIT"
    NOTIONAL_LIMIT = "NOTIONAL_LIMIT" 
    PRICE_COLLAR = "PRICE_COLLAR"
    ORDER_RATE = "ORDER_RATE"
    DAILY_LOSS = "DAILY_LOSS"
    KILLSWITCH = "KILLSWITCH"

class RiskCheckResult(BaseModel):
    passed: bool
    violation_type: Optional[RiskViolationType] = None
    message: str
    timestamp: datetime

class RiskLimits(BaseModel):
    max_position_size: int = 100  # Max lots per instrument
    max_notional_per_order: float = 1000000  # 10L per order
    max_daily_loss: float = 50000  # 50K daily loss limit
    max_orders_per_minute: int = 60
    price_collar_pct: float = 0.05  # 5% price collar
    global_killswitch: bool = False

class PreTradeRiskGate:
    def __init__(self, redis_cache, event_bus, limits: RiskLimits):
        self.cache = redis_cache
        self.event_bus = event_bus
        self.limits = limits
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.order_timestamps: List[datetime] = []
        
        # Daily P&L tracking
        self.daily_pnl = 0.0
        self.last_pnl_reset = datetime.utcnow().date()
        
    async def check_order(self, order_request: Dict[str, Any]) -> RiskCheckResult:
        """Comprehensive pre-trade risk check"""
        
        # Global killswitch check
        if self.limits.global_killswitch:
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.KILLSWITCH,
                message="Global killswitch activated",
                timestamp=datetime.utcnow()
            )
            
        # Daily loss check
        if not await self._check_daily_loss():
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.DAILY_LOSS,
                message=f"Daily loss limit exceeded: {self.daily_pnl}",
                timestamp=datetime.utcnow()
            )
            
        # Position limit check
        if not await self._check_position_limit(order_request):
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.POSITION_LIMIT,
                message="Position limit exceeded",
                timestamp=datetime.utcnow()
            )
            
        # Notional limit check
        if not self._check_notional_limit(order_request):
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.NOTIONAL_LIMIT,
                message="Notional limit exceeded",
                timestamp=datetime.utcnow()
            )
            
        # Price collar check
        if not await self._check_price_collar(order_request):
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.PRICE_COLLAR,
                message="Price outside collar limits",
                timestamp=datetime.utcnow()
            )
            
        # Order rate check
        if not self._check_order_rate():
            return RiskCheckResult(
                passed=False,
                violation_type=RiskViolationType.ORDER_RATE,
                message="Order rate limit exceeded",
                timestamp=datetime.utcnow()
            )
            
        # All checks passed
        self._record_order_timestamp()
        
        return RiskCheckResult(
            passed=True,
            message="All risk checks passed",
            timestamp=datetime.utcnow()
        )
        
    async def _check_daily_loss(self) -> bool:
        """Check daily loss limit"""
        today = datetime.utcnow().date()
        if today > self.last_pnl_reset:
            self.daily_pnl = 0.0
            self.last_pnl_reset = today
            
        return self.daily_pnl > -self.limits.max_daily_loss
        
    async def _check_position_limit(self, order_request: Dict[str, Any]) -> bool:
        """Check position size limits"""
        instrument_token = order_request['instrument_token']
        order_quantity = order_request['quantity']
        transaction_type = order_request['transaction_type']
        
        # Get current position
        current_position = await self.cache.get_position(instrument_token)
        current_qty = current_position['quantity'] if current_position else 0
        
        # Calculate new position after order
        if transaction_type == 'BUY':
            new_qty = current_qty + order_quantity
        else:
            new_qty = current_qty - order_quantity
            
        return abs(new_qty) <= self.limits.max_position_size
        
    def _check_notional_limit(self, order_request: Dict[str, Any]) -> bool:
        """Check notional value limits"""
        notional = order_request['quantity'] * order_request['price']
        return notional <= self.limits.max_notional_per_order
        
    async def _check_price_collar(self, order_request: Dict[str, Any]) -> bool:
        """Check price collar limits"""
        instrument_token = order_request['instrument_token']
        order_price = order_request['price']
        
        # Get latest market price
        market_data = await self.cache.get_market_data(instrument_token)
        if not market_data:
            return True  # Allow if no market data
            
        market_price = market_data['last_price']
        collar_range = market_price * self.limits.price_collar_pct
        
        return (market_price - collar_range) <= order_price <= (market_price + collar_range)
        
    def _check_order_rate(self) -> bool:
        """Check order rate limits"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self.order_timestamps = [ts for ts in self.order_timestamps if ts > cutoff]
        
        return len(self.order_timestamps) < self.limits.max_orders_per_minute
        
    def _record_order_timestamp(self):
        """Record order timestamp for rate limiting"""
        self.order_timestamps.append(datetime.utcnow())
        
    async def activate_killswitch(self, reason: str):
        """Activate global killswitch"""
        self.limits.global_killswitch = True
        await self.event_bus.publish_risk_event("KILLSWITCH_ACTIVATED", {
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.logger.critical(f"KILLSWITCH ACTIVATED: {reason}")
        
    async def deactivate_killswitch(self):
        """Deactivate global killswitch"""
        self.limits.global_killswitch = False
        await self.event_bus.publish_risk_event("KILLSWITCH_DEACTIVATED", {
            "timestamp": datetime.utcnow().isoformat()
        })
        self.logger.info("Killswitch deactivated")
