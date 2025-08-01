import statistics
from typing import List, Tuple
from ..models import ParsedItem, MarketComparable, MarketStats, DecisionResult, Decision


class DecisionEngine:
    """
    Analyzes market data and provides buy/pass recommendations.
    Uses heuristic-based decision making with confidence scoring.
    """
    
    def __init__(self):
        # Decision thresholds (as percentages below market price)
        self.strong_cop_threshold = -0.15  # 15% below market
        self.cop_threshold = -0.05         # 5% below market  
        self.fair_threshold = 0.05         # Within 5% of market
        self.pass_threshold = 0.05         # 5% above market
        
        # Confidence factors
        self.min_sample_size = 3
        self.preferred_sample_size = 8
        
    def analyze(self, item: ParsedItem, user_price_usd: float, 
                comparables: List[MarketComparable]) -> Tuple[MarketStats, DecisionResult]:
        """
        Analyze market data and provide recommendation.
        
        Args:
            item: Parsed item information
            user_price_usd: User's price converted to USD
            comparables: List of market comparables
            
        Returns:
            Tuple of market statistics and decision result
        """
        # Calculate market statistics
        stats = self._calculate_stats(user_price_usd, comparables)
        
        # Make decision
        decision = self._make_decision(item, user_price_usd, stats, comparables)
        
        return stats, decision
    
    def _calculate_stats(self, user_price_usd: float, comparables: List[MarketComparable]) -> MarketStats:
        """Calculate market statistics from comparables."""
        if not comparables:
            return MarketStats(sample_size=0)
        
        # Extract prices (use fee-adjusted when available)
        prices = []
        for comp in comparables:
            price = comp.fee_adjusted_price if comp.fee_adjusted_price else comp.price
            # Convert to USD if needed (for now assume all are USD from eBay)
            prices.append(price)
        
        if not prices:
            return MarketStats(sample_size=0)
        
        # Calculate statistics
        market_median = statistics.median(prices)
        adjusted_market_price = market_median  # Could add further adjustments here
        
        # Calculate user price vs market delta
        user_price_vs_median_delta = None
        if market_median > 0:
            user_price_vs_median_delta = (user_price_usd - market_median) / market_median
        
        return MarketStats(
            market_median=market_median,
            adjusted_market_price=adjusted_market_price,
            user_price_vs_median_delta=user_price_vs_median_delta,
            sample_size=len(prices)
        )
    
    def _make_decision(self, item: ParsedItem, user_price_usd: float, 
                      stats: MarketStats, comparables: List[MarketComparable]) -> DecisionResult:
        """Make buy/pass decision based on analysis."""
        reasons = []
        base_confidence = 0.5
        
        # Handle no market data case
        if stats.sample_size == 0:
            return DecisionResult(
                verdict="Insufficient market data - proceed with caution",
                confidence=0.1,
                reasons=["No comparable listings found", "Unable to assess market value"]
            )
        
        # Handle insufficient market data
        if stats.sample_size < self.min_sample_size:
            base_confidence *= 0.6
            reasons.append(f"Limited market data ({stats.sample_size} comparables)")
        
        # Main decision logic based on price delta
        delta = stats.user_price_vs_median_delta
        if delta is None:
            return DecisionResult(
                verdict="Unable to calculate price comparison",
                confidence=0.2,
                reasons=["Market price calculation failed"]
            )
        
        # Base decision on price delta
        if delta <= self.strong_cop_threshold:
            verdict = "Strong Cop - Excellent deal if authentic"
            base_confidence += 0.3
            reasons.append(f"User price is {abs(delta):.1%} below market median")
        elif delta <= self.cop_threshold:
            verdict = "Cop - Good deal, verify authenticity and condition"
            base_confidence += 0.2
            reasons.append(f"User price is {abs(delta):.1%} below market median")
        elif abs(delta) <= self.fair_threshold:
            verdict = "Fair price - consider rarity and condition"
            reasons.append(f"User price is within {abs(delta):.1%} of market median")
        else:
            verdict = "Pass - Price above market value"
            base_confidence += 0.1
            reasons.append(f"User price is {delta:.1%} above market median")
        
        # Adjust confidence based on various factors
        confidence_adjustments = []
        
        # Sample size confidence
        if stats.sample_size >= self.preferred_sample_size:
            confidence_adjustments.append(0.1)
        elif stats.sample_size < self.min_sample_size:
            confidence_adjustments.append(-0.2)
        
        # Rarity/exclusivity modifiers
        rarity_bonus = self._assess_rarity(item)
        if rarity_bonus > 0:
            confidence_adjustments.append(rarity_bonus * 0.1)
            reasons.append(f"Item appears to be limited/exclusive")
        
        # Condition consistency check
        condition_penalty = self._assess_condition_consistency(comparables)
        if condition_penalty > 0:
            confidence_adjustments.append(-condition_penalty * 0.1)
            reasons.append("Mixed conditions in comparables - verify item condition")
        
        # Price spread analysis
        price_spread_penalty = self._assess_price_spread(comparables)
        if price_spread_penalty > 0:
            confidence_adjustments.append(-price_spread_penalty * 0.1)
            reasons.append("High price variance in market data")
        
        # Calculate final confidence
        final_confidence = base_confidence + sum(confidence_adjustments)
        final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to [0, 1]
        
        # Add market context
        if stats.market_median:
            reasons.append(f"Market median: ${stats.market_median:.2f}")
        
        return DecisionResult(
            verdict=verdict,
            confidence=final_confidence,
            reasons=reasons
        )
    
    def _assess_rarity(self, item: ParsedItem) -> float:
        """Assess item rarity based on notes and metadata."""
        rarity_score = 0.0
        
        rarity_keywords = {
            'limited': 0.8,
            'exclusive': 0.7,
            'sample': 1.0,
            'friends and family': 0.9,
            'f&f': 0.9,
            'deadstock': 0.3,
            'vintage': 0.4,
            'rare': 0.6
        }
        
        # Check notes for rarity indicators
        for note in item.notes:
            note_lower = note.lower()
            for keyword, score in rarity_keywords.items():
                if keyword in note_lower:
                    rarity_score = max(rarity_score, score)
        
        # Check title for rarity indicators
        title_lower = item.title.lower()
        for keyword, score in rarity_keywords.items():
            if keyword in title_lower:
                rarity_score = max(rarity_score, score * 0.8)  # Slightly lower confidence from title
        
        return rarity_score
    
    def _assess_condition_consistency(self, comparables: List[MarketComparable]) -> float:
        """Assess consistency of conditions in comparables."""
        if len(comparables) < 2:
            return 0.0
        
        conditions = [comp.condition for comp in comparables if comp.condition]
        if not conditions:
            return 0.3  # No condition info is concerning
        
        # Check for mixed conditions
        unique_conditions = set(conditions)
        if len(unique_conditions) > 2:
            return 0.5  # High variance in conditions
        elif len(unique_conditions) == 2:
            return 0.2  # Some variance
        else:
            return 0.0  # Consistent conditions
    
    def _assess_price_spread(self, comparables: List[MarketComparable]) -> float:
        """Assess price spread/variance in comparables."""
        if len(comparables) < 3:
            return 0.0
        
        prices = []
        for comp in comparables:
            price = comp.fee_adjusted_price if comp.fee_adjusted_price else comp.price
            prices.append(price)
        
        if not prices:
            return 0.0
        
        # Calculate coefficient of variation
        mean_price = statistics.mean(prices)
        if mean_price == 0:
            return 0.0
        
        try:
            std_dev = statistics.stdev(prices)
            cv = std_dev / mean_price
            
            # Return penalty based on coefficient of variation
            if cv > 0.4:  # Very high variance
                return 0.8
            elif cv > 0.25:  # High variance
                return 0.5
            elif cv > 0.15:  # Moderate variance
                return 0.2
            else:
                return 0.0  # Low variance
        except statistics.StatisticsError:
            return 0.1  # Some penalty for calculation issues