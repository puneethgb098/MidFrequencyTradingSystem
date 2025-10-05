/**
 * Trading System Dashboard JavaScript
 * Handles real-time updates and user interactions
 */

class TradingDashboard {
    constructor() {
        this.socket = io();
        this.performanceChart = null;
        this.performanceData = [];
        this.isConnected = false;
        
        this.initializeElements();
        this.bindEvents();
        this.startRealTimeUpdates();
    }
    
    initializeElements() {
        // Status elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        
        // Performance elements
        this.portfolioValue = document.getElementById('portfolioValue');
        this.totalPnL = document.getElementById('totalPnL');
        this.activePositions = document.getElementById('activePositions');
        this.maxDrawdown = document.getElementById('maxDrawdown');
        
        // Risk elements
        this.var95Progress = document.getElementById('var95Progress');
        this.var95Value = document.getElementById('var95Value');
        this.sharpeProgress = document.getElementById('sharpeProgress');
        this.sharpeValue = document.getElementById('sharpeValue');
        this.betaProgress = document.getElementById('betaProgress');
        this.betaValue = document.getElementById('betaValue');
        
        // Lists
        this.strategiesList = document.getElementById('strategiesList');
        this.positionsList = document.getElementById('positionsList');
        this.recentTrades = document.getElementById('recentTrades');
        this.systemLog = document.getElementById('systemLog');
        
        // Buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
    }
    
