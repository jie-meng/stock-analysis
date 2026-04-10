# 自定义技能创建指南

你可以创建自己的分析技能，让 AI 助手在你需要时自动调用。本文档介绍技能的结构规范和创建方法。

---

## 什么是技能

技能是一个独立的功能模块，包含：
- **SKILL.md**：告诉 AI 这个技能做什么、什么时候用、怎么用
- **scripts/**（可选）：执行具体分析的 Python 脚本

当你向 AI 提问时，AI 会根据 SKILL.md 的描述判断是否需要调用这个技能。

---

## 技能目录结构

```
.agents/skills/
└── 你的技能名/
    ├── SKILL.md          # 必须 — 技能说明文件
    └── scripts/          # 可选 — 工具脚本
        └── xxx.py
```

技能名使用小写英文和连字符，如 `value-stock-screener`、`white-spirit-analysis`。

---

## SKILL.md 规范

### 必须的 YAML 头部

```yaml
---
name: 技能名称
description: >
  技能说明。包含两部分：
  1. 这个技能做什么（功能描述）
  2. 什么时候触发（触发条件和关键词）
---
```

#### name 字段

- 小写英文字母、数字和连字符
- 最多 64 个字符
- 示例：`value-stock-screener`、`dividend-analyzer`

#### description 字段

这是最关键的字段 — AI 靠它决定什么时候使用你的技能。

**好的写法：**

```yaml
description: >
  基于价值投资理念筛选 A 股股票。筛选条件：ROE>15%、PE<行业平均、
  连续3年盈利增长、资产负债率<50%。
  当用户提到价值投资、价值选股、ROE筛选、低估值选股时触发。
  触发短语："价值选股"、"帮我筛股票"、"低估值"、"value investing"。
```

**不好的写法：**

```yaml
description: 分析股票
```

原因：太模糊，AI 无法判断什么时候该用这个技能。

### 正文内容

SKILL.md 正文告诉 AI 具体怎么使用这个技能：

```markdown
# 技能标题

一句话说明功能。

## 前置条件

需要什么依赖。

## 使用方式

具体命令和参数。

## 注意事项

使用时需要注意什么。
```

**正文控制在 500 行以内**，保持简洁。AI 已经很聪明，不需要解释基础概念。

---

## 创建技能的两种方式

### 方式一：让 AI 帮你创建（推荐）

直接告诉 AI 你的需求，它会帮你生成整个技能：

```
你：帮我创建一个技能，用来筛选高股息率的股票。
    条件是：股息率 > 3%，连续 5 年分红，PE < 20
```

AI 会自动在 `.agents/skills/` 下创建对应的目录和文件。

### 方式二：手动创建

1. 在 `.agents/skills/` 下创建目录
2. 编写 SKILL.md
3. 编写脚本（如需要）

---

## 示例：创建一个完整技能

假设你想做一个"低估值价值股筛选"技能：

### 目录

```
.agents/skills/value-stock-screener/
├── SKILL.md
└── scripts/
    └── screener.py
```

### SKILL.md

```markdown
---
name: value-stock-screener
description: >
  基于价值投资理念筛选 A 股，条件：ROE连续3年>15%、PE<行业平均水平、
  最近一季营收同比增长>10%、资产负债率<50%。
  当用户提到价值选股、低估值筛选、ROE 筛选、巴菲特选股时触发。
  触发短语："价值选股"、"帮我选股"、"低估值"、"好公司便宜价"。
---

# 低估值价值股筛选

按价值投资标准筛选 A 股股票。

## 前置条件

\`\`\`bash
pip install akshare pandas
\`\`\`

## 使用方式

\`\`\`bash
python .agents/skills/value-stock-screener/scripts/screener.py [--roe-min 15] [--pe-max 20]
\`\`\`

## 筛选标准

| 条件 | 默认值 | 说明 |
|------|--------|------|
| ROE | > 15% | 连续 3 年 |
| PE | < 行业平均 | TTM |
| 营收增速 | > 10% | 最近一季同比 |
| 负债率 | < 50% | 最新报告期 |
```

### scripts/screener.py

脚本负责实际的数据获取和筛选逻辑，输出结果到标准输出。

---

## 纯指令型技能（无脚本）

不是所有技能都需要脚本。有些技能只是给 AI 一套分析框架：

```markdown
---
name: warren-buffett-analysis
description: >
  用巴菲特价值投资框架分析一家公司。关注护城河、管理层、长期盈利能力。
  当用户提到巴菲特、价值投资分析、护城河分析时触发。
---

# 巴菲特价值投资分析框架

按以下维度分析（使用 financial-data-analysis 技能获取数据）：

## 1. 护城河分析
- 品牌价值：毛利率是否持续高于同行？
- 转换成本：客户是否难以更换？
- 网络效应：用户越多产品越有价值？
- 成本优势：规模效应是否显著？

## 2. 管理层评估
- ROE 是否持续 > 15%（管理层运用资本的效率）
- 自由现金流是否持续为正
- 是否大量举债扩张

## 3. 估值判断
- 当前 PE 是否低于历史平均
- PB 是否合理
- 用 DCF 估算内在价值（假设增长率和折现率）

## 4. 安全边际
- 当前价格相对于估算内在价值的折让幅度
- 建议安全边际 > 30%
```

这种技能不需要脚本，AI 会按照框架调用其他技能获取数据，然后按框架组织分析。

---

## 共享模块与数据源

## 行情数据：ashare.py（各 skill 独立）

每个需要行情数据的 skill 在自己的 `scripts/` 目录下有一份 `ashare.py`，提供单只股票的行情获取（新浪/腾讯双源，<1 秒响应）。skill 脚本通过 `__file__` 定位引用：

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ashare import get_price, get_realtime
```

这样 skill 可以独立安装到任意目录，不依赖项目根结构。新建需要行情数据的 skill 时，从现有 skill 的 `scripts/ashare.py` 复制一份到新 skill 的 `scripts/` 目录即可。

### 数据接口选型

创建涉及数据获取的脚本前，先阅读 `docs/data-sources.md`，了解各接口的能力和性能。核心原则：

- **单只股票行情** → `ashare.py`（快，<1s）
- **批量/全市场数据** → akshare 批量接口（yjbb/fhps/zcfz 等）
- **板块成分股** → 直调东财 clist API（绕过 akshare 的页间 sleep）
- **不要在循环里逐个调用慢接口**（如 `stock_financial_abstract_ths`），筛选场景用批量接口 + merge

详见 [数据源参考手册](data-sources.md)。

---

## 技能创建清单

创建完技能后，检查以下几点：

- [ ] `name` 字段使用小写英文和连字符
- [ ] `description` 包含功能说明和触发条件
- [ ] `description` 包含中英文触发短语
- [ ] SKILL.md 正文简洁，不超过 500 行
- [ ] 如有脚本，脚本支持命令行调用
- [ ] 脚本的依赖包已注明
- [ ] 输出格式为纯文本或 Markdown（便于 AI 解读）
- [ ] 如需行情数据，已将 `ashare.py` 复制到 skill 的 `scripts/` 目录，并用 `os.path.dirname(os.path.abspath(__file__))` 引用
- [ ] 数据接口选型参考了 `docs/data-sources.md`
