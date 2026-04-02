---
name: technical-indicator
description: >
  计算股票技术分析指标并输出分析结果。支持均线(MA/EMA)、MACD、RSI、KDJ、
  布林带(BOLL)、成交量分析等常用技术指标。基于行情数据进行技术面研判。
  当用户提到技术分析、技术指标、均线、MACD、RSI、KDJ、布林带、量价分析、
  买卖点、支撑位、压力位、金叉、死叉、超买超卖时触发。
  触发短语："技术分析"、"看看指标"、"MACD 怎么样"、"RSI 多少"、
  "有没有金叉"、"技术面"、"technical analysis"、"indicators"。
---

# 技术指标分析

计算常用技术分析指标，输出结构化分析结果和信号判断。

## 前置条件

```bash
pip install pandas requests
```

## 使用方式

```bash
python .agents/skills/technical-indicator/scripts/indicator.py <证券代码> [--frequency 1d] [--count 120] [--indicators ma,macd,rsi]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 证券代码 | `sh600519`、`sz000001` 等格式 | 必填 |
| `--frequency` | K 线周期：`1d` / `1w` / `60m` 等 | `1d` |
| `--count` | 计算所用数据量（条） | `120` |
| `--indicators` | 逗号分隔的指标列表 | `ma,macd,rsi,kdj,boll,vol` |

### 支持的指标

| 指标 | 代码 | 说明 |
|------|------|------|
| 移动平均线 | `ma` | MA5/MA10/MA20/MA60，含多头/空头排列判断 |
| MACD | `macd` | DIF/DEA/MACD 柱，含金叉/死叉信号 |
| RSI | `rsi` | 6日/12日/24日 RSI，含超买(>70)/超卖(<30)判断 |
| KDJ | `kdj` | K/D/J 值，含金叉/死叉和超买/超卖 |
| 布林带 | `boll` | 上轨/中轨/下轨，含突破和触轨信号 |
| 成交量 | `vol` | 量比、均量比较，放量/缩量判断 |

### 输出格式

Markdown 格式报告，每个指标包含：
- **当前数值**：最新一期的指标数值
- **信号判断**：如"MACD 金叉"、"RSI 超卖区"
- **趋势描述**：如"均线多头排列，短期趋势向上"

## 技术分析使用提示

- 单一指标不能作为买卖依据，应多指标交叉验证
- 不同市场环境适用不同指标：趋势行情看均线/MACD，震荡行情看 RSI/KDJ
- 技术分析需结合基本面和市场情绪综合判断
- 本工具只提供客观数据计算，不构成投资建议
