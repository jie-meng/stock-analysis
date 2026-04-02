# Alert Manager Agent

## Purpose
Monitors market conditions and triggers alerts based on user-defined rules, enabling timely investment decisions.

## Features
- **Price Alerts**: Break above/below levels, percentage moves
- **Technical Alerts**: Indicator crossovers, pattern completions
- **Volume Alerts**: Unusual volume, relative volume spikes
- **Fundamental Alerts**: Earnings, dividends, analyst changes
- **Portfolio Alerts**: Allocation drift, loss limits

## Usage
```bash
# Add price alert
python alerts.py add --symbol AAPL --type price --above 180.00

# List active alerts
python alerts.py list

# Run alert checker
python alerts.py check --interval 5m

# Remove alert
python alerts.py remove --id 12345
```

## Alert Types

### Price Alerts
```json
{
  "symbol": "AAPL",
  "type": "price",
  "condition": "above",
  "value": 180.00,
  "action": ["email", "sms"]
}
```

### Technical Alerts
```json
{
  "symbol": "MSFT",
  "type": "technical",
  "indicator": "RSI",
  "condition": "below",
  "value": 30,
  "period": "1d"
}
```

### Portfolio Alerts
```json
{
  "type": "portfolio",
  "metric": "total_loss",
  "threshold": -0.10,
  "action": ["email"]
}
```

## Notification Channels
- Email
- SMS (via Twilio)
- Slack/Discord webhooks
- Push notifications

## Configuration
```json
{
  "check_interval": "1m",
  "notifications": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "sender": "alerts@example.com",
      "recipients": ["user@example.com"]
    },
    "slack": {
      "webhook_url": "https://hooks.slack.com/..."
    }
  },
  "max_alerts_per_day": 50
}
```