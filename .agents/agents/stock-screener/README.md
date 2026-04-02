# Stock Screener Agent

## Purpose
Automatically screens stocks based on customizable criteria including fundamental metrics, technical indicators, and market conditions.

## Features
- **Fundamental Screening**: P/E ratio, market cap, revenue growth, profit margins
- **Technical Screening**: Moving averages, RSI, MACD, volume patterns
- **Market Conditions**: Sector performance, market cap rankings
- **Custom Criteria**: User-defined screening parameters

## Usage
```bash
# Run basic screening
python screen.py --pe-max 20 --market-cap-min 1B

# Run with config file
python screen.py --config my_screen.json
```

## Configuration
Create `screen_config.json`:
```json
{
  "criteria": {
    "pe_ratio": {"max": 25},
    "market_cap": {"min": 1000000000},
    "dividend_yield": {"min": 0.02}
  },
  "data_source": "yahoo_finance",
  "output_format": "csv"
}
```

## Output
- List of stocks meeting criteria
- Key metrics for each stock
- Scoring/ranking system

## Customization
Modify `criteria.py` to add new screening criteria or adjust weighting.