"""
Configuration Manager

Handles loading and management of system configuration.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Configuration Manager
    
    Manages system configuration loaded from YAML files.
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
        self.load_config()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
                self.config = self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = self._get_default_config()
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'name': 'Mid-Frequency Trading System',
                'version': '1.0.0',
                'timezone': 'UTC'
            },
            'data_feed': {
                'symbols': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
                'sources': ['yahoo', 'websocket'],
                'update_frequency': 1.0,
                'historical_days': 30
            },
            'strategies': {
                'mean_reversion': {
                    'symbols': ['AAPL', 'GOOGL'],
                    'parameters': {
                        'lookback_period': 20,
                        'z_score_threshold': 2.0,
                        'position_size': 0.1,
                        'max_positions': 5,
                        'stop_loss_pct': 0.05,
                        'take_profit_pct': 0.03
                    }
                },
                'momentum': {
                    'symbols': ['MSFT', 'AMZN'],
                    'parameters': {
                        'lookback_period': 10,
                        'momentum_threshold': 0.02,
                        'position_size': 0.1,
                        'max_positions': 3
                    }
                }
            },
            'risk_management': {
                'max_position_size': 100000,
                'max_portfolio_value': 10000000,
                'max_drawdown_pct': 0.10,
                'max_correlation': 0.8,
                'var_confidence': 0.95,
                'var_time_horizon': 1,
                'initial_cash': 1000000
            },
            'execution': {
                'venues': ['simulation'],
                'transaction_cost': 0.001,
                'slippage': 0.0005,
                'venue_weights': {
                    'simulation': 1.0
                }
            },
            'backtest': {
                'initial_capital': 1000000,
                'transaction_cost': 0.001,
                'slippage': 0.0005,
                'data_frequency': '1min'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/trading_system.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'web_dashboard': {
                'host': '0.0.0.0',
                'port': 8080,
                'debug': False,
                'update_frequency': 1.0
            }
        }
        
    def validate_config(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        """
        required_sections = [
            'system', 'data_feed', 'strategies', 
            'risk_management', 'execution'
        ]
        
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Missing required config section: {section}")
                return False
                
        return True
        
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config.copy()