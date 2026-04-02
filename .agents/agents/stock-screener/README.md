# 股票筛选代理

## 用途
基于可自定义条件自动筛选股票，包括基本面指标、技术指标和市场条件。

## 功能特点
- **基本面筛选**：市盈率、市值、收入增长、利润率
- **技术面筛选**：移动平均线、RSI、MACD、成交量模式
- **市场条件**：行业表现、市值排名
- **自定义条件**：用户定义的筛选参数

## 使用方法
```bash
# 运行基础筛选
python screen.py --pe-max 20 --market-cap-min 1B

# 使用配置文件运行
python screen.py --config my_screen.json
```

## 配置
创建 `screen_config.json`：
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

## 输出结果
- 符合条件的股票列表
- 每只股票的关键指标
- 评分/排名系统

## 自定义
修改 `criteria.py` 以添加新的筛选条件或调整权重。