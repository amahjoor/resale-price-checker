import re
from typing import Dict, List, Optional, Tuple
from ..models import ParsedItem


class TagParser:
    """
    Parses product tag strings to extract structured metadata.
    Uses rule-based regex patterns and heuristics.
    """
    
    def __init__(self):
        # Brand patterns - common luxury/streetwear brands
        self.brand_patterns = [
            r'\b(chrome hearts?)\b',
            r'\b(supreme)\b',
            r'\b(off[-\s]?white)\b',
            r'\b(nike)\b',
            r'\b(adidas)\b',
            r'\b(jordan)\b',
            r'\b(yeezy)\b',
            r'\b(balenciaga)\b',
            r'\b(gucci)\b',
            r'\b(louis vuitton|lv)\b',
            r'\b(fear of god|fog)\b',
            r'\b(stone island)\b',
            r'\b(bape|a bathing ape)\b',
            r'\b(palace)\b',
            r'\b(travis scott)\b',
            r'\b(kaws)\b'
        ]
        
        # Size patterns
        self.size_patterns = [
            r'size\s*:?\s*([xsmlXSML]+|\d+(?:\.\d+)?)',
            r'\bsize\s+([xsmlXSML]+|\d+(?:\.\d+)?)\b',
            r'\b([xsmlXSML]{1,3})\b(?=\s|$)',
            r'\b(US\s*\d+(?:\.\d+)?|UK\s*\d+(?:\.\d+)?|EU\s*\d+(?:\.\d+)?)\b'
        ]
        
        # Color patterns
        self.color_patterns = [
            r'color\s*:?\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)',
            r'\b(black|white|red|blue|green|yellow|orange|purple|pink|brown|gray|grey|navy|beige|cream|tan|khaki|olive|maroon|burgundy|teal|turquoise|gold|silver)\b'
        ]
        
        # Gender patterns
        self.gender_patterns = [
            r'gender\s*type\s*:?\s*(men\'?s?|women\'?s?|unisex)',
            r'\b(men\'?s?|women\'?s?|unisex|male|female)\b'
        ]
        
        # Price patterns - supports multiple currencies
        self.price_patterns = [
            r'([¥$€£₩])(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Symbol before
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*([¥$€£₩])',  # Symbol after
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(yen|usd|eur|gbp|krw|yuan|dollars?|euros?|pounds?)',  # Word currency
            r'price\s*:?\s*([¥$€£₩]?)(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        # Currency mapping
        self.currency_map = {
            '¥': 'JPY',
            '$': 'USD', 
            '€': 'EUR',
            '£': 'GBP',
            '₩': 'KRW',
            'yen': 'JPY',
            'yuan': 'CNY',
            'usd': 'USD',
            'dollars': 'USD',
            'dollar': 'USD',
            'eur': 'EUR',
            'euros': 'EUR',
            'euro': 'EUR',
            'gbp': 'GBP',
            'pounds': 'GBP',
            'pound': 'GBP',
            'krw': 'KRW'
        }
        
        # Special qualifiers/notes
        self.qualifier_patterns = [
            r'\b(limited(?:\s+edition)?)\b',
            r'\b(exclusive)\b',
            r'\b(rare)\b',
            r'\b(vintage)\b',
            r'\b(deadstock|ds)\b',
            r'\b(new with tags?|nwt)\b',
            r'\b(tax included)\b',
            r'\b(shipping included)\b',
            r'\b(authentic)\b',
            r'\b(sample)\b',
            r'\b(friends\s+and\s+family|f&f)\b'
        ]

    def parse(self, raw_tag: str, overrides: Optional[Dict] = None) -> ParsedItem:
        """
        Parse a raw tag string into structured item data.
        
        Args:
            raw_tag: Raw product description/tag string
            overrides: Optional dictionary to override parsed values
            
        Returns:
            ParsedItem with extracted metadata
        """
        if not raw_tag:
            raise ValueError("Raw tag string cannot be empty")
            
        # Normalize the input
        text = raw_tag.strip()
        text_lower = text.lower()
        
        # Extract components
        brand = self._extract_brand(text_lower)
        size = self._extract_size(text)
        color = self._extract_color(text_lower)
        gender = self._extract_gender(text_lower)
        price, currency = self._extract_price(text)
        notes = self._extract_qualifiers(text_lower)
        
        # Generate title by cleaning up the raw text
        title = self._generate_title(text, brand)
        
        # Apply overrides if provided
        if overrides:
            brand = overrides.get('brand', brand)
            size = overrides.get('size', size)
            color = overrides.get('color', color)
            gender = overrides.get('gender', gender)
            if 'currency' in overrides and overrides['currency']:
                currency = overrides['currency']
            if 'price' in overrides and overrides['price']:
                price = float(overrides['price'])
        
        return ParsedItem(
            title=title,
            brand=brand,
            size=size,
            color=color,
            gender=gender,
            price=price,
            currency=currency,
            notes=notes
        )
    
    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name from text."""
        for pattern in self.brand_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                # Normalize common variations
                brand_lower = brand.lower()
                if 'chrome' in brand_lower:
                    return 'Chrome Hearts'
                elif 'off' in brand_lower and 'white' in brand_lower:
                    return 'Off-White'
                elif 'louis' in brand_lower or 'lv' == brand_lower:
                    return 'Louis Vuitton'
                elif 'fear of god' in brand_lower or 'fog' == brand_lower:
                    return 'Fear of God'
                elif 'stone island' in brand_lower:
                    return 'Stone Island'
                elif 'bape' in brand_lower or 'bathing ape' in brand_lower:
                    return 'BAPE'
                else:
                    return brand.title()
        return None
    
    def _extract_size(self, text: str) -> Optional[str]:
        """Extract size from text."""
        for pattern in self.size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                size = match.group(1).strip().upper()
                # Normalize size formats
                if re.match(r'^[XSML]+$', size):
                    return size
                elif re.match(r'^\d+(\.\d+)?$', size):
                    return size
                elif size.startswith(('US', 'UK', 'EU')):
                    return size
        return None
    
    def _extract_color(self, text: str) -> Optional[str]:
        """Extract color from text."""
        for pattern in self.color_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                color = match.group(1).strip().title()
                return color
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender/target demographic from text."""
        for pattern in self.gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).lower()
                if 'men' in gender:
                    return "Men's"
                elif 'women' in gender:
                    return "Women's"
                elif 'unisex' in gender:
                    return "Unisex"
        return None
    
    def _extract_price(self, text: str) -> Tuple[float, str]:
        """Extract price and currency from text."""
        for pattern in self.price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                # Handle different pattern formats
                if len(groups) == 2:
                    symbol_or_amount, amount_or_symbol = groups
                    
                    # Check if first group is currency symbol
                    if symbol_or_amount in self.currency_map:
                        currency_code = self.currency_map[symbol_or_amount]
                        amount_str = amount_or_symbol
                    # Check if second group is currency
                    elif amount_or_symbol.lower() in self.currency_map:
                        currency_code = self.currency_map[amount_or_symbol.lower()]
                        amount_str = symbol_or_amount
                    else:
                        # Assume first is symbol, second is amount
                        currency_code = self.currency_map.get(symbol_or_amount, 'USD')
                        amount_str = amount_or_symbol
                        
                    # Parse amount
                    try:
                        amount = float(amount_str.replace(',', ''))
                        return amount, currency_code
                    except ValueError:
                        continue
        
        # Default fallback - look for any number that could be a price
        number_matches = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', text)
        if number_matches:
            # Take the largest number as likely price
            amounts = []
            for match in number_matches:
                try:
                    amount = float(match.replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    continue
            
            if amounts:
                max_amount = max(amounts)
                # Heuristic currency detection based on amount ranges
                if max_amount > 10000:
                    currency = 'JPY'  # Japanese Yen (common for high amounts)
                elif max_amount > 1000:
                    currency = 'USD'  # US Dollars
                else:
                    currency = 'USD'  # Default to USD
                
                return max_amount, currency
        
        raise ValueError("Could not extract price from tag string")
    
    def _extract_qualifiers(self, text: str) -> List[str]:
        """Extract special qualifiers and notes."""
        qualifiers = []
        for pattern in self.qualifier_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                qualifier = match.group(1).title()
                if qualifier not in qualifiers:
                    qualifiers.append(qualifier)
        return qualifiers
    
    def _generate_title(self, text: str, brand: Optional[str]) -> str:
        """Generate a clean title from the raw text."""
        # Remove price information
        title = re.sub(r'[¥$€£₩]\d{1,3}(?:,\d{3})*(?:\.\d{2})?', '', text)
        title = re.sub(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*[¥$€£₩]', '', title)
        title = re.sub(r'price\s*:?\s*[¥$€£₩]?\d+(?:,\d+)*(?:\.\d+)?', '', title, flags=re.IGNORECASE)
        
        # Remove metadata labels
        title = re.sub(r'gender\s*type\s*:?\s*\w+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'size\s*:?\s*\w+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'color\s*:?\s*\w+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'tax\s+included', '', title, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and formatting
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'^[:\-\s]+|[:\-\s]+$', '', title)
        
        # Ensure title is reasonable length
        if len(title) > 100:
            title = title[:100].rstrip()
        
        return title or "Unknown Item"