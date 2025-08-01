import pytest
from src.currency import CurrencyConverter


class TestCurrencyConverter:
    def setup_method(self):
        self.converter = CurrencyConverter()
    
    def test_same_currency_conversion(self):
        """Test conversion between same currencies."""
        result = self.converter.convert(100, 'USD', 'USD')
        assert result == 100.0
    
    def test_fallback_rates(self):
        """Test that fallback rates work when API is unavailable."""
        # Clear cache to force fallback
        self.converter.clear_cache()
        
        # This should work even without API
        result = self.converter.convert(100, 'USD', 'JPY')
        assert result > 0
        
        # Test reverse conversion
        result = self.converter.convert(15000, 'JPY', 'USD')
        assert result > 0 and result < 200  # Should be reasonable
    
    def test_unsupported_currency(self):
        """Test error handling for unsupported currencies."""
        with pytest.raises(ValueError):
            self.converter.convert(100, 'INVALID', 'USD')
    
    def test_cache_functionality(self):
        """Test that caching works properly."""
        # First call should populate cache
        result1 = self.converter.convert(100, 'USD', 'EUR')
        
        # Second call should use cache (same result)
        result2 = self.converter.convert(100, 'USD', 'EUR')
        
        assert result1 == result2
    
    def test_supported_currencies(self):
        """Test that we can get supported currencies list."""
        currencies = self.converter.get_supported_currencies()
        assert isinstance(currencies, list)
        assert 'USD' in currencies
        assert 'EUR' in currencies
        assert 'JPY' in currencies