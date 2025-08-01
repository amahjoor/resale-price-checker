from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from ..models import EvaluationRequest, EvaluationResponse
from ..services import ScannerService

# Create FastAPI app
app = FastAPI(
    title="Market Price Comparison Scanner",
    description="API for analyzing clothing/item prices against market data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
scanner_service = ScannerService()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Market Price Comparison Scanner",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    # Test currency converter
    try:
        from ..currency import CurrencyConverter
        converter = CurrencyConverter()
        test_conversion = converter.convert(100, 'USD', 'USD')
        currency_status = "ok"
    except Exception as e:
        currency_status = f"error: {str(e)}"
    
    # Test eBay connection (basic)
    try:
        from ..market import EbayClient
        ebay_client = EbayClient()
        # Just check if client initializes
        ebay_status = "ok" if ebay_client else "error"  
    except Exception as e:
        ebay_status = f"error: {str(e)}"
    
    return {
        "status": "online",
        "components": {
            "currency_converter": currency_status,
            "ebay_client": ebay_status,
            "parser": "ok",
            "decision_engine": "ok"
        }
    }


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_item(request: EvaluationRequest):
    """
    Evaluate an item based on its tag description.
    
    This endpoint parses the tag, normalizes the price, fetches market data,
    and provides a buy/pass recommendation with confidence scoring.
    """
    try:
        result = await scanner_service.evaluate_item(request)
        return result
    except ValueError as e:
        # Handle validation/parsing errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/parse-only")
async def parse_only(request: dict):
    """
    Parse tag string only, without market analysis.
    Useful for testing the parser component.
    """
    raw_tag = request.get("raw_tag")
    if not raw_tag:
        raise HTTPException(status_code=400, detail="raw_tag is required")
    
    try:
        from ..parser import TagParser
        parser = TagParser()
        parsed = parser.parse(raw_tag, request.get("overrides"))
        return {"parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/currencies")
async def get_supported_currencies():
    """Get list of supported currencies."""
    try:
        from ..currency import CurrencyConverter
        converter = CurrencyConverter()
        currencies = converter.get_supported_currencies()
        return {"currencies": currencies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )