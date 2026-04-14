# 数据源参考手册

本文档记录项目中所有可用的数据接口、它们的能力、性能特征和选用建议。创建或优化 skill 脚本时必须参考本文档，避免选错接口导致性能低下。

> 最后更新：2026-04-02，基于 akshare 1.18.49 + 新浪/腾讯公开接口。

---

## 速查：按数据需求选接口

| 我需要… | 推荐接口 | 耗时 | 来源 |
|---------|---------|------|------|
| 单只股票日线/周线/月线 | ashare.py `get_price()` | <1s | 新浪/腾讯 |
| 单只股票分钟线 | ashare.py `get_price()` | <1s | 新浪/腾讯 |
| 单只股票实时报价 | ashare.py `get_realtime()` | <1s | 新浪/腾讯 |
| 单只股票日线（含成交额/换手率/振幅） | `ak.stock_zh_a_hist()` | ~2s | 东财 |
| 全市场 PE/PB/市值快照 | `ak.stock_zh_a_spot_em()` | ~7min | 东财 |
| 概念板块成分股 + PE/PB | 东财 clist API 直调 | ~3-4s/板块 | 东财 |
| 全市场 ROE/EPS/利润增速 | `ak.stock_yjbb_em()` | ~80s | 东财 |
| 全市场股息率 | `ak.stock_fhps_em()` | ~28s | 东财 |
| 全市场资产负债率 | `ak.stock_zcfz_em()` | ~40s | 东财 |
| 全市场分红次数/累计股息 | `ak.stock_history_dividend()` | ~3s | 东财/中财网 |
| 单只股票详细财务指标 | `ak.stock_financial_abstract_ths()` | ~5s | 同花顺 |
| 单只股票分红历史 | `ak.stock_history_dividend_detail()` | ~2s | 东财 |
| 概念板块列表 | `ak.stock_board_concept_name_em()` | ~18s | 东财 |

---

## 数据源一：新浪财经 / 腾讯股票（ashare.py）

**库模块位置**：`.agents/shared/ashare.py`（共享模块，所有 skill 共用）

**CLI 入口**：`.agents/skills/ashare-price-data/scripts/price.py`（薄 wrapper）

**依赖**：仅 `requests` + `pandas`，无 akshare 依赖。

**核心优势**：极快（<1 秒）、轻量、双源容错。

### 接口清单

| 函数 | 数据 | 频率支持 | 耗时 |
|------|------|---------|------|
| `get_price(code, count, frequency)` | OHLCV（前复权） | 1d/1w/1M/1m/5m/15m/30m/60m | <1s |
| `get_realtime(code)` | 实时价格/开盘/最高/最低/成交量/成交额 | 实时快照 | <1s |

### 输出字段

**历史数据**：`date, open, close, high, low, volume`

**实时数据**：`name, open, pre_close, price, high, low, volume, amount, date, time`

### 代码格式

支持 `sh600519`、`sz000001`、`000001.XSHG` 等格式，内部自动转换。

### skill 内引用方式

行情模块 `ashare.py` 统一存放在 `.agents/shared/` 目录，各 skill 通过 `__file__` 向上定位引用：

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, os.pardir, "shared"))
from ashare import get_price, get_realtime
```

共享模块目录结构：

```
.agents/
├── shared/
│   ├── __init__.py
│   └── ashare.py     ← 行情模块（唯一副本）
└── skills/
    └── <skill-name>/scripts/
        └── <entry>.py    ← CLI 入口
