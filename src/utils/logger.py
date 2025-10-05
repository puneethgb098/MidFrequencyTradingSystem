"""
Logging Configuration

Sets up structured logging for the trading system.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        config: Logging configuration dictionary
        
    Returns:
        Root logger instance
    """
    # Get logging configuration
    level = config.get('level', 'INFO')
    log_format = config.get('format', 
                           '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = config.get('file', 'trading_system.log')
    max_size = config.get('max_size', '10MB')
    backup_count = config.get('backup_count', 5)
    
    # Parse max size
    if isinstance(max_size, str):
        if max_size.endswith('MB'):
            max_bytes = int(max_size[:-2]) * 1024 * 1024
        elif max_size.endswith('KB'):
            max_bytes = int(max_size[:-2]) * 1024
        else:
            max_bytes = 10 * 1024 * 1024  # Default 10MB
    else:
        max_bytes = max_size
        
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            
            # Rotating file handler
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        ]
    )
    
    # Create logger for trading system
    logger = logging.getLogger('trading_system')
    
    # Add custom log levels if needed
    logging.addLevelName(25, "TRADE")  # Between INFO and WARNING
    
    def trade(self, message, *args, **kwargs):
        """Log trade execution"""
        self._log(25, message, args, **kwargs)
        
    logging.Logger.trade = trade
    
    logger.info("Logging system initialized")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"trading_system.{name}")


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging
    """
    
    def format(self, record):
        """Format log record with additional context"""
        # Add timestamp in ISO format
        record.iso_timestamp = self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Add log level name
        record.level_name = record.levelname
        
        # Format the message
        return super().format(record)


def setup_structured_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup structured logging for better log analysis
    
    Args:
        config: Logging configuration
        
    Returns:
        Logger instance
    """
    import json
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
                
            return json.dumps(log_data)
    
    # Setup JSON logging
    logger = setup_logging(config)
    
    # Add JSON handler for structured logging
    json_handler = logging.handlers.RotatingFileHandler(
        'logs/trading_system_structured.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    json_handler.setFormatter(JSONFormatter())
    json_handler.setLevel(logging.INFO)
    
    # Add to root logger
    logging.getLogger().addHandler(json_handler)
    
    return logger