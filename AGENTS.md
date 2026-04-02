# Stock Analysis

This directory provides specialized skills and agents for stock analysis and investment research, designed for professional investors and non-technical users.

## Architecture

The project follows a modular architecture with two main components:

### Skills (`.agents/skills/`)
Individual analysis functions that perform specific tasks:
- **fundamental_analysis**: Basic financial metrics analysis
- **technical_analysis**: Price and volume technical indicators
- **sentiment_analysis**: News and social media sentiment
- **risk_metrics**: Risk calculation utilities

### Agents (`.agents/agents/`)
Autonomous workflows that combine multiple skills:
- **stock-screener**: Automated stock filtering based on criteria
- **portfolio-monitor**: Continuous portfolio tracking and analysis
- **risk-assessor**: Comprehensive risk evaluation
- **market-scanner**: Market opportunity identification
- **report-writer**: Automated report generation
- **alert-manager**: Condition-based notification system

## Usage Patterns

### For Non-Technical Users
1. Fork this repository
2. Configure API keys in `.env` file
3. Use existing agents via simple commands
4. Customize parameters in JSON config files

### For Technical Users
1. Create new skills in `.agents/skills/`
2. Build new agents in `.agents/agents/`
3. Extend existing functionality
4. Share improvements via pull requests

## Skill Structure

Each skill follows this pattern:
```
skill_name/
├── __init__.py
├── main.py
└── README.md
```

## Agent Structure

Each agent follows this pattern:
```
agent_name/
├── __init__.py
├── agent.py
├── config.json
└── README.md
```

## API Integration

Supported financial data providers:
- Yahoo Finance (free)
- Alpha Vantage (free tier available)
- Quandl (limited free tier)
- IEX Cloud (free tier available)

## User Customization

Professional investors can:
- Modify existing agents for specific workflows
- Create new agents for proprietary strategies
- Combine agents for comprehensive analysis
- Schedule automated runs
- Set up custom alerting rules

## Security Note

Never hardcode API keys or sensitive data. Use environment variables or secure configuration files.

## Getting Started

```bash
# Install with all features
pip install -e .[full]

# Or install core only
pip install -e .
```