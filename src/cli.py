#!/usr/bin/env python3
"""
Command-line interface for the Market Price Comparison Scanner.
Useful for testing and batch processing.
"""

import asyncio
import json
import sys
import argparse
from typing import Optional
from .models import EvaluationRequest
from .services import ScannerService


class CLI:
    def __init__(self):
        self.scanner_service = ScannerService()
    
    async def evaluate_tag(self, raw_tag: str, overrides: Optional[dict] = None, 
                          output_format: str = "pretty") -> str:
        """Evaluate a single tag string."""
        request = EvaluationRequest(raw_tag=raw_tag, overrides=overrides or {})
        
        try:
            result = await self.scanner_service.evaluate_item(request)
            
            if output_format == "json":
                return json.dumps(result.dict(), indent=2, default=str)
            else:
                return self._format_pretty_output(result)
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if output_format == "json":
                return json.dumps({"error": error_msg})
            else:
                return error_msg
    
    def _format_pretty_output(self, result) -> str:
        """Format result in human-readable format."""
        lines = []
        lines.append("=" * 60)
        lines.append("MARKET PRICE COMPARISON SCANNER RESULTS")
        lines.append("=" * 60)
        
        # Parsed item info
        lines.append("\n📦 PARSED ITEM:")
        lines.append(f"   Title: {result.parsed.title}")
        if result.parsed.brand:
            lines.append(f"   Brand: {result.parsed.brand}")
        if result.parsed.size:
            lines.append(f"   Size: {result.parsed.size}")
        if result.parsed.color:
            lines.append(f"   Color: {result.parsed.color}")
        if result.parsed.gender:
            lines.append(f"   Gender: {result.parsed.gender}")
        lines.append(f"   Original Price: {result.parsed.price:.2f} {result.parsed.currency}")
        lines.append(f"   USD Equivalent: ${result.converted_price_usd:.2f}")
        if result.parsed.notes:
            lines.append(f"   Notes: {', '.join(result.parsed.notes)}")
        
        # Market analysis
        lines.append(f"\n📊 MARKET ANALYSIS:")
        if result.stats.sample_size > 0:
            lines.append(f"   Sample Size: {result.stats.sample_size} comparables")
            if result.stats.market_median:
                lines.append(f"   Market Median: ${result.stats.market_median:.2f}")
            if result.stats.user_price_vs_median_delta is not None:
                delta_pct = result.stats.user_price_vs_median_delta * 100
                delta_sign = "+" if delta_pct >= 0 else ""
                lines.append(f"   Price vs Market: {delta_sign}{delta_pct:.1f}%")
        else:
            lines.append("   No market data available")
        
        # Decision
        lines.append(f"\n🎯 RECOMMENDATION:")
        lines.append(f"   Verdict: {result.decision.verdict}")
        lines.append(f"   Confidence: {result.decision.confidence:.1%}")
        if result.decision.reasons:
            lines.append("   Reasons:")
            for reason in result.decision.reasons:
                lines.append(f"     • {reason}")
        
        # Market comparables (top 5)
        if result.market_comparables:
            lines.append(f"\n🛒 TOP COMPARABLES:")
            for i, comp in enumerate(result.market_comparables[:5], 1):
                price_display = f"${comp.price:.2f}"
                if comp.fee_adjusted_price and comp.fee_adjusted_price != comp.price:
                    price_display += f" (${comp.fee_adjusted_price:.2f} w/ fees)"
                
                lines.append(f"   {i}. {comp.title[:50]}...")
                lines.append(f"      Source: {comp.source} | Price: {price_display}")
                if comp.condition:
                    lines.append(f"      Condition: {comp.condition}")
                if comp.url:
                    lines.append(f"      URL: {comp.url}")
                lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(
        description="Market Price Comparison Scanner CLI"
    )
    parser.add_argument(
        "tag", 
        help="Product tag string to analyze"
    )
    parser.add_argument(
        "--format", 
        choices=["pretty", "json"], 
        default="pretty",
        help="Output format (default: pretty)"
    )
    parser.add_argument(
        "--brand",
        help="Override detected brand"
    )
    parser.add_argument(
        "--size", 
        help="Override detected size"
    )
    parser.add_argument(
        "--color",
        help="Override detected color"
    )
    parser.add_argument(
        "--currency",
        help="Override detected currency"
    )
    parser.add_argument(
        "--price",
        type=float,
        help="Override detected price"
    )
    
    args = parser.parse_args()
    
    # Build overrides dict
    overrides = {}
    if args.brand:
        overrides["brand"] = args.brand
    if args.size:
        overrides["size"] = args.size
    if args.color:
        overrides["color"] = args.color
    if args.currency:
        overrides["currency"] = args.currency
    if args.price:
        overrides["price"] = args.price
    
    # Run evaluation
    cli = CLI()
    result = await cli.evaluate_tag(args.tag, overrides, args.format)
    print(result)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli \"<tag_string>\"")
        print("Example: python -m src.cli \"Chrome Hearts Tokyo Limited Horse Shoeback Print Hoodie SWTSHRT PLV Gender Type : Men's Size :L Color : Black ¥175,560 tax included\"")
        sys.exit(1)
    
    asyncio.run(main())