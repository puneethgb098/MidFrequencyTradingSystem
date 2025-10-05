# Makefile for Mid-Frequency Trading System

.PHONY: help install install-dev test lint format clean run dashboard backtest docker-build docker-run docker-stop

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean temporary files"
	@echo "  run          - Run trading system"
	@echo "  dashboard    - Run web dashboard"
	@echo "  backtest     - Run backtest example"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker services"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Testing and quality
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/ examples/
	mypy src/

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

# Running the system
run:
	python -m src.main

dashboard:
	cd web && python app.py

backtest:
	python examples/backtest_example.py

# Development utilities
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info/
	rm -rf htmlcov/ .coverage

# Docker targets
docker-build:
	docker build -t midfreq-trading-system .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database utilities
db-init:
	python scripts/init_database.py

db-migrate:
	python scripts/migrate_database.py

# Setup utilities
setup:
	mkdir -p logs data
	cp config/config.example.yaml config/config.yaml
	@echo "Setup complete. Edit config/config.yaml to customize settings."

# Monitoring utilities
monitor:
	python scripts/monitor_system.py

logs:
	tail -f logs/trading_system.log

# Performance profiling
profile:
	python -m cProfile -o profile.stats src/main.py
	python -m pstats profile.stats

# Documentation
docs:
	cd docs && make html

# Release utilities
version:
	@echo "Current version: $$(python setup.py --version)"

release-check:
	python setup.py check
	python setup.py sdist bdist_wheel
	twine check dist/*

# Backup utilities
backup-config:
	cp config/config.yaml config/config_backup_$$(date +%Y%m%d_%H%M%S).yaml

backup-data:
	tar -czf backup_$$(date +%Y%m%d_%H%M%S).tar.gz data/ logs/ config/