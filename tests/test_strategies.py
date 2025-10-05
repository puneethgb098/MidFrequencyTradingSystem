"""
Test suite for trading strategies
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.strategies.base import BaseStrategy, Signal
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.arbitrage import ArbitrageStrategy
from src.strategies.factory import StrategyFactory


class MockRiskManager:
    def __init__(self):
        pass
        
    async def check_signal(self, signal):
        return True


class MockOrderRouter:
    def __init__(self):
        pass
        
    async def submit_order(self, **kwargs):
        return "ORDER_123"


@pytest.fixture
def mock_risk_manager():
    return MockRiskManager()


@pytest.fixture
def mock_order_router():
    return MockOrderRouter()


@pytest.fixture
def sample_market_data():
    return {
        'AAPL': Mock(
            symbol='AAPL',
            timestamp=datetime.now(),
            bid=150.0,
            ask=150.05,
            last=150.02,
            volume=1000
        ),
        'GOOGL': Mock(
            symbol='GOOGL',
            timestamp=datetime.now(),
            bid=2500.0,
            ask=2500.50,
            last=2500.25,
            volume=500
        )
    }


class TestBaseStrategy:
    
    def test_signal_creation(self):
        """Test signal object creation"""
        signal = Signal(
            symbol='AAPL',
            side='buy',
            quantity=100,
            signal_type='entry',
            confidence=0.8
        )
        
        assert signal.symbol == 'AAPL'
        assert signal.side == 'buy'
        assert signal.quantity == 100
        assert signal.signal_type == 'entry'
        assert signal.confidence == 0.8
        assert signal.timestamp is not None
        
    def test_signal_to_dict(self):
        """Test signal serialization"""
        signal = Signal(
            symbol='AAPL',
            side='buy',
            quantity=100,
            signal_type='entry',
            confidence=0.8,
            metadata={'reason': 'test'}
        )
        
        signal_dict = signal.to_dict()
        
        assert signal_dict['symbol'] == 'AAPL'
        assert signal_dict['side'] == 'buy'
        assert signal_dict['quantity'] == 100
        assert signal_dict['confidence'] == 0.8
        assert signal_dict['metadata']['reason'] == 'test'


class TestMeanReversionStrategy:
    
    @pytest.fixture
    def mean_reversion_strategy(self, mock_risk_manager, mock_order_router):
        return MeanReversionStrategy(
            name='test_mean_reversion',
            symbols=['AAPL', 'GOOGL'],
            config={
                'lookback_period': 20,
                'z_score_threshold': 2.0,
                'position_size': 0.1,
                'max_positions': 5
            },
            order_router=mock_order_router,
            risk_manager=mock_risk_manager
        )
    
    def test_strategy_initialization(self, mean_reversion_strategy):
        """Test strategy initialization"""
        assert mean_reversion_strategy.name == 'test_mean_reversion'
        assert mean_reversion_strategy.symbols == ['AAPL', 'GOOGL']
        assert mean_reversion_strategy.lookback_period == 20
        assert mean_reversion_strategy.z_score_threshold == 2.0
        
    def test_calculate_position_size(self, mean_reversion_strategy):
        """Test position size calculation"""
        # Mock market data
        market_data = Mock(last=150.0)
        
        size = mean_reversion_strategy._calculate_position_size('AAPL', market_data)
        assert size > 0
        assert size <= mean_reversion_strategy.position_size
        
    def test_get_status(self, mean_reversion_strategy):
        """Test strategy status"""
        status = mean_reversion_strategy.get_status()
        
        assert status['name'] == 'test_mean_reversion'
        assert status['is_running'] == False
        assert 'symbols' in status
        assert 'config' in status


class TestMomentumStrategy:
    
    @pytest.fixture
    def momentum_strategy(self, mock_risk_manager, mock_order_router):
        return MomentumStrategy(
            name='test_momentum',
            symbols=['AAPL', 'GOOGL'],
            config={
                'lookback_period': 10,
                'momentum_threshold': 0.02,
                'position_size': 0.1,
                'max_positions': 3
            },
            order_router=mock_order_router,
            risk_manager=mock_risk_manager
        )
    
    def test_strategy_initialization(self, momentum_strategy):
        """Test momentum strategy initialization"""
        assert momentum_strategy.name == 'test_momentum'
        assert momentum_strategy.symbols == ['AAPL', 'GOOGL']
        assert momentum_strategy.lookback_period == 10
        assert momentum_strategy.momentum_threshold == 0.02
        
    def test_calculate_momentum(self, momentum_strategy):
        """Test momentum calculation"""
        # Create test price series with upward trend
        prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
        
        momentum = momentum_strategy._calculate_momentum(prices)
        assert momentum > 0  # Should be positive for upward trend
        
        # Test with downward trend
        prices_down = np.array([110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100])
        momentum_down = momentum_strategy._calculate_momentum(prices_down)
        assert momentum_down < 0  # Should be negative for downward trend


class TestArbitrageStrategy:
    
    @pytest.fixture
    def arbitrage_strategy(self, mock_risk_manager, mock_order_router):
        return ArbitrageStrategy(
            name='test_arbitrage',
            symbols=['AAPL', 'GOOGL', 'MSFT'],
            config={
                'lookback_period': 60,
                'z_score_threshold': 2.0,
                'position_size': 0.05,
                'max_pairs': 5,
                'min_correlation': 0.7
            },
            order_router=mock_order_router,
            risk_manager=mock_risk_manager
        )
    
    def test_strategy_initialization(self, arbitrage_strategy):
        """Test arbitrage strategy initialization"""
        assert arbitrage_strategy.name == 'test_arbitrage'
        assert len(arbitrage_strategy.symbols) == 3
        assert arbitrage_strategy.lookback_period == 60
        assert len(arbitrage_strategy.pairs) == 3  # 3C2 = 3 pairs
        
    def test_initialize_pairs(self, arbitrage_strategy):
        """Test pair initialization"""
        expected_pairs = [
            ('AAPL', 'GOOGL'),
            ('AAPL', 'MSFT'),
            ('GOOGL', 'MSFT')
        ]
        
        assert sorted(arbitrage_strategy.pairs) == sorted(expected_pairs)
        
    def test_count_active_pairs(self, arbitrage_strategy):
        """Test active pair counting"""
        # Initially no active pairs
        assert arbitrage_strategy._count_active_pairs() == 0
        
        # Mock some positions
        arbitrage_strategy.positions['AAPL'] = 100
        arbitrage_strategy.positions['GOOGL'] = -100
        
        assert arbitrage_strategy._count_active_pairs() == 1


class TestStrategyFactory:
    
    def test_get_available_strategies(self):
        """Test getting available strategies"""
        strategies = StrategyFactory.get_available_strategies()
        
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert 'mean_reversion' in strategies
        assert 'momentum' in strategies
        assert 'arbitrage' in strategies
        
    def test_create_mean_reversion_strategy(self, mock_risk_manager, mock_order_router):
        """Test creating mean reversion strategy"""
        config = {
            'symbols': ['AAPL', 'GOOGL'],
            'parameters': {
                'lookback_period': 20,
                'z_score_threshold': 2.0
            }
        }
        
        strategy = StrategyFactory.create_strategy(
            'mean_reversion',
            config,
            mock_order_router,
            mock_risk_manager
        )
        
        assert isinstance(strategy, MeanReversionStrategy)
        assert strategy.name == 'mean_reversion'
        
    def test_create_momentum_strategy(self, mock_risk_manager, mock_order_router):
        """Test creating momentum strategy"""
        config = {
            'symbols': ['AAPL', 'GOOGL'],
            'parameters': {
                'lookback_period': 10,
                'momentum_threshold': 0.02
            }
        }
        
        strategy = StrategyFactory.create_strategy(
            'momentum',
            config,
            mock_order_router,
            mock_risk_manager
        )
        
        assert isinstance(strategy, MomentumStrategy)
        assert strategy.name == 'momentum'
        
    def test_create_arbitrage_strategy(self, mock_risk_manager, mock_order_router):
        """Test creating arbitrage strategy"""
        config = {
            'symbols': ['AAPL', 'GOOGL', 'MSFT'],
            'parameters': {
                'lookback_period': 60,
                'z_score_threshold': 2.0
            }
        }
        
        strategy = StrategyFactory.create_strategy(
            'arbitrage',
            config,
            mock_order_router,
            mock_risk_manager
        )
        
        assert isinstance(strategy, ArbitrageStrategy)
        assert strategy.name == 'arbitrage'
        
    def test_create_unknown_strategy(self, mock_risk_manager, mock_order_router):
        """Test creating unknown strategy type"""
        with pytest.raises(ValueError):
            StrategyFactory.create_strategy(
                'unknown_strategy',
                {},
                mock_order_router,
                mock_risk_manager
            )


class TestSignalExecution:
    
    @pytest.mark.asyncio
    async def test_signal_execution(self, mean_reversion_strategy, sample_market_data):
        """Test signal execution flow"""
        # Mock the execute_signal method
        mean_reversion_strategy.execute_signal = AsyncMock()
        
        # Create test signal
        signal = Signal(
            symbol='AAPL',
            side='buy',
            quantity=100,
            signal_type='entry'
        )
        
        # Process market data
        await mean_reversion_strategy.on_market_data(sample_market_data)
        
        # Verify execute_signal was called
        # Note: This is a simplified test - in reality, signals would be generated
        # based on strategy logic
        
    @pytest.mark.asyncio
    async def test_strategy_start_stop(self, mean_reversion_strategy):
        """Test strategy lifecycle"""
        # Start strategy
        await mean_reversion_strategy.start()
        assert mean_reversion_strategy.is_running == True
        
        # Check status
        status = mean_reversion_strategy.get_status()
        assert status['is_running'] == True
        
        # Stop strategy
        await mean_reversion_strategy.stop()
        assert mean_reversion_strategy.is_running == False


if __name__ == "__main__":
    pytest.main(["-v", __file__])