# Report Writer Agent

## Purpose
Generates comprehensive investment analysis reports in multiple formats, combining data from other agents.

## Features
- **Multi-Source Integration**: Combine data from screener, monitor, risk assessor
- **Template System**: Customizable report templates
- **Multiple Formats**: Markdown, PDF, HTML, Excel
- **Scheduled Reports**: Daily, weekly, monthly automated reports
- **Chart Generation**: Automatic visualization creation

## Usage
```bash
# Generate single stock report
python report.py --symbol AAPL --type fundamental

# Generate portfolio report
python report.py --portfolio portfolio.json --format pdf

# Schedule weekly report
python report.py --schedule weekly --email user@example.com
```

## Report Types

### Stock Analysis Report
- Company overview and business model
- Financial analysis (revenue, margins, growth)
- Technical analysis (charts, indicators)
- Valuation metrics and comparisons
- Risk assessment
- Analyst consensus

### Portfolio Report
- Performance summary
- Asset allocation analysis
- Risk metrics
- Rebalancing recommendations
- Dividend income tracking

### Market Overview Report
- Market indices performance
- Sector analysis
- Economic indicators
- Market sentiment

## Templates
Located in `templates/` directory:
- `stock_analysis.md`
- `portfolio_summary.md`
- `market_overview.md`

## Configuration
```json
{
  "output_dir": "reports",
  "templates_dir": "templates",
  "default_format": "markdown",
  "email_settings": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "reports@example.com"
  }
}
```