```

### 适用场景

- 技术分析技能（technical-indicator）的行情输入
- 用户问"看看 XX 走势"时的快速响应
- 需要分钟级数据的日内分析

### 不适用场景

- 批量获取多只股票（无批量接口）
- 需要成交额、换手率、振幅等衍生字段
- 财务数据

---

## 数据源二：akshare（东方财富为主）

**依赖**：`akshare` 包（底层调东财、同花顺、中财网等多个源）。

**核心优势**：批量全市场数据、财务数据覆盖全面。

**核心劣势**：部分接口有内置 sleep（反爬），导致耗时长。

### 关键性能特征

akshare 内部有一个 `fetch_paginated_data()` 函数（`akshare/utils/func.py`），用于东财 push2 系列接口的分页获取。该函数**每页 sleep 0.5-1.5 秒**。以下接口受此影响：

- `stock_zh_a_spot_em()` — 全市场行情（~50 页 × sleep = 慢）
- `stock_board_concept_cons_em()` — 板块成分股（每板块多页 × sleep）
- `stock_board_concept_name_em()` — 概念板块列表

以下接口**不受此影响**（走 `datacenter-web` 分页，无内置 sleep）：

- `stock_yjbb_em()` — 业绩报表
- `stock_fhps_em()` — 分红送配
- `stock_zcfz_em()` — 资产负债表
- `stock_lrb_em()` — 利润表

### 批量接口详细说明

#### stock_yjbb_em(date) — 业绩报表

**耗时**：~80s  **数据量**：~11000 只

```python
df = ak.stock_yjbb_em(date="20241231")
```

| 字段 | 说明 |
|------|------|
| 股票代码 | 6 位纯数字 |
| 股票简称 | 中文名称 |
| 每股收益 | EPS |
| 净资产收益率 | **加权 ROE**（准确） |
| 净利润-同比增长 | 净利润增速 % |
| 营业总收入-同比增长 | 营收增速 % |
| 销售毛利率 | 毛利率 % |
| 每股净资产 | BPS |
| 每股经营现金流量 | 经营现金流 |
| 所处行业 | 行业分类 |

**注意**：`date` 参数是报告期（如 `20241231`），不是查询日期。全年报通常次年 4 月前披露完毕。

#### stock_fhps_em(date) — 分红送配

**耗时**：~28s  **数据量**：~3600 只

```python
df = ak.stock_fhps_em(date="20241231")
```

| 字段 | 说明 |
|------|------|
| 代码 | 6 位纯数字 |
| 现金分红-股息率 | **小数格式**（0.0423 = 4.23%），需要 ×100 |
| 每股收益 | EPS |
| 每股净资产 | BPS |
| 净利润同比增长 | % |
| 方案进度 | "预案"/"实施分配" 等 |

**注意**：股息率是基于分红预案/实施的报告期数据，不是实时 TTM 股息率。

#### stock_zcfz_em(date) — 资产负债表

**耗时**：~40s  **数据量**：~5200 只

```python
df = ak.stock_zcfz_em(date="20241231")
```

| 字段 | 说明 |
|------|------|
| 股票代码 | 6 位纯数字 |
| 资产负债率 | **直接百分比数值**（如 61.55） |
| 资产-总资产 | 总资产（元） |
| 负债-总负债 | 总负债（元） |
| 资产-货币资金 | 货币资金（元） |
| 资产-应收账款 | 应收账款（元） |
| 资产-存货 | 存货（元） |

#### stock_history_dividend() — 分红历史汇总

**耗时**：~3s  **数据量**：~5600 只

```python
df = ak.stock_history_dividend()
```

| 字段 | 说明 |
|------|------|
| 代码 | 6 位纯数字 |
| 分红次数 | 历史累计分红次数 |
| 累计股息 | 累计每股分红（元） |
| 年均股息 | 年均每股分红 |
| 融资总额 | 融资金额（亿元） |

#### stock_zh_a_spot_em() — 全市场实时行情

**耗时**：~7 分钟（受 fetch_paginated_data sleep 影响）  **数据量**：~5300 只

```python
df = ak.stock_zh_a_spot_em()
```

包含：代码、名称、最新价、涨跌幅、涨跌额、成交量、成交额、振幅、最高、最低、今开、昨收、量比、换手率、市盈率-动态、市净率、总市值、流通市值、涨速、5 分钟涨跌、60 日涨跌幅、年初至今涨跌幅。

**重要**：这是最慢的批量接口。如果只需要 PE/PB/市值，优先通过板块接口获取（按需拉取，而非全市场）。

### 板块接口

#### stock_board_concept_cons_em(symbol) — 概念板块成分股

通过 akshare 调用：**每板块 20-70 秒**（受 sleep 影响，随成分股数量变化）。

```python
df = ak.stock_board_concept_cons_em(symbol="光伏概念")
```

返回该板块所有成分股 + 实时行情（最新价、涨跌幅、PE、PB、总市值等）。

**优化方案**：直调东财 clist API，绕过 akshare 的 `fetch_paginated_data` sleep。stock-screener 技能已实现此优化。

#### 东财 clist API 直调（绕过 akshare sleep）

```python
url = "https://29.push2.eastmoney.com/api/qt/clist/get"
params = {
    "pn": "1", "pz": "100",   # pz 最大有效值为 100
    "po": "1", "np": "1",
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": "2", "invt": "2",
    "fid": "f12",
    "fs": f"b:{bk_code} f:!50",   # bk_code 如 "BK0800"
    "fields": "f2,f3,f9,f12,f14,f20,f21,f23",
}
```

字段映射：

| 字段代码 | 含义 |
|---------|------|
| f2 | 最新价 |
| f3 | 涨跌幅 |
| f9 | 市盈率（动态） |
| f12 | 股票代码 |
| f14 | 名称 |
| f20 | 总市值 |
| f21 | 流通市值 |
| f23 | 市净率 |

**注意**：`pz` 参数虽然可以设更大值，但东财接口固定最多返回 100 条/页。需自行分页，但不需要 sleep，单板块 700 只约 3-4 秒。

#### stock_board_concept_name_em() — 概念板块列表

**耗时**：~18s

```python
df = ak.stock_board_concept_name_em()
# 板块名称 → 板块代码（BKxxxx）的映射
```

### 单只股票接口

以下接口每次只能查一只股票，不适合批量场景。

| 接口 | 数据 | 耗时/只 |
|------|------|---------|
| `stock_financial_abstract_ths(symbol, indicator)` | 同花顺财务摘要（宽表） | ~5s |
| `stock_history_dividend_detail(symbol, indicator)` | 单只分红历史明细 | ~2s |
| `stock_zh_a_hist(symbol, period, ...)` | 单只日线（含成交额/换手率） | ~2s |
| `stock_individual_spot_xq(symbol)` | 雪球实时行情（含 PE/PB/股息率 TTM） | ~5s |

### 不可用 / 已废弃接口

以下接口在实测中发现不可用，创建 skill 时**不要使用**：

| 接口 | 问题 |
|------|------|
| `stock_financial_analysis_indicator()` | 返回空数据 |
| `stock_financial_analysis_indicator_em()` | 返回空数据 |
| `stock_board_concept_cons_ths()` | 已从 akshare 移除 |

---

## 数据源对比与选用原则

### 行情数据：ashare.py vs akshare

| 场景 | 选 ashare.py | 选 akshare |
|------|-------------|-----------|
| 单只股票看行情 | ✅ <1s | ❌ 2-5s |
| 分钟线数据 | ✅ <1s | ❌ 2s |
| 需要换手率/振幅 | ❌ 无此字段 | ✅ 有 |
| 批量全市场 | ❌ 无批量接口 | ✅ 有 |
| 实时报价 | ✅ <1s 基础字段 | ✅ 5s 丰富字段 |

**原则**：单只 → ashare.py，批量 → akshare。

### 财务数据：批量 vs 逐个

| 场景 | 选批量接口 | 选逐个接口 |
|------|-----------|-----------|
| 选股筛选 100+ 只 | ✅ yjbb + fhps + zcfz | ❌ 逐个 = 100×5s = 500s |
| 深度分析 1-3 只 | ❌ 杀鸡用牛刀 | ✅ stock_financial_abstract_ths |
| 只需 ROE 一个指标 | ✅ yjbb 80s 包含 ROE | ❌ |
| 需要季度财务明细 | ❌ 批量只有最新报告期 | ✅ 逐个可取多期 |

**原则**：筛选/对比 → 批量；深度分析 → 逐个。

---

## 性能优化经验

### 1. 并发是最有效的优化

多个独立的批量接口应并发调用：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    f1 = executor.submit(fetch_yjbb)
    f2 = executor.submit(fetch_fhps)
    f3 = executor.submit(fetch_zcfz)
    f4 = executor.submit(fetch_divhist)
```

