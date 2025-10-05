# Installation Guide

This guide will help you install and set up the Mid-Frequency Trading System.

## Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

## System Requirements

- **Operating System**: Windows 10, macOS 10.15+, or Linux
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: At least 2GB of free disk space
- **Network**: Stable internet connection for market data

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/midfreq-trading-system.git
cd midfreq-trading-system
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# For development (optional)
pip install -e ".[dev]"

# For machine learning features (optional)
pip install -e ".[ml]"
```

### 4. Configuration Setup

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit the configuration file
# nano config/config.yaml  # On Linux/macOS
# notepad config/config.yaml  # On Windows
```

### 5. Create Required Directories

```bash
# Create logs directory
mkdir logs

# Create data directory for database files
mkdir data
```

## Configuration

### Basic Configuration

Edit `config/config.yaml` to customize your setup:

```yaml
# Market Data
symbols: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
data_sources: ['yahoo']

# Risk Management
max_position_size: 100000
max_drawdown_pct: 0.10
initial_cash: 1000000
```

### Advanced Configuration

For production use, consider these additional settings:

- **Database**: Configure PostgreSQL for better performance
- **Logging**: Set up proper log rotation and monitoring
- **Notifications**: Configure email alerts for important events

## Verification

### 1. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### 2. Test Basic Functionality

```bash
# Test strategy creation
python examples/basic_usage.py

# Test backtesting
python examples/backtest_example.py
```

### 3. Start Web Dashboard

```bash
# Start the web dashboard
cd web
python app.py

# Access at http://localhost:8080
```

## Docker Installation (Optional)

### 1. Build Docker Image

```bash
docker build -t midfreq-trading-system .
```

### 2. Run with Docker Compose

```bash
docker-compose up -d
```

### 3. Access Services

- **Trading System**: Port 8080
- **Database**: Port 5432 (if using PostgreSQL)
- **Monitoring**: Port 3000 (if using Grafana)

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project directory
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

2. **Permission Errors**
   ```bash
   # On Linux/macOS
   chmod +x examples/*.py
   ```

3. **Port Already in Use**
   ```bash
   # Find process using port 8080
   lsof -i :8080
   
   # Kill the process or change port in config
   ```

### Performance Optimization

1. **Increase Memory**: For large backtests, increase available memory
2. **Use SSD**: Store data files on SSD for better I/O performance
3. **Network**: Use wired connection for stable market data

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Database**: Use strong passwords for database connections
3. **Network**: Configure firewall rules for production deployment
4. **Updates**: Keep dependencies updated for security patches

## Next Steps

After installation:

1. Read the [User Guide](USER_GUIDE.md)
2. Review [Strategy Documentation](STRATEGIES.md)
3. Check [API Reference](API_REFERENCE.md)
4. Explore [Examples](../examples/)

## Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs on GitHub
- **Discussions**: Use GitHub Discussions for questions