# Market Scanner Agent

## Purpose
Scans market for unusual activity, momentum shifts, and potential opportunities across multiple timeframes.

## Features
- **Volume Scanners**: Unusual volume spikes, relative volume
- **Price Movers**: Gainers, losers, gap up/down
- **Technical Breakouts**: Support/resistance breaks, pattern completions
- **Sector Rotation**: Identify leading and lagging sectors
- **Options Activity**: Unusual options flow, high open interest

## Usage
```bash
# Daily market scan
python scan.py --type daily

# Real-time scanner
python scan.py --type realtime --interval 5m

# Custom scan
python scan.py --config scan_config.json
```

## Scan Types

### Daily Scans
- Top gainers/losers by percentage
- Volume breakouts (>2x average)
- New 52-week highs/lows
- Earnings announcements

### Intraday Scans
- Momentum stocks
- Reversal patterns
- Unusual options activity
- Dark pool prints

## Configuration
```json
{
  "scanners": {
    "volume_breakout": {"threshold": 2.0},
    "price_momentum": {"period": "1h", "min_change": 0.03},
    "options_flow": {"min_premium": 100000}
  },
  "filters": {
    "min_price": 5.00,
    "min_volume": 500000,
    "exclude_symbols": ["SPY", "QQQ"]
  }
}
```