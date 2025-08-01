# Market Price Comparison Scanner

A tool that helps users decide whether to "cop" or "pass" on an item by scanning its tag, extracting metadata, and comparing it to real-time market prices.

## Features

- **Tag String Parsing**: Extract brand, size, price, and other metadata from product descriptions
- **Price Normalization**: Convert prices to USD using live exchange rates
- **Market Data Fetching**: Query resale platforms (starting with eBay) for comparable listings
- **Decision Engine**: Get "cop/pass/maybe" recommendations with confidence scores
- **REST API**: Clean JSON API for integration

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your eBay API credentials
```

3. Run the API server:
```bash
python -m src.main
```

4. Or use the CLI:
```bash
python -m src.cli "Chrome Hearts Tokyo Limited Horse Shoeback Print Hoodie SWTSHRT PLV Gender Type : Men's Size :L Color : Black ¥175,560 tax included"
```

## API Usage

```bash
curl -X POST "http://localhost:8000/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"raw_tag": "Chrome Hearts Tokyo Limited Horse Shoeback Print Hoodie SWTSHRT PLV Gender Type : Mens Size :L Color : Black ¥175,560 tax included"}'
```

## Architecture

- `src/parser/`: Tag string parsing and metadata extraction
- `src/currency/`: Currency conversion with live rates
- `src/market/`: Market data fetching from various sources
- `src/decision/`: Aggregation and recommendation logic
- `src/api/`: FastAPI endpoints and models