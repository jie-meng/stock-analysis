---
name: ashare-price-data
description: >
  获取中国 A 股股票历史行情和实时数据。通过内置 Python 脚本从新浪财经/腾讯股票
  获取日线、周线、月线、分钟线数据，返回 pandas DataFrame。
  当用户提到 A 股、沪深股票、行情数据、K线、股价、历史价格、实时报价，
  或提到具体的 A 股代码（如 600519、000001、sh000001）时触发此技能。
  触发短语："查行情"、"看看股价"、"拉一下数据"、"最近走势"、"K线数据"、
  "获取行情"、"stock price"、"price data"、"get quotes"。
---

# A 股行情数据获取

通过新浪财经和腾讯股票公开接口获取 A 股历史行情及实时数据，双数据源自动容错。

## 前置条件

需要 `pandas` 和 `requests`：

```bash
pip install pandas requests
```

## 使用方式

运行内置脚本获取数据：

```bash
python .agents/skills/ashare-price-data/scripts/ashare.py <证券代码> [--frequency 1d] [--count 30] [--end-date 2024-12-31] [--realtime]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 证券代码 | 支持 `sh600519`、`sz000001`、`000001.XSHG` 等格式 | 必填 |
| `--frequency` | `1d` 日线 / `1w` 周线 / `1M` 月线 / `5m` `15m` `30m` `60m` 分钟线 | `1d` |
| `--count` | 数据条数 | `30` |
| `--end-date` | 截止日期 `YYYY-MM-DD`，默认取最新 | 无 |
| `--realtime` | 获取实时行情快照 | 否 |

### 示例

```bash
# 贵州茅台最近60个交易日日线
python .agents/skills/ashare-price-data/scripts/ashare.py sh600519 --count 60

# 上证指数15分钟线，最近100根
python .agents/skills/ashare-price-data/scripts/ashare.py sh000001 --frequency 15m --count 100

# 实时行情
python .agents/skills/ashare-price-data/scripts/ashare.py sh600519 --realtime
```

### 输出格式

历史数据输出 CSV 格式表格（含表头）：`date,open,close,high,low,volume`

实时数据输出 JSON：`{"name":"贵州茅台","price":1680.0,"open":1675.0,...}`

## 常见代码对照

| 名称 | 代码 |
|------|------|
| 上证指数 | `sh000001` |
| 深证成指 | `sz399001` |
| 创业板指 | `sz399006` |
| 贵州茅台 | `sh600519` |
| 平安银行 | `sz000001` |
| 宁德时代 | `sz300750` |

## 注意事项

- 数据源为公开接口，可能有访问频率限制，短时间内不要大量并发请求
- 分钟线数据通常只保留近期，历史分钟线可能不完整
- 交易时间外获取的实时数据为上一交易日收盘价
