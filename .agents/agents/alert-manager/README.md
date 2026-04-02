# 警报管理代理

## 用途
监控市场条件并根据用户定义的规则触发警报，实现及时的投资决策。

## 功能特点
- **价格警报**：突破上方/下方价位、百分比变动
- **技术指标警报**：指标交叉、形态完成
- **成交量警报**：异常成交量、相对成交量激增
- **基本面警报**：财报、股息、分析师变动
- **投资组合警报**：配置偏离、损失限额

## 使用方法
```bash
# 添加价格警报
python alerts.py add --symbol AAPL --type price --above 180.00

# 列出活动警报
python alerts.py list

# 运行警报检查器
python alerts.py check --interval 5m

# 移除警报
python alerts.py remove --id 12345
```

## 警报类型

### 价格警报
```json
{
  "symbol": "AAPL",
  "type": "price",
  "condition": "above",
  "value": 180.00,
  "action": ["email", "sms"]
}
```

### 技术指标警报
```json
{
  "symbol": "MSFT",
  "type": "technical",
  "indicator": "RSI",
  "condition": "below",
  "value": 30,
  "period": "1d"
}
```

### 投资组合警报
```json
{
  "type": "portfolio",
  "metric": "total_loss",
  "threshold": -0.10,
  "action": ["email"]
}
```

## 通知渠道
- 电子邮件
- 短信（通过Twilio）
- Slack/Discord网页钩子
- 推送通知

## 配置
```json
{
  "check_interval": "1m",
  "notifications": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "sender": "alerts@example.com",
      "recipients": ["user@example.com"]
    },
    "slack": {
      "webhook_url": "https://hooks.slack.com/..."
    }
  },
  "max_alerts_per_day": 50
}
```