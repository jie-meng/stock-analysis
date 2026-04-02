# 股票分析工具

一个全面的股票市场分析和投资研究工具包，采用模块化技能和自主代理设计，适用于专业投资者和非技术用户。

## 功能特点

- **模块化技能**：即用型分析功能，涵盖基本面、技术面和情绪面分析
- **自主代理**：预构建的工作流程，用于筛选、监控、风险评估和报告生成
- **自定义创建**：易于创建个性化技能和代理的框架
- **公共API集成**：连接流行金融数据提供商
- **用户友好**：专为非技术投资者设计，配置简单

## 快速开始

1. **安装软件包**：
   ```bash
   # 安装完整功能（技术分析 + 可视化）
   pip install -e .[full]
   
   # 或仅安装核心功能
   pip install -e .
   ```

2. **配置API密钥**：
   ```bash
   cp config.example.json config.json
   # 编辑 config.json 文件，填入您的API密钥
   ```

3. **运行代理**：
   ```bash
   stock-analysis --help
   ```

## 架构

### 技能 (`.agents/skills/`)
独立分析功能：
- **fundamental_analysis**：财务比率、收入、利润率分析
- **technical_analysis**：移动平均线、RSI、MACD技术指标
- **sentiment_analysis**：新闻和社交媒体情绪分析
- **risk_metrics**：VaR、贝塔、波动率风险计算

### 代理 (`.agents/agents/`)
自主工作流程：
- **stock-screener**：基于可自定义条件的股票筛选
- **portfolio-monitor**：跟踪投资组合表现和配置
- **risk-assessor**：多层面投资风险评估
- **market-scanner**：识别市场机会和异常情况
- **report-writer**：生成全面分析报告
- **alert-manager**：基于市场条件的触发通知

## 使用示例

### 基础股票筛选
```python
from agents.stock_screener import screen_stocks

results = screen_stocks(
    criteria={
        "pe_ratio": {"max": 25},
        "market_cap": {"min": 1000000000},
        "dividend_yield": {"min": 0.02}
    }
)
```

### 投资组合监控
```python
from agents.portfolio_monitor import monitor_portfolio

report = monitor_portfolio(
    holdings=[
        {"symbol": "AAPL", "shares": 100},
        {"symbol": "MSFT", "shares": 50}
    ],
    benchmark="SPY"
)
```

### 风险评估
```python
from agents.risk_assessor import assess_risk

risk_metrics = assess_risk(
    symbol="AAPL",
    confidence_level=0.95,
    period="1y"
)
```

## 创建自定义技能

1. 在 `.agents/skills/` 目录下创建新目录
2. 遵循技能模板结构：
   ```
   my_skill/
   ├── __init__.py
   ├── main.py
   └── README.md
   ```
3. 实现您的分析逻辑
4. 在代理中使用或与他人分享

## 创建自定义代理

1. 在 `.agents/agents/` 目录下创建新目录
2. 遵循代理模板结构：
   ```
   my_agent/
   ├── __init__.py
   ├── agent.py
   ├── config.json
   └── README.md
   ```
3. 组合现有技能或创建新技能
4. 安排运行计划或设置条件触发

## API配置

支持的金融数据提供商：
- **Yahoo Finance**（免费）- 默认
- **Alpha Vantage**（提供免费层级）
- **Quandl**（有限免费层级）
- **IEX Cloud**（提供免费层级）

## 目录结构

```
stock-analysis/
├── .agents/
│   ├── skills/          # 分析技能
│   │   ├── fundamental_analysis/
│   │   ├── technical_analysis/
│   │   └── sentiment_analysis/
│   └── agents/          # 自主代理
│       ├── stock-screener/
│       ├── portfolio-monitor/
│       └── risk-assessor/
├── config.example.json  # 配置模板
├── pyproject.toml       # 项目依赖
├── AGENTS.md           # 架构指南
└── README.md           # 本文件
```

## 应用场景

- **快速股票筛选**：按基本面指标筛选股票
- **技术择时**：识别买卖点
- **风险管理**：评估投资组合风险
- **市场情绪**：分析新闻和社交媒体
- **自动报告**：生成定期分析报告
- **自定义策略**：实现专有分析方法

## 获取帮助

- 查看 `AGENTS.md` 了解架构和指南
- 每个技能和代理都有自己的README，包含使用示例
- 使用技能创建工具构建新的分析方法

## 安全提示

- 切勿提交API密钥或敏感数据
- 使用环境变量存储密钥
- 如有需要，可保持分析方法的私密性

## 许可证

MIT许可证 - 详情请参阅LICENSE文件。