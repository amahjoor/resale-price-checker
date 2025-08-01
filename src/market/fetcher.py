from typing import List, Dict, Optional, Any
from ..models import ParsedItem, MarketComparable
from .ebay_client import EbayClient


class MarketFetcher:
    """
    Orchestrates fetching market data from multiple sources.
    Currently supports eBay, with extensibility for other platforms.
    """
    
    def __init__(self):
        self.ebay_client = EbayClient()
        # Future: Add StockX, Grailed, etc. clients here
        
    def fetch_comparables(self, item: ParsedItem, limit: int = 20) -> List[MarketComparable]:
        """
        Fetch comparable market listings for the given item.
        
        Args:
            item: Parsed item to find comparables for
            limit: Maximum number of comparables to fetch
            
        Returns:
            List of comparable market listings
        """
        comparables = []
        
        # Fetch from eBay
        try:
            ebay_comparables = self._fetch_from_ebay(item, limit)
            comparables.extend(ebay_comparables)
        except Exception as e:
            print(f"Failed to fetch eBay comparables: {e}")
        
        # Future: Add other sources
        # try:
        #     stockx_comparables = self._fetch_from_stockx(item, limit)
        #     comparables.extend(stockx_comparables)
        # except Exception as e:
        #     print(f"Failed to fetch StockX comparables: {e}")
        
        return comparables[:limit]  # Limit total results
    
    def _fetch_from_ebay(self, item: ParsedItem, limit: int) -> List[MarketComparable]:
        """Fetch comparables from eBay."""
        # Build search query
        query_parts = []
        
        if item.brand:
            query_parts.append(item.brand)
        
        # Use title keywords, but clean up
        title_words = item.title.split()
        # Filter out common noise words and take first few meaningful words
        meaningful_words = []
        noise_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        for word in title_words:
            if len(meaningful_words) >= 4:  # Limit query length
                break
            if word.lower() not in noise_words and len(word) > 2:
                meaningful_words.append(word)
        
        query_parts.extend(meaningful_words)
        
        if item.size:
            query_parts.append(f"size {item.size}")
        
        query = " ".join(query_parts)
        
        # Search eBay
        response = self.ebay_client.search(query, limit=limit)
        
        # Parse response into MarketComparable objects
        comparables = []
        items = response.get('itemSummaries', [])
        
        for ebay_item in items:
            try:
                comparable = self._parse_ebay_item(ebay_item)
                comparables.append(comparable)
            except Exception as e:
                print(f"Failed to parse eBay item: {e}")
                continue
        
        return comparables
    
    def _parse_ebay_item(self, ebay_item: Dict[str, Any]) -> MarketComparable:
        """Parse eBay API response item into MarketComparable."""
        # Extract price
        price_info = ebay_item.get('price', {})
        price = float(price_info.get('value', 0))
        currency = price_info.get('currency', 'USD')
        
        # Calculate fee-adjusted price (eBay + PayPal fees ~10-13%)
        fee_rate = 0.115  # Approximate combined fees
        fee_adjusted_price = price * (1 + fee_rate)
        
        # Extract condition
        condition = ebay_item.get('condition', 'Unknown')
        
        # Extract shipping cost
        shipping_cost = 0
        shipping_options = ebay_item.get('shippingOptions', [])
        if shipping_options:
            shipping_info = shipping_options[0].get('shippingCost', {})
            try:
                shipping_cost = float(shipping_info.get('value', 0))
            except (ValueError, TypeError):
                shipping_cost = 0
        
        # Adjust price for shipping
        total_price = price + shipping_cost
        fee_adjusted_total = total_price * (1 + fee_rate)
        
        return MarketComparable(
            source="eBay",
            title=ebay_item.get('title', 'Unknown Item'),
            price=total_price,
            currency=currency,
            condition=condition,
            fee_adjusted_price=fee_adjusted_total,
            url=ebay_item.get('itemWebUrl'),
            metadata={
                'item_id': ebay_item.get('itemId'),
                'seller': ebay_item.get('seller', {}).get('username'),
                'seller_feedback': ebay_item.get('seller', {}).get('feedbackPercentage'),
                'shipping_cost': shipping_cost,
                'image_url': ebay_item.get('image', {}).get('imageUrl')
            }
        )
    
    # Future methods for other platforms
    def _fetch_from_stockx(self, item: ParsedItem, limit: int) -> List[MarketComparable]:
        """Fetch comparables from StockX (placeholder)."""
        # TODO: Implement StockX integration
        return []
    
    def _fetch_from_grailed(self, item: ParsedItem, limit: int) -> List[MarketComparable]:
        """Fetch comparables from Grailed (placeholder)."""  
        # TODO: Implement Grailed integration
        return []