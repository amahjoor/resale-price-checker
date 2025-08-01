from typing import Dict, Any
from ..models import EvaluationRequest, EvaluationResponse, ParsedItem
from ..parser import TagParser
from ..currency import CurrencyConverter
from ..market import MarketFetcher
from ..decision import DecisionEngine


class ScannerService:
    """
    Main service orchestrator that coordinates all components
    to provide price comparison and recommendations.
    """
    
    def __init__(self):
        self.parser = TagParser()
        self.currency_converter = CurrencyConverter()
        self.market_fetcher = MarketFetcher()
        self.decision_engine = DecisionEngine()
    
    async def evaluate_item(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Main evaluation pipeline: parse -> normalize -> fetch -> analyze -> decide.
        
        Args:
            request: Evaluation request with raw tag and optional overrides
            
        Returns:
            Complete evaluation response with recommendation
        """
        try:
            # Step 1: Parse the raw tag string
            parsed_item = self.parser.parse(request.raw_tag, request.overrides)
            
            # Step 2: Convert price to USD
            converted_price_usd = self.currency_converter.convert(
                parsed_item.price, 
                parsed_item.currency, 
                'USD'
            )
            
            # Step 3: Fetch market comparables
            market_comparables = self.market_fetcher.fetch_comparables(parsed_item)
            
            # Step 4: Analyze and make decision
            stats, decision = self.decision_engine.analyze(
                parsed_item, 
                converted_price_usd, 
                market_comparables
            )
            
            # Step 5: Build response
            return EvaluationResponse(
                parsed=parsed_item,
                converted_price_usd=converted_price_usd,
                market_comparables=market_comparables,
                stats=stats,
                decision=decision
            )
            
        except Exception as e:
            # Create error response
            error_decision = {
                "verdict": f"Error during evaluation: {str(e)}",
                "confidence": 0.0,
                "reasons": ["Processing failed", str(e)]
            }
            
            # Try to return partial data if parsing succeeded
            try:
                parsed_item = self.parser.parse(request.raw_tag, request.overrides)
                converted_price = self.currency_converter.convert(
                    parsed_item.price, parsed_item.currency, 'USD'
                )
            except:
                # Fallback parsed item
                parsed_item = ParsedItem(
                    title="Parsing failed",
                    price=0.0,
                    currency="USD"
                )
                converted_price = 0.0
            
            from ..models import MarketStats, DecisionResult
            
            return EvaluationResponse(
                parsed=parsed_item,
                converted_price_usd=converted_price,
                market_comparables=[],
                stats=MarketStats(sample_size=0),
                decision=DecisionResult(
                    verdict=error_decision["verdict"],
                    confidence=error_decision["confidence"],
                    reasons=error_decision["reasons"]
                )
            )