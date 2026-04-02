# 报告生成代理

## 用途
生成全面的投资分析报告，支持多种格式，整合来自其他代理的数据。

## 功能特点
- **多源整合**：整合来自筛选器、监控器、风险评估器的数据
- **模板系统**：可自定义的报告模板
- **多种格式**：Markdown、PDF、HTML、Excel
- **定时报告**：每日、每周、每月自动生成报告
- **图表生成**：自动创建可视化图表

## 使用方法
```bash
# 生成单只股票报告
python report.py --symbol AAPL --type fundamental

# 生成投资组合报告
python report.py --portfolio portfolio.json --format pdf

# 安排每周报告
python report.py --schedule weekly --email user@example.com
```

## 报告类型

### 股票分析报告
- 公司概况和业务模式
- 财务分析（收入、利润率、增长）
- 技术分析（图表、指标）
- 估值指标和比较
- 风险评估
- 分析师共识

### 投资组合报告
- 表现总结
- 资产配置分析
- 风险指标
- 再平衡建议
- 股息收入跟踪

### 市场概览报告
- 市场指数表现
- 行业分析
- 经济指标
- 市场情绪

## 模板
位于 `templates/` 目录：
- `stock_analysis.md`
- `portfolio_summary.md`
- `market_overview.md`

## 配置
```json
{
  "output_dir": "reports",
  "templates_dir": "templates",
  "default_format": "markdown",
  "email_settings": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "reports@example.com"
  }
}
```