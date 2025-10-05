"""
Web Dashboard

Interactive web interface for monitoring and controlling the trading system.
"""

import asyncio
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging

# Add the parent directory to the path to import trading system modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import TradingSystem
from src.utils.config import ConfigManager


app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-system-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global trading system instance
trading_system = None
config_manager = None


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current system status"""
    if trading_system:
        return jsonify(trading_system.get_system_status())
    return jsonify({'error': 'Trading system not initialized'})


@app.route('/api/performance')
def get_performance():
    """Get performance metrics"""
    if trading_system and trading_system.risk_manager:
        return jsonify(trading_system.risk_manager.get_metrics())
    return jsonify({'error': 'Performance data not available'})


@app.route('/api/strategies')
def get_strategies():
    """Get strategy information"""
    if trading_system:
        strategies_status = {}
        for name, strategy in trading_system.strategies.items():
            strategies_status[name] = strategy.get_status()
        return jsonify(strategies_status)
    return jsonify({'error': 'Strategies not available'})


@app.route('/api/start', methods=['POST'])
def start_system():
    """Start the trading system"""
    global trading_system
    try:
        if not trading_system:
            trading_system = TradingSystem()
            
        asyncio.create_task(trading_system.start())
        return jsonify({'status': 'success', 'message': 'Trading system started'})
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/stop', methods=['POST'])
def stop_system():
    """Stop the trading system"""
    global trading_system
    try:
        if trading_system:
            asyncio.create_task(trading_system.stop())
            return jsonify({'status': 'success', 'message': 'Trading system stopped'})
        return jsonify({'status': 'error', 'message': 'Trading system not running'})
    except Exception as e:
        logger.error(f"Error stopping system: {e}")
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    global config_manager
    
    if request.method == 'GET':
        if config_manager:
            return jsonify(config_manager.get_all())
        return jsonify({'error': 'Configuration not available'})
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            # Update configuration
            for key, value in new_config.items():
                config_manager.set(key, value)
            config_manager.save_config()
            return jsonify({'status': 'success', 'message': 'Configuration updated'})
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return jsonify({'status': 'error', 'message': str(e)})


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to trading system'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('subscribe_status')
def handle_subscribe_status():
    """Subscribe to status updates"""
    def send_status_updates():
        while True:
            if trading_system:
                status = trading_system.get_system_status()
                socketio.emit('status_update', status)
            socketio.sleep(5)  # Send updates every 5 seconds
    
    socketio.start_background_task(send_status_updates)


@socketio.on('subscribe_performance')
def handle_subscribe_performance():
    """Subscribe to performance updates"""
    def send_performance_updates():
        while True:
            if trading_system and trading_system.risk_manager:
                performance = trading_system.risk_manager.get_metrics()
                socketio.emit('performance_update', performance)
            socketio.sleep(10)  # Send updates every 10 seconds
    
    socketio.start_background_task(send_performance_updates)


def create_default_config():
    """Create default configuration file if it doesn't exist"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not config_path.exists():
        default_config = ConfigManager('')._get_default_config()
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        logger.info(f"Created default configuration at {config_path}")


if __name__ == '__main__':
    # Create default config if needed
    create_default_config()
    
    # Initialize configuration
    config_manager = ConfigManager('config/config.yaml')
    
    # Start the web application
    logger.info("Starting Trading System Dashboard")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)