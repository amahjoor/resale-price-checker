import requests
import base64
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import os


class EbayClient:
    """
    eBay Browse API client for fetching market data.
    Handles authentication and rate limiting.
    """
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.getenv('EBAY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('EBAY_CLIENT_SECRET')
        
        self.sandbox = True  # Set to False for production
        
        if self.sandbox:
            self.base_url = "https://api.sandbox.ebay.com"
            self.auth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            self.base_url = "https://api.ebay.com"
            self.auth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            
        self.browse_api_url = f"{self.base_url}/buy/browse/v1"
        
        self._access_token = None
        self._token_expires_at = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
    def search(self, query: str, limit: int = 20, category_ids: Optional[List[str]] = None, 
               condition: Optional[str] = None, price_range: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Search for items on eBay.
        
        Args:
            query: Search query string
            limit: Maximum number of results (max 200)
            category_ids: List of eBay category IDs to filter by
            condition: Item condition filter
            price_range: Price range filter with 'min' and 'max' keys
            
        Returns:
            eBay API response with search results
        """
        if not self.client_id or not self.client_secret:
            # Return mock data for demo purposes when API credentials not available
            return self._get_mock_data(query)
        
        # Ensure we have a valid access token
        self._ensure_valid_token()
        
        # Rate limiting
        self._rate_limit()
        
        # Build search parameters
        params = {
            'q': query,
            'limit': min(limit, 200)
        }
        
        if category_ids:
            params['category_ids'] = ','.join(category_ids)
            
        if condition:
            params['filter'] = f'conditionIds:{{{self._condition_to_id(condition)}}}'
            
        if price_range:
            price_filter = []
            if 'min' in price_range:
                price_filter.append(f'price:[{price_range["min"]}..]')
            if 'max' in price_range:
                if price_filter:
                    price_filter[0] = f'price:[{price_range["min"]}..{price_range["max"]}]'
                else:
                    price_filter.append(f'price:[..{price_range["max"]}]')
            
            if price_filter:
                existing_filter = params.get('filter', '')
                if existing_filter:
                    params['filter'] = f"{existing_filter},{price_filter[0]}"
                else:
                    params['filter'] = price_filter[0]
        
        # Make the request
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        try:
            response = requests.get(f"{self.browse_api_url}/item_summary/search", 
                                 params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"eBay API request failed: {e}")
            # Return mock data as fallback
            return self._get_mock_data(query)
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token."""
        if (not self._access_token or 
            not self._token_expires_at or 
            datetime.now() >= self._token_expires_at):
            self._get_access_token()
    
    def _get_access_token(self):
        """Get OAuth2 access token using client credentials."""
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {auth_header}'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }
        
        response = requests.post(self.auth_url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        self._access_token = token_data['access_token']
        # Set expiration slightly before actual expiration
        expires_in = token_data.get('expires_in', 7200) - 60  
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    def _rate_limit(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    def _condition_to_id(self, condition: str) -> str:
        """Convert condition string to eBay condition ID."""
        condition_map = {
            'new': '1000',
            'new with tags': '1500',
            'new without tags': '1750', 
            'new with defects': '2000',
            'manufacturer refurbished': '2500',
            'seller refurbished': '2750',
            'used': '3000',
            'very good': '4000',
            'good': '5000',
            'acceptable': '6000',
            'for parts': '7000'
        }
        return condition_map.get(condition.lower(), '3000')  # Default to 'used'
    
    def _get_mock_data(self, query: str) -> Dict[str, Any]:
        """Return mock data when API is not available."""
        # Generate realistic mock data based on query
        brand = "Unknown"
        if "chrome hearts" in query.lower():
            brand = "Chrome Hearts"
        elif "supreme" in query.lower():
            brand = "Supreme"
        elif "off white" in query.lower():
            brand = "Off-White"
        
        # Mock items with varied pricing
        mock_items = []
        base_price = 800 if "chrome hearts" in query.lower() else 400
        
        for i in range(5):
            price_variation = base_price + (i * 100) - 200
            mock_items.append({
                'itemId': f'mock_item_{i}_{int(time.time())}',
                'title': f'{brand} {query[:30]} - Size L - Black',
                'price': {
                    'value': str(price_variation),
                    'currency': 'USD'
                },
                'condition': 'Used',
                'itemWebUrl': f'https://ebay.com/itm/mock_item_{i}',
                'seller': {
                    'username': f'seller_{i}',
                    'feedbackPercentage': '99.1'
                },
                'shippingOptions': [{
                    'shippingCost': {'value': '0.00', 'currency': 'USD'},
                    'type': 'FIXED'
                }],
                'image': {
                    'imageUrl': 'https://via.placeholder.com/300x300?text=Mock+Item'
                }
            })
        
        return {
            'itemSummaries': mock_items,
            'total': len(mock_items),
            'limit': 20,
            'offset': 0
        }