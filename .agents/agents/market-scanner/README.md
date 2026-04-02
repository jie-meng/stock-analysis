# 市场扫描代理

## 用途
扫描市场异常活动、动量变化和多个时间框架内的潜在机会。

## 功能特点
- **成交量扫描**：异常成交量激增、相对成交量
- **价格变动**：涨幅榜、跌幅榜、跳空高开/低开
- **技术突破**：支撑/阻力位突破、形态完成
- **行业轮动**：识别领先和落后行业
- **期权活动**：异常期权流动、高未平仓合约

## 使用方法
```bash
# 每日市场扫描
python scan.py --type daily

# 实时扫描
python scan.py --type realtime --interval 5m

# 自定义扫描
python scan.py --config scan_config.json
```

## 扫描类型

### 每日扫描
- 按百分比排序的涨幅榜/跌幅榜
- 成交量突破（>2倍平均）
- 52周新高/新低
- 财报公告

### 日内扫描
- 动量股票
- 反转形态
- 异常期权活动
- 暗池交易

## 配置
```json
{
  "scanners": {
    "volume_breakout": {"threshold": 2.0},
    "price_momentum": {"period": "1h", "min_change": 0.03},
    "options_flow": {"min_premium": 100000}
  },
  "filters": {
    "min_price": 5.00,
    "min_volume": 500000,
    "exclude_symbols": ["SPY", "QQQ"]
  }
}
```