#!/usr/bin/env python3
"""
Main entry point for the Market Price Comparison Scanner API server.
"""

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Starting Market Price Comparison Scanner API on port {port}")
    print(f"Debug mode: {debug}")
    print("API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=debug
    )