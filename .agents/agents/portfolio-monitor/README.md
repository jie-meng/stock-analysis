# 投资组合监控代理

## 用途
持续监控投资组合表现，跟踪资产配置，识别再平衡机会。

## 功能特点
- **表现跟踪**：每日/每周/每月收益
- **配置分析**：行业、资产类别、地理分布
- **基准比较**：与市场指数对比
- **再平衡警报**：识别配置偏离目标的情况

## 使用方法
```bash
# 开始监控
python monitor.py --portfolio portfolio.json

# 生成报告
python monitor.py --report --period monthly
```

## 配置
`portfolio.json`：
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

## 指标
- 总收益（绝对值和百分比）
- 夏普比率
- 最大回撤
- 相对于基准的阿尔法和贝塔值
- 股息收入跟踪