---
name: stock-comparison
description: >
  对比多只股票或同行业公司的行情走势、财务指标、估值水平，生成对比分析表格和结论。
  当用户要求对比两只或多只股票、进行同行业比较、选股对比、估值比较时触发。
  触发短语："对比一下"、"比较"、"哪个更好"、"同行业对比"、"选哪个"、
  "A和B怎么选"、"compare stocks"、"which is better"、"peer comparison"、
  "对比分析"、"横向对比"。
---

# 股票对比分析

对比多只股票的行情走势和关键指标，生成可视化对比表格。

## 前置条件

```bash
pip install akshare pandas requests
```

## 使用方式

```bash
# 对比多只股票行情走势
python .agents/skills/stock-comparison/scripts/compare.py sh600519 sh000858 sh601318 --mode price --days 60

# 对比财务指标
python .agents/skills/stock-comparison/scripts/compare.py 600519 000858 --mode financial

# 综合对比
python .agents/skills/stock-comparison/scripts/compare.py 600519 000858 --mode all
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 股票代码 | 2-10 个代码，空格分隔。行情对比用 `sh`/`sz` 前缀，财务对比用纯数字 | 必填 |
| `--mode` | `price`（行情对比）/ `financial`（财务对比）/ `all`（综合） | `all` |
| `--days` | 行情对比的天数 | `60` |

### 对比维度

**行情对比** (`price`)：
- 区间涨跌幅对比
- 波动率对比
- 成交量变化对比
- 最高/最低价位置

**财务对比** (`financial`)：
- 估值：PE / PB / PS
- 盈利：ROE / 毛利率 / 净利率
- 成长：营收增速 / 利润增速
- 安全：资产负债率

### 输出格式

Markdown 对比表格 + 简要结论。示例：

```
| 指标 | 贵州茅台(600519) | 五粮液(000858) |
|------|------------------|----------------|
| 区间涨跌幅 | +5.2% | -2.1% |
| PE(TTM) | 28.5 | 19.3 |
| ROE | 31.2% | 22.8% |
| 营收增速 | 15.3% | 10.1% |
```

## 注意事项

- 对比分析应在同行业或相似业务的公司之间进行才有意义
- 不同行业估值水平差异较大，跨行业对比 PE/PB 意义有限
- 行情对比使用 `sh`/`sz` 前缀代码，财务对比使用纯 6 位数字