四个接口串行 ~150s，并发 ~80s（受最慢的 yjbb 限制）。

### 2. 板块接口要绕过 akshare

`stock_board_concept_cons_em` 通过 akshare 调用时每页 sleep 0.5-1.5s。直调东财 API + 并发，27 个板块从 ~9 分钟降到 ~60 秒。

参考实现：`.agents/skills/stock-screener/scripts/screener.py` 中的 `_fetch_board_direct()` 和 `fetch_sector_pool_concurrent()`。

### 3. 能用板块接口就不用全市场接口

`stock_zh_a_spot_em()` 需要 ~7 分钟。如果用户的需求可以框定到具体板块（概念板块或行业板块），用板块接口替代，速度快 10 倍以上。

### 4. merge 代替循环

获取到多个批量 DataFrame 后，用 `pd.merge(on="代码")` 合并为宽表，然后用向量化 boolean mask 筛选。不要用 `for` 循环逐行处理。

---

## 数据质量注意事项

- **ROE**：`stock_yjbb_em` 提供的是加权净资产收益率，与同花顺/东方财富页面一致。`stock_fhps_em` 的 EPS/BPS 可近似算 ROE（EPS÷BPS×100），但与加权 ROE 有 ±2pp 偏差
- **股息率**：`stock_fhps_em` 的股息率是**小数格式**（0.0423），需要 ×100 才是百分比。且是报告期数据，非 TTM
- **市盈率**：板块接口和全市场接口返回的是**动态 PE**，非 TTM。akshare 没有全市场个股 TTM PE 的批量接口
- **报告期滞后**：财务数据通常滞后 1-2 个季度。`date` 参数应使用最近已披露的报告期（如 4 月查询用 `20241231`，8 月查询用 `20250630`）
- **ST/退市股**：批量接口包含 ST 和退市股，筛选时需主动排除（按名称匹配 "ST" 或 "退"）

