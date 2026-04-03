# Stock Analysis — A 股 AI 分析助手

一个面向投资者的 AI 分析工作空间。用 [opencode](https://opencode.ai) 打开，用自然语言提问，AI 自动调用内置技能帮你获取行情、分析财务、计算技术指标。

**不需要写代码。** 你只需要会打字提问。

---

## 快速开始

```bash
# 1. 安装依赖
pip install -Ur requirements.txt

# 2. 进入项目目录，启动 opencode
cd stock-analysis
opencode

# 3. 开始提问
# > 帮我看看贵州茅台最近的走势和技术指标
```

> 需要 Python 3.11+。首次使用请参考 [安装指南](docs/installation.md) 从零配置环境。

---

## 内置技能

| 技能 | 功能 | 问法示例 |
|------|------|----------|
| **A 股行情数据** | 获取历史 K 线、实时报价 | "看看茅台最近 60 天走势" |
| **财务数据分析** | 财报数据、PE/ROE 等指标 | "分析宁德时代的财务状况" |
| **技术指标分析** | MA/MACD/RSI/KDJ/BOLL 计算 | "平安银行的 MACD 什么情况" |
| **股票对比分析** | 多股行情和财务横向对比 | "对比茅台和五粮液" |
| **选股筛选器** | 高分红/价值优选/政策主题选股（并发架构，~1.5 分钟） | "帮我选几只高分红股票" |
| **投资笔记管理** | 保存和查阅分析记录 | "把这次分析记下来" |

---

## 使用方式

### 方式一：提问分析

在 opencode 中直接提问，AI 自动识别你的意图并调用对应技能：

```
你：帮我全面分析一下比亚迪

AI：（自动获取行情数据 → 计算技术指标 → 获取财务数据 → 输出综合分析报告）
```

更多示例和详细说明请参考 **[使用指南](docs/usage-guide.md)**。

### 方式二：选股筛选

内置三种选股策略，并发获取数据 + 向量化筛选（全主题约 1.5 分钟）：

```
你：帮我筛选高分红的股票
你：有没有低估值、经营好的公司？
你：十五五规划半导体方向有哪些值得关注的？
```

AI 并发获取板块行情 + 财务数据，向量化筛选后输出候选列表。详细说明见 **[选股筛选器文档](.agents/skills/stock-screener/README.md)**。

### 方式三：创建自定义技能

每个投资者都有自己的分析方法。你可以让 AI 把你的策略做成可复用的技能：

```
你：帮我创建一个技能，用巴菲特的框架分析一家公司
```

AI 会在 `.agents/skills/` 下创建新技能，以后你说对应的关键词就能直接用。

详细规范请参考 **[自定义技能创建指南](docs/custom-skill-guide.md)**。

---

## 项目结构

```
stock-analysis/
├── .agents/skills/               # 分析技能
│   ├── ashare-price-data/        # A 股行情数据
│   ├── financial-data-analysis/  # 财务数据分析
│   ├── technical-indicator/      # 技术指标分析
│   ├── stock-comparison/         # 股票对比分析
│   ├── stock-screener/           # 选股筛选器
│   └── investment-notebook/      # 投资笔记管理
├── notes/                        # 投资笔记
│   ├── stocks/                   #   按股票归档
│   ├── market/                   #   市场观察
│   └── strategy/                 #   策略思考
├── docs/                         # 文档
│   ├── installation.md           # 安装指南
│   ├── usage-guide.md            # 使用指南
│   └── custom-skill-guide.md     # 自定义技能指南
├── AGENTS.md                     # AI 助手行为规则
├── requirements.txt              # Python 依赖
├── LICENSE                       # MIT 许可证
└── README.md                     # 本文件
```

---

## 文档

| 文档 | 说明 |
|------|------|
| [安装指南](docs/installation.md) | Python、opencode 安装（macOS / Windows / Linux） |
| [使用指南](docs/usage-guide.md) | 详细的提问示例和使用方法 |
| [自定义技能创建指南](docs/custom-skill-guide.md) | 如何创建自己的分析技能 |

---

## 数据来源

- **行情数据**：新浪财经、腾讯股票（公开接口，免费）
- **财务数据**：[akshare](https://github.com/akfamily/akshare)（开源，免费）

无需申请 API Key。

---

## 免责声明

本项目仅提供数据获取和分析工具，不构成任何投资建议。投资有风险，入市需谨慎。所有分析结果仅供参考，投资决策请基于你自己的判断。

---

## 许可证

[MIT](LICENSE)
