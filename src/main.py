#!/usr/bin/env python3
"""
Main entry point for the Mid-Frequency Trading System
"""

import asyncio
import logging
from typing import Dict, Any
import yaml
from pathlib import Path

from data.feeds import MarketDataFeed
from strategies.factory import StrategyFactory
from execution.router import SmartOrderRouter
from risk.manager import RiskManager
from backtest.engine import BacktestEngine
from utils.config import ConfigManager
from utils.logger import setup_logging


class TradingSystem:
    """
    Main trading system orchestrator
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = ConfigManager(config_path)
        setup_logging(self.config.get('logging', {}))
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.data_feed = None
        self.strategies = {}
        self.order_router = None
        self.risk_manager = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize all system components"""
        self.logger.info("Initializing trading system...")
        
        # Initialize market data feed
        self.data_feed = MarketDataFeed(
            self.config.get('data_feed', {})
        )
        
        # Initialize risk manager
        self.risk_manager = RiskManager(
            self.config.get('risk_management', {})
        )
        
        # Initialize order router
        self.order_router = SmartOrderRouter(
            self.config.get('execution', {}),
            self.risk_manager
        )
        
        # Initialize strategies
        strategy_configs = self.config.get('strategies', {})
        for strategy_name, strategy_config in strategy_configs.items():
            strategy = StrategyFactory.create_strategy(
                strategy_name,
                strategy_config,
                self.order_router,
                self.risk_manager
            )
            self.strategies[strategy_name] = strategy
            
        self.logger.info("Trading system initialized successfully")
        
    async def start(self):
        """Start the trading system"""
        self.logger.info("Starting trading system...")
        self.is_running = True
        
        # Start data feed
        await self.data_feed.start()
        
        # Start strategies
        for strategy in self.strategies.values():
            await strategy.start()
            
        # Start order router
        await self.order_router.start()
        
        self.logger.info("Trading system started")
        
        # Main event loop
        try:
            while self.is_running:
                await self._process_market_data()
                await asyncio.sleep(0.1)  # 100ms tick
        except KeyboardInterrupt:
            await self.stop()
            
    async def stop(self):
        """Stop the trading system"""
        self.logger.info("Stopping trading system...")
        self.is_running = False
        
        # Stop all components
        await self.data_feed.stop()
        
        for strategy in self.strategies.values():
            await strategy.stop()
            
        await self.order_router.stop()
        
        self.logger.info("Trading system stopped")
        
    async def _process_market_data(self):
        """Process incoming market data"""
        market_data = await self.data_feed.get_latest_data()
        
        if market_data:
            # Update strategies with new data
            for strategy in self.strategies.values():
                await strategy.on_market_data(market_data)
                
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'strategies': {
                name: strategy.get_status() 
                for name, strategy in self.strategies.items()
            },
            'data_feed': self.data_feed.get_status() if self.data_feed else {},
            'risk_metrics': self.risk_manager.get_metrics() if self.risk_manager else {}
        }


async def main():
    """Main function"""
    system = TradingSystem()
    await system.initialize()
    await system.start()


if __name__ == "__main__":
    asyncio.run(main())