# Portfolio Monitor Agent

## Purpose
Continuously monitors investment portfolio performance, tracks asset allocation, and identifies rebalancing opportunities.

## Features
- **Performance Tracking**: Daily/weekly/monthly returns
- **Allocation Analysis**: Sector, asset class, geographic distribution
- **Benchmark Comparison**: Compare against market indices
- **Rebalancing Alerts**: Identify when allocation drifts from targets

## Usage
```bash
# Start monitoring
python monitor.py --portfolio portfolio.json

# Generate report
python monitor.py --report --period monthly
```

## Configuration
`portfolio.json`:
```json
{
  "holdings": [
    {"symbol": "AAPL", "shares": 100, "cost_basis": 150.00},
    {"symbol": "MSFT", "shares": 50, "cost_basis": 300.00}
  ],
  "target_allocation": {
    "technology": 0.40,
    "healthcare": 0.20,
    "financials": 0.20,
    "other": 0.20
  },
  "benchmark": "SPY"
}
```

## Metrics
- Total return (absolute and percentage)
- Sharpe ratio
- Maximum drawdown
- Alpha and beta vs benchmark
- Dividend income tracking