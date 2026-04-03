# 选股筛选器（stock-screener）

从 A 股全市场 5000+ 只股票中，按条件筛选出值得关注的标的。

---

## 为什么这样设计

### 问题

投资者选股时有三类典型需求：

1. **可量化条件** — PE < 20、股息率 > 3%、ROE > 15%
2. **多指标组合判断** — "经营状况良好"（ROE + 负债率 + 利润增速交叉验证）
3. **语义/主题条件** — "符合十五五规划"（无法用数值表达，需要人工定义范围）

纯通用的参数化筛选器能处理第 1 类，但无法理解"十五五规划"；而每个需求独立写一个脚本，又会产生大量重复代码。

### 方案：一个引擎 + 预设策略 + 自定义模式

```
┌──────────────────────────────────────────────────────┐
│                    screener.py                       │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ high-dividend│  │value-quality│  │ policy-theme │ │
│  │  (预设策略)  │  │ (预设策略)  │  │ (预设策略)   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ │
│         │                │                │          │
│         ▼                ▼                ▼          │
│  ┌────────────────────────────────────────────────┐  │
│  │      并发批量获取 → merge → 向量化筛选引擎      │  │
│  └────────────────────────────────────────────────┘  │
│         ▲                                            │
│         │  可与策略组合，用户参数覆盖策略默认值      │
│  ┌──────┴──────┐                                     │
│  │ 自定义参数  │                                     │
│  └─────────────┘                                     │
│                                                      │
│  sectors.json ← 政策主题板块映射（人工维护）          │
└──────────────────────────────────────────────────────┘
```

### 架构：并发批量获取 → merge → 向量化筛选

akshare 的大部分接口是批量返回全市场数据的（一次调用返回几千只股票），但每个接口只覆盖部分字段。核心思路是**并发调用多个批量接口，用 pandas merge 合并为宽表，然后向量化过滤**。

```
                    ┌─ 东财 clist API ──→ 板块成分股 + PE/PB/市值
    并发线程池 ──────┤─ stock_yjbb_em ───→ ROE/EPS/利润增速/营收增速
    (max_workers=5) ├─ stock_fhps_em ───→ 股息率
                    ├─ stock_zcfz_em ───→ 资产负债率
                    └─ stock_history_dividend → 分红次数
                              │
                              ▼
                    merge on 代码 → 宽表
                              │
                              ▼
                    向量化 boolean mask 筛选 → 排序 → 输出
```

关键优化点：
- **板块接口直调东财 API**，绕过 akshare 的 `fetch_paginated_data`（该函数每页 sleep 0.5-1.5s），27 个板块并发获取 ~60s
- **财务数据接口并发**：yjbb/fhps/zcfz/divhist 四个接口同时跑，受最慢的 yjbb 限制 ~80s
- 板块获取和财务获取**同时并发**，总耗时 = max(板块, 财务) ≈ 80s

---

## 三个预设策略

### high-dividend — 高分红策略

**投资逻辑**：寻找持续高分红、估值合理的稳健型标的。适合追求现金回报的投资者。

| 条件 | 阈值 | 说明 |
|------|------|------|
| 股息率 | ≥ 3% | 根据最新一次派息和当前股价计算 |
| 连续分红 | ≥ 3 次 | 历史实施过的分红次数 |
| PE | 0 ~ 30 | 排除亏损股和泡沫 |
| 市值 | ≥ 50 亿 | 流动性保障 |

按股息率降序排序。

### value-quality — 价值优选策略

**投资逻辑**：低估值买入经营优秀的公司 — 好公司 + 合理价格。

| 条件 | 阈值 | 说明 |
|------|------|------|
| PE | 0 ~ 25 | 估值不贵 |
| PB | ≤ 5 | 资产端未严重高估 |
| ROE | ≥ 12% | 资本回报能力达标（加权净资产收益率） |
| 净利润增速 | ≥ 0% | 盈利至少没有恶化 |
| 资产负债率 | ≤ 60% | 财务安全 |
| 市值 | ≥ 80 亿 | 有一定规模 |

按 ROE 降序排序。

### policy-theme — 政策主题策略

**投资逻辑**：在政策重点支持方向中，筛选估值合理的标的。

可用主题（`--theme` 参数）：

| 主题 | 涵盖板块 |
|------|---------|
| 新能源 | 光伏概念、储能概念、新能源车、氢能源、核能核电 |
| 半导体 | 半导体概念、第三代半导体、国产芯片、存储芯片 |
| 人工智能 | 人工智能、AIGC概念、算力概念、AI芯片、AI应用、AI智能体 |
| 高端制造 | 机器人概念、人形机器人、新材料、商业航天、军工 |
| 数字经济 | 数据要素、大数据、信创、数据安全 |
| 生物医药 | 合成生物、生物疫苗、AI制药（医疗） |
| 绿色经济 | 碳中和 |

