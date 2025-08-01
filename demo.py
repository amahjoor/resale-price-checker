#!/usr/bin/env python3
"""
Demo script showing various features of the Market Price Comparison Scanner.
"""

import asyncio
from src.services import ScannerService
from src.models import EvaluationRequest


async def demo():
    print("🛍️  Market Price Comparison Scanner Demo")
    print("=" * 50)
    
    scanner = ScannerService()
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Chrome Hearts Hoodie (High-end Japanese item)",
            "tag": "Chrome Hearts Tokyo Limited Horse Shoeback Print Hoodie SWTSHRT PLV Gender Type : Men's Size :L Color : Black ¥175,560 tax included"
        },
        {
            "name": "Supreme Box Logo (Streetwear classic)",
            "tag": "Supreme Box Logo Hoodie Size L Black Limited Edition $450 deadstock"
        },
        {
            "name": "Off-White Tee (European pricing)",
            "tag": "Off-White Diagonal Stripe Tee Shirt Men's Size M White Color €320 authentic"
        },
        {
            "name": "Jordan Sneakers (US pricing)",
            "tag": "Air Jordan 1 Retro High OG Chicago Size US 9 Men's Red White Black $170 new with box"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            request = EvaluationRequest(raw_tag=test_case['tag'])
            result = await scanner.evaluate_item(request)
            
            # Display key results
            print(f"📦 Item: {result.parsed.brand} - {result.parsed.title[:40]}...")
            print(f"💰 Price: {result.parsed.price:.2f} {result.parsed.currency} (${result.converted_price_usd:.2f} USD)")
            
            if result.parsed.size:
                print(f"📏 Size: {result.parsed.size}")
            if result.parsed.color:
                print(f"🎨 Color: {result.parsed.color}")
            if result.parsed.notes:
                print(f"📝 Notes: {', '.join(result.parsed.notes)}")
            
            print(f"📊 Market Data: {result.stats.sample_size} comparables")
            if result.stats.market_median:
                print(f"📈 Market Median: ${result.stats.market_median:.2f}")
                if result.stats.user_price_vs_median_delta is not None:
                    delta_pct = result.stats.user_price_vs_median_delta * 100
                    print(f"📉 Price vs Market: {delta_pct:+.1f}%")
            
            print(f"🎯 Recommendation: {result.decision.verdict}")
            print(f"🎲 Confidence: {result.decision.confidence:.1%}")
            
            if result.decision.reasons:
                print("💭 Reasons:")
                for reason in result.decision.reasons[:3]:  # Show top 3 reasons
                    print(f"   • {reason}")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    print("🚀 Demo complete! The scanner is ready for real-world use.")
    print("\n📚 Next steps:")
    print("   • Add real eBay API credentials for live market data")
    print("   • Integrate OCR for image-based tag scanning") 
    print("   • Add more market sources (StockX, Grailed, etc.)")
    print("   • Build a web/mobile interface")


if __name__ == "__main__":
    asyncio.run(demo())