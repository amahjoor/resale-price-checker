# Compare a clothing tag price to eBay

Paste a resale tag (brand, size, color, price, including a yen amount). The API parses it, converts the price to USD with exchangerate-api.com (fallback: exchangerate.host), and searches the eBay Browse API. The client is hardcoded to the eBay sandbox (`api.sandbox.ebay.com`). The verdict is one of `Strong Cop`, `Cop`, `Fair price`, or `Pass`, based on how far the tag price sits from the listing median. Strong cop is 15% or more under the median. Cop is 5% or more under.

There is no `.env.example` in the repo. Set `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` yourself.

## Evaluate a tag

```bash
pip install -r requirements.txt
```

`requirements.txt` is FastAPI, Uvicorn, requests, Pydantic, python-dotenv, regex, httpx, redis, and pytest. Redis is listed and is not imported by the scanner.

```bash
python -m src.main
python -m src.cli "Chrome Hearts hoodie Size L Color Black ¥175560"
```

The server listens on port 8000 (`PORT` overrides it). Interactive docs are at http://localhost:8000/docs.

```bash
curl -X POST http://localhost:8000/evaluate -H "Content-Type: application/json" -d '{"raw_tag": "Chrome Hearts hoodie Size L 175560 JPY"}'
```

## License

[MIT](LICENSE)
