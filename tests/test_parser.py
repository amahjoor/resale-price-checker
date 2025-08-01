import pytest
from src.parser import TagParser


class TestTagParser:
    def setup_method(self):
        self.parser = TagParser()
    
    def test_chrome_hearts_example(self):
        """Test parsing the Chrome Hearts example from the spec."""
        tag = "Chrome Hearts Tokyo Limited Horse Shoeback Print Hoodie SWTSHRT PLV Gender Type : Men's Size :L Color : Black ¥175,560 tax included"
        
        result = self.parser.parse(tag)
        
        assert result.brand == "Chrome Hearts"
        assert result.size == "L"
        assert result.color == "Black"
        assert result.gender == "Men's"
        assert result.price == 175560
        assert result.currency == "JPY"
        assert "Limited" in result.notes
        assert "Tax Included" in result.notes
        assert "Tokyo" in result.title
        assert "Hoodie" in result.title
    
    def test_price_extraction_variants(self):
        """Test different price formats."""
        test_cases = [
            ("Supreme Box Logo Hoodie $450", 450.0, "USD"),
            ("Off-White Tee 350€", 350.0, "EUR"),
            ("Yeezy 350 £200", 200.0, "GBP"),
            ("Jordan 1 ₩250,000", 250000.0, "KRW"),
            ("Price: $1,200.50", 1200.50, "USD"),
        ]
        
        for tag, expected_price, expected_currency in test_cases:
            result = self.parser.parse(tag)
            assert result.price == expected_price
            assert result.currency == expected_currency
    
    def test_size_extraction(self):
        """Test size extraction variations."""
        test_cases = [
            ("Nike Shirt Size: M", "M"),
            ("Adidas Hoodie size L", "L"),
            ("Supreme Tee XL", "XL"),
            ("Jordan 1 US 9.5", "US 9.5"),
            ("Balenciaga UK 8", "UK 8"),
        ]
        
        for tag, expected_size in test_cases:
            result = self.parser.parse(tag + " $100")  # Add price to make parsing work
            assert result.size == expected_size
    
    def test_brand_normalization(self):
        """Test brand name normalization."""
        test_cases = [
            ("chrome hearts tee $100", "Chrome Hearts"),
            ("off-white shirt $200", "Off-White"),
            ("OFF WHITE hoodie $300", "Off-White"),
            ("louis vuitton bag $1000", "Louis Vuitton"),
            ("LV wallet $500", "Louis Vuitton"),
        ]
        
        for tag, expected_brand in test_cases:
            result = self.parser.parse(tag)
            assert result.brand == expected_brand
    
    def test_overrides(self):
        """Test override functionality."""
        tag = "Unknown Brand Tee $50"
        overrides = {
            "brand": "Supreme",
            "size": "L",
            "color": "Red"
        }
        
        result = self.parser.parse(tag, overrides)
        
        assert result.brand == "Supreme"
        assert result.size == "L"
        assert result.color == "Red"
        assert result.price == 50.0
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            self.parser.parse("")
        
        with pytest.raises(ValueError):
            self.parser.parse("No price here")
    
    def test_qualifiers_extraction(self):
        """Test extraction of special qualifiers."""
        tag = "Supreme Box Logo Limited Edition Deadstock Vintage $500"
        result = self.parser.parse(tag)
        
        assert "Limited Edition" in result.notes
        assert "Deadstock" in result.notes
        assert "Vintage" in result.notes
        assert "Archive" in result.notes