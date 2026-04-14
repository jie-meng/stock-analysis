---
name: market-context
description: >
  获取股票分析所需的市场环境上下文：行业板块走势与资金流向、大宗商品/期货价格、
  个股新闻与事件、宏观经济指标。为基本面和技术面分析补充"变量因素"，
  避免脱离市场环境的孤立分析。
  当用户分析个股或行业时应主动调用，获取最新市场环境数据。
  当用户提到行业景气度、板块资金流、大宗商品价格、铝价/铜价/油价/金价、
  最近有什么新闻、市场环境、宏观数据、PMI、CPI 时触发。
  触发短语："市场环境"、"行业景气度"、"板块资金"、"铝价多少"、"最近新闻"、
  "大宗商品"、"宏观数据"、"market context"、"sector flow"、"commodity price"、
  "看看板块"、"资金流向"、"行业表现"。
---

# 市场环境上下文

为个股和行业分析提供最新的市场环境数据，包括行业板块走势、资金流向、
大宗商品价格、个股新闻和宏观经济指标。

**核心价值**：基本面和技术面分析只能看到历史数据。本技能补充正在发生的
"变量因素"——行业景气变化、资金动向、商品价格波动、重大事件——
让分析从"看后视镜"升级为"看前方路况"。

## 前置条件

```bash
pip install akshare pandas requests
```

## 使用方式

```bash
python .agents/skills/market-context/scripts/context.py <子命令> [参数]
```

### 子命令一览

| 子命令 | 用途 | 典型场景 |
|--------|------|---------|
| `sector` | 行业/概念板块排名 + 资金流 | "有色金属行业最近怎么样" |
| `commodity` | 大宗商品期货价格走势 | "铝价/铜价最近走势" |
| `news` | 个股最新新闻 | "银泰铝业最近有什么消息" |
| `macro` | 宏观经济指标 | "最近PMI怎么样" |
| `overview` | 全景概览（板块+商品+宏观） | 综合分析前的环境扫描 |

---

### sector — 行业/概念板块分析

```bash
# 查看行业板块排名（今日涨跌幅 + 资金流向）
python .agents/skills/market-context/scripts/context.py sector --type industry

# 查看概念板块排名
python .agents/skills/market-context/scripts/context.py sector --type concept

# 按关键词筛选板块
python .agents/skills/market-context/scripts/context.py sector --keyword 铝
python .agents/skills/market-context/scripts/context.py sector --keyword 有色金属
python .agents/skills/market-context/scripts/context.py sector --keyword 半导体

# 控制输出数量
python .agents/skills/market-context/scripts/context.py sector --type industry --top 20
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | `industry`（行业）/ `concept`（概念） | `industry` |
| `--keyword` | 按板块名称关键词筛选 | 无（显示全部排名） |
| `--top` | 显示前 N 个板块 | `15` |

输出内容：板块名称、涨跌幅排名、主力净流入金额和占比、领涨股。

---

### commodity — 大宗商品价格

```bash
# 查看常用大宗商品价格（铝、铜、原油、黄金、铁矿石）
python .agents/skills/market-context/scripts/context.py commodity

# 指定品种
python .agents/skills/market-context/scripts/context.py commodity --symbols AL0,CU0,AU0

# 调整历史天数
python .agents/skills/market-context/scripts/context.py commodity --days 30
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--symbols` | 逗号分隔的期货代码 | `AL0,CU0,SC0,AU0,I0` |
| `--days` | 显示最近 N 个交易日走势 | `20` |

内置品种代码映射：

| 代码 | 品种 | 关联行业 |
|------|------|---------|
| `AL0` | 沪铝 | 电解铝、铝加工 |
| `CU0` | 沪铜 | 铜矿、铜加工 |
| `SC0` | 原油 | 石化、化工、航空（成本端） |
| `AU0` | 沪金 | 黄金珠宝、避险资产 |
| `I0` | 铁矿石 | 钢铁 |
| `RB0` | 螺纹钢 | 钢铁、建筑 |
| `AG0` | 沪银 | 光伏（银浆）、电子 |
| `C0` | 玉米 | 养殖饲料 |
| `P0` | 棕榈油 | 油脂加工 |
| `CF0` | 棉花 | 纺织服装 |

输出内容：最新价、区间涨跌幅、最高/最低价、价格走势概要。

---

### news — 个股新闻

```bash
# 获取个股最新新闻
python .agents/skills/market-context/scripts/context.py news --code 002869

# 控制条数
python .agents/skills/market-context/scripts/context.py news --code 600519 --count 10
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--code` | 6 位股票代码 | 必填 |
| `--count` | 获取新闻条数 | `5` |

输出内容：新闻标题、发布时间、来源、内容摘要。

**重要提示**：东财新闻接口返回的是与该股票代码相关联的新闻，
可能包含不太相关的内容（如龙虎榜汇总中提到了该代码）。
分析时需要 AI 过滤噪音，聚焦真正影响基本面的重大事件。
对于行业级别的重大事件（如地缘冲突、政策变化），建议配合 WebSearch 工具搜索。

---

### macro — 宏观经济指标

```bash
# 查看最新宏观数据概览
python .agents/skills/market-context/scripts/context.py macro
```

输出内容：最新 PMI（制造业/非制造业）、CPI 月率。

**注意**：宏观数据有发布滞后（通常滞后 1-2 个月）。输出会标注数据所属月份。

---

### overview — 全景概览

```bash
# 一次性获取市场环境全景
python .agents/skills/market-context/scripts/context.py overview

# 按关键词聚焦
python .agents/skills/market-context/scripts/context.py overview --keyword 有色
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--keyword` | 聚焦特定行业/概念 | 无 |

overview 会依次输出：行业板块 Top 排名 + 资金流向 + 核心大宗商品 + 宏观指标。
是做综合分析前的"环境扫描"快捷方式。

---

## 与其他技能的配合

| 场景 | 工作流 |
|------|--------|
| **个股基本面分析** | 先 `market-context sector --keyword <行业>` + `news --code <代码>` 获取环境，再调 `financial-data-analysis` |
| **选股筛选后审查** | 筛选器输出候选名单后，用 `sector` 检查各行业景气度，用 `commodity` 检查上游原材料价格趋势 |
| **持仓组合诊断** | `overview` 全景扫描，结合持仓行业分布判断宏观风险敞口 |
| **行业变量因素追踪** | `commodity` + WebSearch 搜索最新地缘/政策事件 |

## 与 WebSearch 的分工

| 数据类型 | 用 market-context | 用 WebSearch |
|---------|-------------------|-------------|
| 板块涨跌幅/资金流 | ✅ 结构化数据 | ❌ |
| 大宗商品价格 | ✅ 准确数字 | ❌ |
| 个股日常新闻 | ✅ 东财新闻流 | 不够深度时补充 |
| 地缘政治/重大事件 | ❌ | ✅ 搜"伊朗 美国 电解铝"等 |
| 产业政策/规划文件 | ❌ | ✅ 搜"十五五 有色金属 政策" |
| 机构研报观点 | ❌ | ✅ 搜"XX股票 研报 评级" |

## 注意事项

- 板块资金流和排名数据为**盘中/盘后实时**，交易日内多次调用会有变化
- 期货价格为**收盘价**（非实时），盘中数据截止到上一个收盘日
- 东财新闻可能包含 AI 生成的低质量内容，分析时需过滤
- 宏观数据有 1-2 个月滞后，不代表当前最新经济状况
- 板块接口有频率限制，短时间内频繁调用可能被限流