按 PE 升序排序。不指定 `--theme` 则扫描全部主题。

---

## 使用方式

### 在 AI 对话中使用（推荐）

直接用自然语言提问，AI 会自动调用此技能：

```
你：帮我筛选高分红的股票
你：有没有低估值、经营好的股票？
你：十五五规划里半导体方向有哪些值得关注的？
你：帮我选股，PE 低于 15，ROE 大于 20
```

### 直接运行脚本

```bash
# 预设策略
python .agents/skills/stock-screener/scripts/screener.py --strategy high-dividend
python .agents/skills/stock-screener/scripts/screener.py --strategy value-quality
python .agents/skills/stock-screener/scripts/screener.py --strategy policy-theme --theme 半导体

# 策略 + 自定义条件覆盖（可组合）
python .agents/skills/stock-screener/scripts/screener.py --strategy policy-theme \
  --pe-max 20 --div-yield-min 2 --roe-min 10 --debt-ratio-max 60

# 纯自定义
python .agents/skills/stock-screener/scripts/screener.py \
  --pe-max 20 --roe-min 15 --debt-ratio-max 50

# 限定单板块
python .agents/skills/stock-screener/scripts/screener.py \
  --sector 光伏概念 --pe-max 20 --roe-min 10
```

### 参数速查

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--strategy` | 预设策略名 | — |
| `--theme` | 政策主题方向 | 全部 |
| `--sector` | 限定单个概念板块 | — |
| `--top` | 输出前 N 只 | 30 |
| `--sort` | 排序字段 | 策略默认 |
| `--pe-max` / `--pe-min` | PE 范围 | — / 0 |
| `--pb-max` | PB 上限 | — |
| `--roe-min` | ROE 下限 (%) | — |
| `--div-yield-min` | 股息率下限 (%) | — |
| `--debt-ratio-max` | 负债率上限 (%) | — |
| `--revenue-growth-min` | 营收增速下限 (%) | — |
| `--profit-growth-min` | 净利增速下限 (%) | — |
| `--consecutive-div-years` | 最少分红次数 | — |
| `--min-market-cap` | 最低市值（亿） | 50 |
| `--include-st` | 包含 ST 股票 | 默认排除 |

---

## 数据源说明

| 接口 | 数据内容 | 耗时 | 调用方式 |
|------|---------|------|---------|
| 东财 clist API | 板块成分股 + PE/PB/市值 | ~60s（27 板块并发） | 直调 HTTP，绕过 akshare sleep |
| `stock_yjbb_em` | ROE/EPS/利润增速/营收增速/毛利率 | ~80s | akshare 批量 |
| `stock_fhps_em` | 股息率 | ~28s | akshare 批量 |
| `stock_zcfz_em` | 资产负债率 | ~40s | akshare 批量 |
| `stock_history_dividend` | 分红次数/累计股息 | ~3s | akshare 批量 |
| `stock_zh_a_spot_em` | 全市场 PE/PB/市值 | ~7min | 备选，仅无板块时使用 |

ROE 使用东财业绩报表的**加权净资产收益率**，准确度与同花顺等平台一致。

---

## 性能参考

| 场景 | 耗时 |
|------|------|
| 单板块 `--sector 光伏概念` | ~30 秒 |
| 单主题 `--theme 新能源` + 财务条件 | ~1.5 分钟 |
| 全主题 `--strategy policy-theme` + 全部条件 | ~1.5 分钟 |
| 全市场（无 theme/sector） | ~8 分钟 |

---

## 文件结构

```
stock-screener/
├── SKILL.md           # AI 技能描述（触发条件、参数定义）
├── README.md          # 本文件
└── scripts/
    ├── screener.py    # 筛选引擎
    └── sectors.json   # 政策主题板块映射
```

---

## 维护 sectors.json

当政策方向发生变化（如新增"低空经济"主题），编辑 `sectors.json` 即可：

```json
{
  "低空经济": {
    "description": "无人机、eVTOL 及低空空域管理",
    "sub_themes": {
      "无人机": {
        "concept_boards": ["无人机"]
      }
    }
  }
}
```

`concept_boards` 中的名称必须是东方财富概念板块的**精确名称**。可以通过 akshare 查询可用板块：

```python
import akshare as ak
df = ak.stock_board_concept_name_em()
print(df["板块名称"].tolist())
```

---

## 筛选结果的使用建议

筛选结果是进一步分析的**起点**，不是终点。建议的工作流：

1. 运行筛选器，得到候选列表
2. 对感兴趣的个股，用 `financial-data-analysis` 技能看详细财务数据
3. 用 `technical-indicator` 技能判断技术面位置（是否在高位/低位）
4. 用 `stock-comparison` 技能做同行对比
5. 用 `investment-notebook` 技能记录分析结论
