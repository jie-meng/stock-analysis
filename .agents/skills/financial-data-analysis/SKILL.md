---
name: financial-data-analysis
description: >
  分析股票财务数据，计算关键财务指标（PE、PB、ROE、毛利率、负债率等），
  生成财务健康评估报告。通过 akshare 获取 A 股上市公司财务报表数据。
  当用户提到基本面分析、财务分析、财报、财务指标、估值分析、PE/PB/ROE、
  利润表、资产负债表、现金流量表、年报、季报，或要求判断一家公司财务状况时触发。
  触发短语："分析财务"、"看看基本面"、"财务数据"、"估值如何"、"值不值得买"、
  "financial analysis"、"fundamental analysis"、"valuation"、"financial health"。
---

# 财务数据分析

获取 A 股上市公司财务报表，计算核心财务指标，生成可读的财务分析摘要。

## 前置条件

```bash
pip install akshare pandas
```

## 使用方式

```bash
# 分析单只股票的财务数据
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> [--years 3]

# 获取特定报表
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report balance
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report income
python .agents/skills/financial-data-analysis/scripts/finance.py <股票代码> --report cashflow
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 股票代码 | 6 位纯数字，如 `600519`、`000001` | 必填 |
| `--years` | 分析最近几年的数据 | `3` |
| `--report` | 指定报表：`balance`（资产负债表）/ `income`（利润表）/ `cashflow`（现金流量表）/ `all`（全部） | `all` |

### 输出内容

脚本输出结构化的 Markdown 格式分析报告，包含：

1. **估值指标**：市盈率（PE）、市净率（PB）、市销率（PS）
2. **盈利能力**：净资产收益率（ROE）、毛利率、净利率
3. **成长性**：营收增长率、净利润增长率
4. **财务安全**：资产负债率、流动比率、速动比率
5. **现金流**：经营现金流/净利润比率

## 分析框架参考

在向用户呈现分析结果时，可参考以下判断标准：

| 指标 | 优秀 | 良好 | 关注 |
|------|------|------|------|
| ROE | > 15% | 10-15% | < 10% |
| 毛利率 | > 40% | 20-40% | < 20% |
| 资产负债率 | < 40% | 40-60% | > 60% |
| 营收增长率 | > 20% | 10-20% | < 0% |
| 经营现金流/净利润 | > 1.0 | 0.7-1.0 | < 0.7 |

不同行业的标准有差异，金融、地产行业的负债率天然较高，需结合行业特性判断。

## 注意事项

- 股票代码使用纯 6 位数字（不带 sh/sz 前缀）
- akshare 获取的是公开披露的财报数据，可能有数据延迟
- 首次运行可能需要较长时间下载数据
