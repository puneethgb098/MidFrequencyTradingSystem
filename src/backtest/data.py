"""
Backtest Data Module

Handles historical data loading and management for backtesting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import yfinance as yf
import logging


class BacktestData:
    """
    Backtest Data Handler
    
    Manages historical market data for backtesting purposes.
    """
    
    def __init__(self, 
                 symbols: List[str], 
                 start_date: datetime, 
                 end_date: datetime,
                 frequency: str = '1min'):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency
        self.logger = logging.getLogger(__name__)
        
        self.data = {}  # symbol -> DataFrame
        self.current_index = 0
        self.total_records = 0
        
    async def load_data(self):
        """
        Load historical data for all symbols
        """
        self.logger.info(f"Loading historical data for {self.symbols}")
        
        for symbol in self.symbols:
            try:
                data = await self._fetch_symbol_data(symbol)
                self.data[symbol] = data
                self.logger.info(f"Loaded {len(data)} records for {symbol}")
            except Exception as e:
                self.logger.error(f"Error loading data for {symbol}: {e}")
                
        # Align data and create combined dataset
        self._align_data()
        
    async def _fetch_symbol_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch historical data for a single symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Use yfinance for demo purposes
            # In production, use a proper data provider
            ticker = yf.Ticker(symbol)
            
            # Determine period based on frequency
            if self.frequency == '1min':
                period = '7d'  # 1-minute data only available for last 7 days
                interval = '1m'
            elif self.frequency == '5min':
                period = '60d'
                interval = '5m'
            elif self.frequency == '1H':
                period = '730d'
                interval = '1h'
            else:  # 1D
                period = 'max'
                interval = '1d'
                
            hist = ticker.history(
                period=period,
                interval=interval,
                start=self.start_date if self.frequency == '1D' else None,
                end=self.end_date if self.frequency == '1D' else None
            )
            
            if hist.empty:
                # Generate synthetic data for testing
                hist = self._generate_synthetic_data(symbol)
            else:
                # Filter by date range
                hist = hist[(hist.index >= self.start_date) & (hist.index <= self.end_date)]
                
            # Reset index to make datetime a column
            hist = hist.reset_index()
            
            # Add symbol column
            hist['symbol'] = symbol
            
            return hist
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            # Return synthetic data as fallback
            return self._generate_synthetic_data(symbol)
            
    def _generate_synthetic_data(self, symbol: str) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data for testing
        
        Args:
            symbol: Trading symbol
            
        Returns:
            DataFrame with synthetic OHLCV data
        """
        self.logger.info(f"Generating synthetic data for {symbol}")
        
        # Generate date range
        if self.frequency == '1min':
            freq = '1min'
            periods = int((self.end_date - self.start_date).total_seconds() / 60)
        elif self.frequency == '5min':
            freq = '5min'
            periods = int((self.end_date - self.start_date).total_seconds() / 300)
        elif self.frequency == '1H':
            freq = '1H'
            periods = int((self.end_date - self.start_date).total_seconds() / 3600)
        else:  # 1D
            freq = '1D'
            periods = (self.end_date - self.start_date).days
            
        dates = pd.date_range(
            start=self.start_date,
            periods=periods,
            freq=freq
        )
        
        # Generate random walk with trend
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
        
        # Base price with some variation per symbol
        base_price = 100 + (hash(symbol) % 50)
        returns = np.random.normal(0.0001, 0.02, len(dates))  # Small positive drift
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
            
        prices = np.array(prices)
        
        # Generate OHLC from prices
        opens = prices.copy()
        highs = prices * (1 + np.abs(np.random.normal(0, 0.01, len(prices))))
        lows = prices * (1 - np.abs(np.random.normal(0, 0.01, len(prices))))
        closes = prices * (1 + np.random.normal(0, 0.005, len(prices)))
        
        # Ensure OHLC relationships
        highs = np.maximum(highs, np.maximum(opens, closes))
        lows = np.minimum(lows, np.minimum(opens, closes))
        
        # Generate volume
        volumes = np.random.randint(1000, 100000, len(dates))
        
        # Create DataFrame
        df = pd.DataFrame({
            'Datetime': dates,
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes,
            'symbol': symbol
        })
        
        df.set_index('Datetime', inplace=True)
        
        return df.reset_index()
        
    def _align_data(self):
        """
        Align data across all symbols and create combined dataset
        """
        if not self.data:
            return
            
        # Find common date range
        common_dates = None
        for symbol, df in self.data.items():
            dates = set(df['Datetime'])
            if common_dates is None:
                common_dates = dates
            else:
                common_dates = common_dates.intersection(dates)
                
        if not common_dates:
            self.logger.warning("No common dates found across symbols")
            return
            
        # Sort dates
        common_dates = sorted(list(common_dates))
        
        # Create combined dataset
        combined_data = []
        
        for date in common_dates:
            row = {'Datetime': date}
            
            for symbol, df in self.data.items():
                symbol_data = df[df['Datetime'] == date].iloc[0]
                
                # Add OHLCV data with symbol prefix
                row[f'{symbol}_open'] = symbol_data['Open']
                row[f'{symbol}_high'] = symbol_data['High']
                row[f'{symbol}_low'] = symbol_data['Low']
                row[f'{symbol}_close'] = symbol_data['Close']
                row[f'{symbol}_volume'] = symbol_data['Volume']
                
            combined_data.append(row)
            
        # Create combined DataFrame
        self.combined_data = pd.DataFrame(combined_data)
        self.combined_data.set_index('Datetime', inplace=True)
        
        self.total_records = len(self.combined_data)
        self.logger.info(f"Aligned data: {self.total_records} records across {len(self.symbols)} symbols")
        
    def get_next_data(self) -> Optional[Dict[str, Any]]:
        """
        Get next data point for backtesting
        
        Returns:
            Dictionary with market data or None if no more data
        """
        if not hasattr(self, 'combined_data') or self.current_index >= self.total_records:
            return None
            
        row = self.combined_data.iloc[self.current_index]
        self.current_index += 1
        
        return row.to_dict()
        
    def get_all_data(self) -> pd.DataFrame:
        """
        Get all historical data
        
        Returns:
            DataFrame with all historical data
        """
        if hasattr(self, 'combined_data'):
            return self.combined_data
        else:
            return pd.DataFrame()
            
    def reset(self):
        """Reset data iterator to beginning"""
        self.current_index = 0
        
    def get_summary(self) -> Dict[str, Any]:
        """Get data summary"""
        return {
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'frequency': self.frequency,
            'total_records': self.total_records,
            'date_range_days': (self.end_date - self.start_date).days
        }
        
    def save_to_csv(self, filename: str):
        """
        Save combined data to CSV file
        
        Args:
            filename: Output filename
        """
        if hasattr(self, 'combined_data'):
            self.combined_data.to_csv(filename)
            self.logger.info(f"Data saved to {filename}")
        else:
            self.logger.error("No data to save")
            
    def load_from_csv(self, filename: str):
        """
        Load data from CSV file
        
        Args:
            filename: Input filename
        """
        try:
            self.combined_data = pd.read_csv(filename, index_col=0, parse_dates=True)
            self.total_records = len(self.combined_data)
            self.logger.info(f"Data loaded from {filename}: {self.total_records} records")
        except Exception as e:
            self.logger.error(f"Error loading data from {filename}: {e}")
            
    def get_data_range(self, start_idx: int, end_idx: int) -> pd.DataFrame:
        """
        Get a subset of the data
        
        Args:
            start_idx: Starting index
            end_idx: Ending index
            
        Returns:
            DataFrame subset
        """
        if hasattr(self, 'combined_data'):
            return self.combined_data.iloc[start_idx:end_idx]
        else:
            return pd.DataFrame()