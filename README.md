# Stock Analysis

A comprehensive toolkit for stock market analysis and investment research, featuring modular skills and autonomous agents designed for professional investors and non-technical users.

## Features

- **Modular Skills**: Ready-to-use analysis functions for fundamental, technical, and sentiment analysis
- **Autonomous Agents**: Pre-built workflows for screening, monitoring, risk assessment, and reporting
- **Custom Creation**: Easy framework for creating personalized skills and agents
- **Public API Integration**: Connect to popular financial data providers
- **User-Friendly**: Designed for non-technical investors with simple configuration

## Quick Start

1. **Install the package**:
   ```bash
   # Install with all features (technical analysis + visualization)
   pip install -e .[full]
   
   # Or install core only
   pip install -e .
   ```

2. **Configure API keys**:
   ```bash
   cp config.example.json config.json
   # Edit config.json with your API keys
   ```

3. **Run an agent**:
   ```bash
   stock-analysis --help
   ```

## Architecture

### Skills (`.agents/skills/`)
Individual analysis functions:
- **fundamental_analysis**: Financial ratios, revenue, margins
- **technical_analysis**: Moving averages, RSI, MACD
- **sentiment_analysis**: News and social media sentiment
- **risk_metrics**: VaR, beta, volatility calculations

### Agents (`.agents/agents/`)
Autonomous workflows:
- **stock-screener**: Filter stocks based on customizable criteria
- **portfolio-monitor**: Track portfolio performance and allocation
- **risk-assessor**: Evaluate investment risk at multiple levels
- **market-scanner**: Identify market opportunities and anomalies
- **report-writer**: Generate comprehensive analysis reports
- **alert-manager**: Trigger notifications based on market conditions

## Usage Examples

### Basic Stock Screening
```python
from agents.stock_screener import screen_stocks

results = screen_stocks(
    criteria={
        "pe_ratio": {"max": 25},
        "market_cap": {"min": 1000000000},
        "dividend_yield": {"min": 0.02}
    }
)
```

### Portfolio Monitoring
```python
from agents.portfolio_monitor import monitor_portfolio

report = monitor_portfolio(
    holdings=[
        {"symbol": "AAPL", "shares": 100},
        {"symbol": "MSFT", "shares": 50}
    ],
    benchmark="SPY"
)
```

### Risk Assessment
```python
from agents.risk_assessor import assess_risk

risk_metrics = assess_risk(
    symbol="AAPL",
    confidence_level=0.95,
    period="1y"
)
```

## Creating Custom Skills

1. Create a new directory in `.agents/skills/`
2. Follow the skill template structure:
   ```
   my_skill/
   ├── __init__.py
   ├── main.py
   └── README.md
   ```
3. Implement your analysis logic
4. Use in your agents or share with others

## Creating Custom Agents

1. Create a new directory in `.agents/agents/`
2. Follow the agent template structure:
   ```
   my_agent/
   ├── __init__.py
   ├── agent.py
   ├── config.json
   └── README.md
   ```
3. Combine existing skills or create new ones
4. Schedule runs or trigger on conditions

## API Configuration

Supported financial data providers:
- **Yahoo Finance** (free) - Default
- **Alpha Vantage** (free tier available)
- **Quandl** (limited free tier)
- **IEX Cloud** (free tier available)

## Directory Structure

```
stock-analysis/
├── .agents/
│   ├── skills/          # Analysis skills
│   │   ├── fundamental_analysis/
│   │   ├── technical_analysis/
│   │   └── sentiment_analysis/
│   └── agents/          # Autonomous agents
│       ├── stock-screener/
│       ├── portfolio-monitor/
│       └── risk-assessor/
├── config.example.json  # Configuration template
├── pyproject.toml       # Project dependencies
├── AGENTS.md           # Architecture guidelines
└── README.md           # This file
```

## Use Cases

- **Quick Stock Screening**: Filter stocks by fundamental metrics
- **Technical Timing**: Identify entry/exit points
- **Risk Management**: Evaluate portfolio risk
- **Market Sentiment**: Analyze news and social media
- **Automated Reporting**: Generate regular analysis reports
- **Custom Strategies**: Implement proprietary analysis methods

## Getting Help

- Check `AGENTS.md` for architecture and guidelines
- Each skill and agent has its own README with usage examples
- Use the skill creator tool to build new analysis methods

## Security

- Never commit API keys or sensitive data
- Use environment variables for secrets
- Keep analysis methods proprietary if needed

## License

MIT License - see LICENSE file for details.