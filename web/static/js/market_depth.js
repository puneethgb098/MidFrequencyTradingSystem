class MarketDepthViewer {
    constructor() {
        this.socket = io();
        this.priceChart = null;
        this.currentInstrument = null;
        this.autoRefresh = false;
        this.priceData = {
            timestamps: [],
            bidPrices: [],
            askPrices: [],
            lastPrices: []
        };

        this.initializeElements();
        this.bindEvents();
        this.setupChart();
    }

    initializeElements() {
        this.instrumentTokenInput = document.getElementById('instrumentToken');
        this.loadBtn = document.getElementById('loadBtn');
        this.toggleAutoRefreshBtn = document.getElementById('toggleAutoRefresh');
        this.orderBookContainer = document.getElementById('orderBookContainer');
        this.currentInstrumentSpan = document.getElementById('currentInstrument');

        this.lastPriceEl = document.getElementById('lastPrice');
        this.spreadEl = document.getElementById('spread');
        this.spreadPctEl = document.getElementById('spreadPct');
        this.imbalanceBarEl = document.getElementById('imbalanceBar');
        this.imbalanceValueEl = document.getElementById('imbalanceValue');
        this.volumeEl = document.getElementById('volume');
        this.totalBidQtyEl = document.getElementById('totalBidQty');
        this.totalAskQtyEl = document.getElementById('totalAskQty');
        this.depthLevelEl = document.getElementById('depthLevel');
        this.lastUpdateEl = document.getElementById('lastUpdate');
    }

    bindEvents() {
        this.loadBtn.addEventListener('click', () => {
            this.loadOrderBook();
        });

        this.toggleAutoRefreshBtn.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });

        this.instrumentTokenInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadOrderBook();
            }
        });

        this.socket.on('order_book_update', (data) => {
            this.updateOrderBook(data);
        });

        this.socket.on('price_update', (data) => {
            this.updatePriceChart(data);
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.showError(data.message);
        });
    }

    setupChart() {
        const ctx = document.getElementById('priceChart').getContext('2d');
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Bid Price',
                        data: [],
                        borderColor: 'rgba(76, 175, 80, 1)',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: 'Ask Price',
                        data: [],
                        borderColor: 'rgba(244, 67, 54, 1)',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: 'Last Price',
                        data: [],
                        borderColor: 'rgba(33, 150, 243, 1)',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    async loadOrderBook() {
        const token = parseInt(this.instrumentTokenInput.value);
        if (!token) {
            this.showError('Please enter a valid instrument token');
            return;
        }

        this.currentInstrument = token;
        this.currentInstrumentSpan.textContent = `Token: ${token}`;

        try {
            const response = await fetch(`/api/order_book/${token}`);
            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.updateOrderBook(data);

            await this.loadPriceHistory(token);

        } catch (error) {
            console.error('Error loading order book:', error);
            this.showError('Failed to load order book');
        }
    }

    async loadPriceHistory(token) {
        try {
            const response = await fetch(`/api/price_history/${token}?count=50`);
            const data = await response.json();

            if (data.error) {
                return;
            }

            this.priceData.timestamps = data.timestamps.map(ts =>
                new Date(ts).toLocaleTimeString()
            );
            this.priceData.bidPrices = data.bid_prices;
            this.priceData.askPrices = data.ask_prices;
            this.priceData.lastPrices = data.last_prices;

            this.refreshChart();

        } catch (error) {
            console.error('Error loading price history:', error);
        }
    }

    updateOrderBook(data) {
        this.updateMetrics(data);
        this.renderOrderBook(data);
    }

    updateMetrics(data) {
        this.lastPriceEl.textContent = this.formatPrice(data.last_price);
        this.spreadEl.textContent = this.formatPrice(data.spread);
        this.spreadPctEl.textContent = `(${data.spread_pct.toFixed(3)}%)`;
        this.volumeEl.textContent = this.formatNumber(data.volume);
        this.depthLevelEl.textContent = `Level ${data.depth_level}`;

        const totalBidQty = data.bids.reduce((sum, bid) => sum + bid.quantity, 0);
        const totalAskQty = data.asks.reduce((sum, ask) => sum + ask.quantity, 0);
        this.totalBidQtyEl.textContent = this.formatNumber(totalBidQty);
        this.totalAskQtyEl.textContent = this.formatNumber(totalAskQty);

        const imbalance = data.imbalance;
        const imbalancePct = ((imbalance + 1) / 2) * 100;
        this.imbalanceBarEl.style.width = `${imbalancePct}%`;

        if (imbalance > 0) {
            this.imbalanceBarEl.className = 'progress-bar bg-success';
            this.imbalanceValueEl.innerHTML = `<span class="imbalance-positive">+${(imbalance * 100).toFixed(2)}% (Bid pressure)</span>`;
        } else {
            this.imbalanceBarEl.className = 'progress-bar bg-danger';
            this.imbalanceValueEl.innerHTML = `<span class="imbalance-negative">${(imbalance * 100).toFixed(2)}% (Ask pressure)</span>`;
        }

        this.lastUpdateEl.textContent = new Date(data.timestamp).toLocaleString();
    }

    renderOrderBook(data) {
        const maxBidQty = Math.max(...data.bids.map(b => b.quantity), 1);
        const maxAskQty = Math.max(...data.asks.map(a => a.quantity), 1);

        let html = `
            <div class="table-responsive">
                <table class="table order-book-table table-sm">
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Bid Qty</th>
                            <th>Bid Price</th>
                            <th>Cumulative</th>
                            <th style="width: 100px;">Depth</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.bids.forEach((bid, index) => {
            const depthPct = (bid.quantity / maxBidQty) * 100;
            html += `
                <tr class="bid-row level-${bid.level}">
                    <td class="text-center">${bid.level}</td>
                    <td>${this.formatNumber(bid.quantity)}</td>
                    <td><strong>${this.formatPrice(bid.price)}</strong></td>
                    <td class="text-muted">${this.formatNumber(bid.cumulative)}</td>
                    <td>
                        <div style="position: relative; height: 20px;">
                            <div class="depth-bar depth-bar-bid" style="width: ${depthPct}%; height: 100%;"></div>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>

                <div class="spread-info text-center">
                    <strong>SPREAD:</strong> ${this.formatPrice(data.spread)} (${data.spread_pct.toFixed(3)}%)
                </div>

                <table class="table order-book-table table-sm">
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Ask Price</th>
                            <th>Ask Qty</th>
                            <th>Cumulative</th>
                            <th style="width: 100px;">Depth</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.asks.forEach((ask, index) => {
            const depthPct = (ask.quantity / maxAskQty) * 100;
            html += `
                <tr class="ask-row level-${ask.level}">
                    <td class="text-center">${ask.level}</td>
                    <td><strong>${this.formatPrice(ask.price)}</strong></td>
                    <td>${this.formatNumber(ask.quantity)}</td>
                    <td class="text-muted">${this.formatNumber(ask.cumulative)}</td>
                    <td>
                        <div style="position: relative; height: 20px;">
                            <div class="depth-bar depth-bar-ask" style="width: ${depthPct}%; height: 100%;"></div>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        this.orderBookContainer.innerHTML = html;
    }

    updatePriceChart(data) {
        const timestamp = new Date(data.timestamp).toLocaleTimeString();

        this.priceData.timestamps.push(timestamp);
        this.priceData.bidPrices.push(data.bid_price);
        this.priceData.askPrices.push(data.ask_price);
        this.priceData.lastPrices.push(data.last_price);

        if (this.priceData.timestamps.length > 50) {
            this.priceData.timestamps.shift();
            this.priceData.bidPrices.shift();
            this.priceData.askPrices.shift();
            this.priceData.lastPrices.shift();
        }

        this.refreshChart();
    }

    refreshChart() {
        this.priceChart.data.labels = this.priceData.timestamps;
        this.priceChart.data.datasets[0].data = this.priceData.bidPrices;
        this.priceChart.data.datasets[1].data = this.priceData.askPrices;
        this.priceChart.data.datasets[2].data = this.priceData.lastPrices;
        this.priceChart.update('none');
    }

    toggleAutoRefresh() {
        this.autoRefresh = !this.autoRefresh;

        if (this.autoRefresh) {
            if (!this.currentInstrument) {
                this.showError('Please load an instrument first');
                this.autoRefresh = false;
                return;
            }

            this.toggleAutoRefreshBtn.innerHTML = '<i class="fas fa-pause"></i> Stop Auto Refresh';
            this.toggleAutoRefreshBtn.className = 'btn btn-warning w-100';

            this.socket.emit('subscribe_order_book', {
                instrument_token: this.currentInstrument
            });

            this.socket.emit('subscribe_price_chart', {
                instrument_token: this.currentInstrument
            });

        } else {
            this.toggleAutoRefreshBtn.innerHTML = '<i class="fas fa-play"></i> Auto Refresh';
            this.toggleAutoRefreshBtn.className = 'btn btn-success w-100';
        }
    }

    formatPrice(price) {
        return parseFloat(price).toFixed(2);
    }

    formatNumber(num) {
        return num.toLocaleString();
    }

    showError(message) {
        alert(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.marketDepthViewer = new MarketDepthViewer();
});
