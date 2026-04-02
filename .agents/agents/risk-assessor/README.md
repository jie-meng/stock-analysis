# 风险评估代理

## 用途
评估投资组合和个股层面的投资风险，提供风险指标和建议。

## 功能特点
- **风险价值 (VaR)**：计算置信水平下的潜在损失
- **贝塔分析**：衡量相对于市场的波动性
- **相关性分析**：识别分散化效果
- **压力测试**：模拟市场情景下的投资组合表现
- **行业集中度**：识别过度暴露风险

## 使用方法
```bash
# 评估单只股票风险
python assess.py --symbol AAPL

# 评估投资组合风险
python assess.py --portfolio portfolio.json --confidence 0.95

# 压力测试
python assess.py --stress-test recession
```

## 风险指标
- 历史VaR（参数法和蒙特卡洛法）
- 条件VaR（预期损失）
- 最大回撤分析
- 波动率（标准差、贝塔）
- 夏普比率和索提诺比率

## 输出格式
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
    "考虑使用看跌期权进行对冲",
    "监控科技行业相关性"
  ]
}
```