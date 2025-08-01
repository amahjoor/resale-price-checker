import requests
import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class CurrencyConverter:
    """
    Handles currency conversion using live exchange rates.
    Caches rates to avoid excessive API calls.
    """
    
    def __init__(self, cache_ttl: int = 300):  # 5 minutes default cache
        self.cache_ttl = cache_ttl
        self._rates_cache: Dict[str, float] = {}
        self._cache_timestamp: Optional[datetime] = None
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.fallback_url = "https://api.exchangerate.host/latest"
        
        # Fallback rates (approximate, for offline scenarios)
        self.fallback_rates = {
            'USD': 1.0,
            'JPY': 150.0,
            'EUR': 0.85,
            'GBP': 0.73,
            'KRW': 1300.0,
            'CNY': 7.2,
            'CAD': 1.35,
            'AUD': 1.52
        }
    
    def convert(self, amount: float, from_currency: str, to_currency: str = 'USD') -> float:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'JPY')
            to_currency: Target currency code (default: 'USD')
            
        Returns:
            Converted amount in target currency
        """
        if from_currency == to_currency:
            return amount
            
        # Get exchange rates
        rates = self._get_rates()
        
        # Convert via USD as base
        if from_currency != 'USD':
            if from_currency not in rates:
                raise ValueError(f"Unsupported currency: {from_currency}")
            # Convert to USD first
            usd_amount = amount / rates[from_currency]
        else:
            usd_amount = amount
            
        # Convert from USD to target currency
        if to_currency != 'USD':
            if to_currency not in rates:
                raise ValueError(f"Unsupported currency: {to_currency}")
            return usd_amount * rates[to_currency]
        else:
            return usd_amount
    
    def _get_rates(self) -> Dict[str, float]:
        """Get current exchange rates, using cache if valid."""
        # Check if cache is still valid
        if (self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < timedelta(seconds=self.cache_ttl) and
            self._rates_cache):
            return self._rates_cache
        
        # Try to fetch fresh rates
        try:
            rates = self._fetch_rates()
            self._rates_cache = rates
            self._cache_timestamp = datetime.now()
            return rates
        except Exception as e:
            print(f"Failed to fetch live rates: {e}")
            # Fall back to cached rates if available
            if self._rates_cache:
                print("Using cached exchange rates")
                return self._rates_cache
            else:
                print("Using fallback exchange rates")
                return self.fallback_rates
    
    def _fetch_rates(self) -> Dict[str, float]:
        """Fetch live exchange rates from API."""
        # Try primary API first
        try:
            response = requests.get(f"{self.base_url}/USD", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data['rates']
        except Exception:
            pass
        
        # Try fallback API
        try:
            response = requests.get(f"{self.fallback_url}?base=USD", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data['rates']
        except Exception as e:
            raise Exception(f"Failed to fetch exchange rates from all sources: {e}")
    
    def get_supported_currencies(self) -> list:
        """Get list of supported currency codes."""
        rates = self._get_rates()
        return list(rates.keys())
    
    def clear_cache(self):
        """Clear the exchange rate cache."""
        self._rates_cache.clear()
        self._cache_timestamp = None