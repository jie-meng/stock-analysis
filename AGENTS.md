# 股票分析

本目录提供股票分析和投资研究的专业技能和代理，专为专业投资者和非技术用户设计。

## 架构

项目采用模块化架构，包含两个主要组件：

### 技能 (`.agents/skills/`)
执行特定任务的独立分析功能：
- **fundamental_analysis**：基本财务指标分析
- **technical_analysis**：价格和成交量技术指标
- **sentiment_analysis**：新闻和社交媒体情绪分析
- **risk_metrics**：风险计算工具

### 代理 (`.agents/agents/`)
组合多个技能的自主工作流程：
- **stock-screener**：基于条件的自动股票筛选
- **portfolio-monitor**：持续投资组合跟踪和分析
- **risk-assessor**：全面风险评估
- **market-scanner**：市场机会识别
- **report-writer**：自动报告生成
- **alert-manager**：基于条件的通知系统

## 使用模式

### 非技术用户
1. Fork本仓库
2. 在 `.env` 文件中配置API密钥
3. 通过简单命令使用现有代理
4. 在JSON配置文件中自定义参数

### 技术用户
1. 在 `.agents/skills/` 中创建新技能
2. 在 `.agents/agents/` 中构建新代理
3. 扩展现有功能
4. 通过Pull Request分享改进

## 技能结构

每个技能遵循以下模式：
```
skill_name/
├── __init__.py
├── main.py
└── README.md
```

## 代理结构

每个代理遵循以下模式：
```
agent_name/
├── __init__.py
├── agent.py
├── config.json
└── README.md
```

## API集成

支持的金融数据提供商：
- Yahoo Finance（免费）
- Alpha Vantage（提供免费层级）
- Quandl（有限免费层级）
- IEX Cloud（提供免费层级）

## 用户自定义

专业投资者可以：
- 修改现有代理以适应特定工作流程
- 创建新代理实现专有策略
- 组合代理进行全面分析
- 安排自动运行计划
- 设置自定义警报规则

## 安全提示

切勿硬编码API密钥或敏感数据。使用环境变量或安全配置文件。

## 快速开始

```bash
# 安装完整功能
pip install -e .[full]

# 或仅安装核心功能
pip install -e .
```