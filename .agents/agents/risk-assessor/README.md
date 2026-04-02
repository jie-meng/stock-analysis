# Risk Assessor Agent

## Purpose
Evaluates investment risk at both portfolio and individual stock levels, providing risk metrics and recommendations.

## Features
- **Value at Risk (VaR)**: Calculate potential losses at confidence levels
- **Beta Analysis**: Measure volatility relative to market
- **Correlation Analysis**: Identify diversification effectiveness
- **Stress Testing**: Simulate portfolio under market scenarios
- **Sector Concentration**: Identify over-exposure risks

## Usage
```bash
# Assess single stock risk
python assess.py --symbol AAPL

# Assess portfolio risk
python assess.py --portfolio portfolio.json --confidence 0.95

# Stress test
python assess.py --stress-test recession
```

## Risk Metrics
- Historical VaR (parametric and Monte Carlo)
- Conditional VaR (Expected Shortfall)
- Maximum drawdown analysis
- Volatility (standard deviation, beta)
- Sharpe and Sortino ratios

## Output Format
```json
{
  "symbol": "AAPL",
  "risk_score": 7.2,
  "metrics": {
    "var_95": -0.045,
    "beta": 1.15,
    "volatility": 0.28,
    "max_drawdown": -0.32
  },
  "recommendations": [
    "Consider hedging with put options",
    "Monitor tech sector correlation"
  ]
}
```