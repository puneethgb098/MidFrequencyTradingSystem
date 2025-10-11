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
import redis.asyncio as redis

# Add the parent directory to the path to import trading system modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import TradingSystem
from src.utils.config import ConfigManager
from src.services.order_book_service import OrderBookService


app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-system-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global trading system instance
trading_system = None
config_manager = None
order_book_service = None
redis_client = None


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/market_depth')
def market_depth():
    """Market depth visualization page"""
    return render_template('market_depth.html')


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


@app.route('/api/market_data')
def get_market_data():
    """Get current market data for monitored instruments"""
    global order_book_service

    try:
        if not order_book_service:
            return jsonify({'error': 'Order book service not initialized'})

        # Get instrument tokens from query params or use defaults
        tokens_str = request.args.get('tokens', '')
        if tokens_str:
            tokens = [int(t.strip()) for t in tokens_str.split(',')]
        else:
            tokens = []

        if not tokens:
            return jsonify({'error': 'No instrument tokens provided'})

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(order_book_service.get_multiple_instruments(tokens))
        loop.close()

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/order_book/<int:instrument_token>')
def get_order_book(instrument_token):
    """Get Level 5 order book for a specific instrument"""
    global order_book_service

    try:
        if not order_book_service:
            return jsonify({'error': 'Order book service not initialized'})

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        order_book = loop.run_until_complete(order_book_service.get_order_book(instrument_token))
        loop.close()

        if not order_book:
            return jsonify({'error': 'No data available for this instrument'})

        return jsonify(order_book)
    except Exception as e:
        logger.error(f"Error fetching order book: {e}")
        return jsonify({'error': str(e)})


@app.route('/api/price_history/<int:instrument_token>')
def get_price_history(instrument_token):
    """Get price history for charting"""
    global order_book_service

    try:
        if not order_book_service:
            return jsonify({'error': 'Order book service not initialized'})

        count = int(request.args.get('count', 100))

        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        history = loop.run_until_complete(order_book_service.get_price_history(instrument_token, count))
        loop.close()

        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
        return jsonify({'error': str(e)})


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


@socketio.on('subscribe_order_book')
def handle_subscribe_order_book(data):
    """Subscribe to real-time order book updates"""
    instrument_token = data.get('instrument_token')

    if not instrument_token:
        emit('error', {'message': 'No instrument token provided'})
        return

    def send_order_book_updates():
        global order_book_service
        while True:
            if order_book_service:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    order_book = loop.run_until_complete(
                        order_book_service.get_order_book(instrument_token)
                    )
                    loop.close()

                    if order_book:
                        socketio.emit('order_book_update', order_book)
                except Exception as e:
                    logger.error(f"Error in order book subscription: {e}")

            socketio.sleep(1)  # Send updates every second

    socketio.start_background_task(send_order_book_updates)


@socketio.on('subscribe_price_chart')
def handle_subscribe_price_chart(data):
    """Subscribe to real-time price chart updates"""
    instrument_token = data.get('instrument_token')

    if not instrument_token:
        emit('error', {'message': 'No instrument token provided'})
        return

    def send_price_updates():
        global order_book_service
        while True:
            if order_book_service:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    tick = loop.run_until_complete(
                        order_book_service.get_latest_tick(instrument_token)
                    )
                    loop.close()

                    if tick:
                        socketio.emit('price_update', {
                            'instrument_token': instrument_token,
                            'timestamp': tick.get('process_timestamp'),
                            'bid_price': float(tick.get('bid_price', 0)),
                            'ask_price': float(tick.get('ask_price', 0)),
                            'last_price': float(tick.get('last_price', 0))
                        })
                except Exception as e:
                    logger.error(f"Error in price chart subscription: {e}")

            socketio.sleep(1)  # Send updates every second

    socketio.start_background_task(send_price_updates)


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

    # Initialize Redis client and order book service
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    redis_client = loop.run_until_complete(redis.from_url(redis_url))
    order_book_service = OrderBookService(redis_client)
    logger.info(f"Connected to Redis at {redis_url}")

    # Start the web application
    logger.info("Starting Trading System Dashboard")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)