    bindEvents() {
        // Socket.IO events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.socket.emit('subscribe_status');
            this.socket.emit('subscribe_performance');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
        });
        
        this.socket.on('status_update', (data) => {
            this.updateStatus(data);
        });
        
        this.socket.on('performance_update', (data) => {
            this.updatePerformance(data);
        });
        
        // Button events
        this.startBtn.addEventListener('click', () => {
            this.startSystem();
        });
        
        this.stopBtn.addEventListener('click', () => {
            this.stopSystem();
        });
        
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('href');
                this.showSection(target);
            });
        });
    }
    
    startRealTimeUpdates() {
        // Fetch initial data
        this.fetchInitialData();
        
        // Set up periodic updates
        setInterval(() => {
            this.fetchStatus();
        }, 5000);
        
        setInterval(() => {
            this.fetchPerformance();
        }, 10000);
    }
    
    async fetchInitialData() {
        try {
            const [statusResponse, performanceResponse, strategiesResponse] = await Promise.all([
                fetch('/api/status'),
                fetch('/api/performance'),
                fetch('/api/strategies')
            ]);
            
            const statusData = await statusResponse.json();
            const performanceData = await performanceResponse.json();
            const strategiesData = await strategiesResponse.json();
            
            this.updateStatus(statusData);
            this.updatePerformance(performanceData);
            this.updateStrategies(strategiesData);
            
        } catch (error) {
            console.error('Error fetching initial data:', error);
            this.addLogEntry('ERROR', 'Failed to fetch initial data');
        }
    }
    
    async fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.updateStatus(data);
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }
    
    async fetchPerformance() {
        try {
            const response = await fetch('/api/performance');
            const data = await response.json();
            this.updatePerformance(data);
        } catch (error) {
            console.error('Error fetching performance:', error);
        }
    }
    
    updateStatus(data) {
        // Update status indicator
        if (data.is_running) {
            this.statusIndicator.className = 'btn btn-success';
            this.statusText.textContent = 'Running';
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
        } else {
            this.statusIndicator.className = 'btn btn-danger';
            this.statusText.textContent = 'Stopped';
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
        }
        
        // Update strategies
        if (data.strategies) {
            this.updateStrategies(data.strategies);
        }
        
        // Update positions
        if (data.risk_metrics && data.risk_metrics.positions) {
            this.updatePositions(data.risk_metrics.positions);
        }
    }
    
    updatePerformance(data) {
        if (!data) return;
        
        // Update portfolio value
        if (data.portfolio_value !== undefined) {
            this.portfolioValue.textContent = this.formatCurrency(data.portfolio_value);
        }
        
        // Update P&L
        const totalPnL = (data.realized_pnl || 0) + (data.unrealized_pnl || 0);
        this.totalPnL.textContent = this.formatCurrency(totalPnL);
        this.totalPnL.className = totalPnL >= 0 ? 'text-success' : 'text-danger';
        
        // Update active positions
        const activePositions = Object.values(data.positions || {}).filter(pos => pos.quantity !== 0).length;
        this.activePositions.textContent = activePositions;
        
        // Update max drawdown
        if (data.max_drawdown !== undefined) {
            this.maxDrawdown.textContent = this.formatPercentage(data.max_drawdown);
        }
        
        // Update risk metrics
        if (data.risk_metrics) {
            this.updateRiskMetrics(data.risk_metrics);
        }
        
        // Update chart
        this.updatePerformanceChart(data);
    }
    
    updateRiskMetrics(riskMetrics) {
        // VaR 95%
        if (riskMetrics.var_95 !== undefined) {
            const var95 = Math.abs(riskMetrics.var_95);
            const var95Percent = Math.min((var95 / 100000) * 100, 100); // Assuming 100k base
            this.var95Progress.style.width = `${var95Percent}%`;
            this.var95Value.textContent = this.formatCurrency(var95);
        }
        
        // Sharpe Ratio
        if (riskMetrics.sharpe_ratio !== undefined) {
            const sharpe = riskMetrics.sharpe_ratio;
            const sharpePercent = Math.min(Math.abs(sharpe) * 20, 100);
            this.sharpeProgress.style.width = `${sharpePercent}%`;
            this.sharpeValue.textContent = sharpe.toFixed(2);
            this.sharpeProgress.className = sharpe >= 0 ? 'progress-bar bg-success' : 'progress-bar bg-danger';
        }
        
        // Portfolio Beta
        if (riskMetrics.portfolio_beta !== undefined) {
            const beta = Math.abs(riskMetrics.portfolio_beta);
            const betaPercent = Math.min(beta * 50, 100);
            this.betaProgress.style.width = `${betaPercent}%`;
            this.betaValue.textContent = riskMetrics.portfolio_beta.toFixed(2);
        }
    }
    
    updateStrategies(strategies) {
        this.strategiesList.innerHTML = '';
        
        Object.entries(strategies).forEach(([name, strategy]) => {
            const strategyCard = document.createElement('div');
            strategyCard.className = `card strategy-card ${strategy.is_running ? 'running' : 'stopped'}`;
            
            strategyCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="card-title mb-1">${name}</h6>
                            <small class="text-muted">${strategy.symbols.join(', ')}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${strategy.is_running ? 'success' : 'danger'}">
                                ${strategy.is_running ? 'Running' : 'Stopped'}
                            </span>
                            <div class="mt-1">
                                <small class="text-muted">
                                    Positions: ${Object.keys(strategy.positions || {}).length}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            this.strategiesList.appendChild(strategyCard);
        });
    }
    
    updatePositions(positions) {
        this.positionsList.innerHTML = '';
        
        Object.entries(positions).forEach(([symbol, position]) => {
            if (position.quantity === 0) return;
            
            const positionCard = document.createElement('div');
            positionCard.className = `card mb-2 ${position.quantity > 0 ? 'position-long' : 'position-short'}`;
            
            const pnl = position.unrealized_pnl || 0;
            const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
            
            positionCard.innerHTML = `
                <div class="card-body py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${symbol}</strong>
                            <br>
                            <small class="text-muted">Qty: ${position.quantity}</small>
                        </div>
                        <div class="text-end">
                            <div class="${pnlClass}">
                                ${this.formatCurrency(pnl)}
                            </div>
                            <small class="text-muted">
                                ${this.formatCurrency(position.market_value || 0)}
                            </small>
                        </div>
                    </div>
                </div>
            `;
            
            this.positionsList.appendChild(positionCard);
        });
        
        if (this.positionsList.children.length === 0) {
            this.positionsList.innerHTML = '<p class="text-muted text-center">No active positions</p>';
        }
    }
    
    updatePerformanceChart(data) {
        if (!this.performanceChart) {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            this.performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
        
        // Add new data point
        const timestamp = new Date().toLocaleTimeString();
        const portfolioValue = data.portfolio_value || 0;
        
        this.performanceChart.data.labels.push(timestamp);
        this.performanceChart.data.datasets[0].data.push(portfolioValue);
        
        // Keep only last 50 data points
        if (this.performanceChart.data.labels.length > 50) {
            this.performanceChart.data.labels.shift();
            this.performanceChart.data.datasets[0].data.shift();
        }
        
        this.performanceChart.update();
    }
    
    async startSystem() {
        try {
            this.addLogEntry('INFO', 'Starting trading system...');
            const response = await fetch('/api/start', { method: 'POST' });
            const result = await response.json();
            
            if (result.status === 'success') {
                this.addLogEntry('SUCCESS', 'Trading system started successfully');
            } else {
                this.addLogEntry('ERROR', `Failed to start system: ${result.message}`);
            }
        } catch (error) {
            console.error('Error starting system:', error);
            this.addLogEntry('ERROR', 'Failed to start trading system');
        }
    }
    
    async stopSystem() {
        try {
            this.addLogEntry('INFO', 'Stopping trading system...');
            const response = await fetch('/api/stop', { method: 'POST' });
            const result = await response.json();
            
            if (result.status === 'success') {
                this.addLogEntry('SUCCESS', 'Trading system stopped successfully');
            } else {
                this.addLogEntry('ERROR', `Failed to stop system: ${result.message}`);
            }
        } catch (error) {
            console.error('Error stopping system:', error);
            this.addLogEntry('ERROR', 'Failed to stop trading system');
        }
    }
    
    addLogEntry(level, message) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level.toLowerCase()}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${message}`;
        
        this.systemLog.appendChild(logEntry);
        
        // Keep only last 50 log entries
        while (this.systemLog.children.length > 50) {
            this.systemLog.removeChild(this.systemLog.firstChild);
        }
        
        // Scroll to bottom
        this.systemLog.scrollTop = this.systemLog.scrollHeight;
    }
    
    showSection(target) {
        // This would handle showing/hiding different sections
        // For now, just log the target
        console.log('Showing section:', target);
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }
    
    formatPercentage(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TradingDashboard();
});