---

## 数据源三：market-context 技能新增接口

以下接口由 `market-context` 技能引入，用于获取市场环境上下文数据。

### 行业/概念板块排名

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_board_industry_name_em()` | ~25s | 全行业板块排名（涨跌幅、换手率、领涨股） |
| `stock_board_concept_name_em()` | ~25s | 全概念板块排名 |

### 板块资金流向

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_sector_fund_flow_rank(indicator, sector_type)` | ~25s | 板块资金流向排名（主力净流入、超大单等） |

`indicator` 可选值：`"今日"` / `"5日"` / `"10日"`
`sector_type` 可选值：`"行业资金流"` / `"概念资金流"`

### 期货主力合约

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `futures_main_sina(symbol)` | ~3s | 主力合约日线（开高低收、成交量、持仓量） |

常用品种代码：`AL0`（铝）、`CU0`（铜）、`SC0`（原油）、`AU0`（黄金）、`I0`（铁矿石）、`RB0`（螺纹钢）、`AG0`（银）

### 个股新闻

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_news_em(symbol)` | ~3s | 东财新闻流（标题、内容、来源、时间） |

**注意**：新闻质量参差不齐，可能包含 AI 生成的低质量内容和仅因代码关联的不相关新闻。分析时需人工/AI 过滤。

### 宏观经济指标

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `macro_china_pmi()` | ~15s | 制造业/非制造业 PMI 月度数据 |
| `macro_china_cpi_monthly()` | ~15s | CPI 月率 |

**注意**：宏观数据有 1-2 个月发布滞后。

---

## 数据源四：company-profile 技能新增接口

以下接口由 `company-profile` 技能引入，用于获取公司画像数据。

### 公司基本信息

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_profile_cninfo(symbol)` | ~5s | 公司名称、行业、主营业务描述、经营范围、成立/上市日期、注册地、公司简介 |

`symbol` 为 6 位纯数字代码。

### 主营构成（营收拆分）

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_zygc_em(symbol)` | ~3s | 按产品/行业/地区分类的营收、成本、利润、毛利率，多个报告期 |

`symbol` 需要 SH/SZ 前缀（如 `SH688267`）。返回最近多期数据，可用于分析营收结构变化趋势。

### 十大股东

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_main_stock_holder(stock)` | ~3s | 十大股东名称、持股数量、持股比例、股本性质、股东总数、人均持股 |

`stock` 为 6 位纯数字代码。返回多个报告期数据。

### 业绩快报

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_yjkb_em(date)` | ~4s | 全市场业绩快报（营收、净利润、同比增速、EPS、ROE） |

`date` 为报告期（如 `20251231`）。业绩快报通常早于年报/季报披露。

### 业绩预告

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_yjyg_em(date)` | ~4s | 全市场业绩预告（预告类型、预测数值、变动幅度、变动原因） |

### 估值历史（百度）

| 接口 | 耗时 | 返回内容 |
|------|------|---------|
| `stock_zh_valuation_baidu(symbol, indicator, period)` | ~3s | 个股估值指标历史数据（日频） |

`indicator` 可选值：`"总市值"` / `"市盈率(TTM)"` / `"市净率"` / `"市销率(TTM)"`
`period` 可选值：`"近一年"` / `"近三年"` / `"近五年"` / `"近十年"` / `"全部"`

适用于计算估值分位数，判断当前估值在历史中的位置。
