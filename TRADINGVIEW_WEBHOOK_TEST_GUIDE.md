# TradingView Webhook 测试指南

## 🚀 快速测试

### 1. 基础测试命令
```bash
# 快速测试Signal和Trade数据
python quick_webhook_test.py

# 完整测试工具
python test_tradingview_webhook.py
```

### 2. 手动测试命令
```bash
# 使用curl测试Signal数据
curl -X POST http://localhost:5000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "timeframe": "1h",
    "CVDsignal": "cvdAboveMA",
    "pmaText": "PMA Strong Bullish",
    "AIbandsignal": "blue uptrend"
  }'

# 使用curl测试Trade数据
curl -X POST http://localhost:5000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "action": "buy",
    "quantity": 100,
    "takeProfit": {"limitPrice": 195.00},
    "stopLoss": {"stopPrice": 182.50},
    "extras": {
      "indicator": "EMA Cross",
      "timeframe": "1h",
      "oscrating": 75,
      "trendrating": 85,
      "risk": 2
    }
  }'
```

## 📊 三种数据类型详解

### 1. Signal数据（技术指标信号）
```json
{
  "symbol": "AAPL",
  "timeframe": "1h",
  "CVDsignal": "cvdAboveMA",
  "choppiness": "35.8",
  "adxValue": "62.1",
  "BBPsignal": "bullpower",
  "RSIHAsignal": "BullishHA",
  "SQZsignal": "squeeze",
  "choppingrange_signal": "trending",
  "rsi_state_trend": "Bullish",
  "center_trend": "Strong Bullish",
  "adaptive_timeframe_1": "60",
  "adaptive_timeframe_2": "240",
  "MAtrend": "1",
  "MAtrend_timeframe1": "1",
  "MAtrend_timeframe2": "1",
  "MOMOsignal": "bullishmomo",
  "Middle_smooth_trend": "Bullish +",
  "TrendTracersignal": "1",
  "TrendTracerHTF": "1",
  "pmaText": "PMA Strong Bullish",
  "trend_change_volatility_stop": "186.25",
  "AIbandsignal": "blue uptrend",
  "HTFwave_signal": "Bullish",
  "wavemarket_state": "Long Strong",
  "ewotrend_state": "Strong Bullish"
}
```

### 2. Trade数据（开仓交易）
```json
{
  "ticker": "AAPL",
  "action": "buy",
  "quantity": 150,
  "takeProfit": {"limitPrice": 198.75},
  "stopLoss": {"stopPrice": 181.50},
  "extras": {
    "indicator": "Golden Cross Signal",
    "timeframe": "1h",
    "oscrating": 78,
    "trendrating": 88,
    "risk": 2
  }
}
```

### 3. Close数据（平仓操作）
```json
{
  "ticker": "AAPL",
  "action": "sell",
  "sentiment": "flat",
  "extras": {
    "indicator": "TrailingStop Exit Long",
    "timeframe": "1h"
  }
}
```

## 🔄 交易逻辑说明

### 开仓交易识别
- 必须包含 `takeProfit` 和 `stopLoss`
- `action`: "buy" (做多) 或 "sell" (做空)
- 无 `sentiment: "flat"` 字段

### 平仓交易识别
- 包含 `sentiment: "flat"`
- `flat + sell` = 退出多仓
- `flat + buy` = 退出空仓

## 📋 测试检查清单

### ✅ Signal数据测试
- [ ] 数据成功存储到数据库
- [ ] `data_type` 正确识别为 "signal"
- [ ] 技术指标正确解析（无"状态未知"）
- [ ] 时间框架正确提取

### ✅ Trade数据测试
- [ ] 数据成功存储到数据库
- [ ] `data_type` 正确识别为 "trade"
- [ ] 止损止盈价格正确存储
- [ ] OscRating/TrendRating正确提取

### ✅ Close数据测试
- [ ] 数据成功存储到数据库
- [ ] `data_type` 正确识别为 "close"
- [ ] 平仓方向正确识别

### ✅ 报告生成测试
- [ ] 在Discord报告频道测试股票请求
- [ ] 生成包含技术指标的完整报告
- [ ] 包含"📊TDindicator Bot 交易解读"部分
- [ ] 交易类型和方向正确显示

## 🛠️ 故障排除

### 常见问题
1. **连接失败**: 确保API服务器运行在5000端口
2. **数据不存储**: 检查数据库连接状态
3. **解析错误**: 验证JSON格式正确性
4. **报告无交易解读**: 确保有匹配的signal+trade数据

### 调试命令
```bash
# 检查API服务器状态
curl http://localhost:5000/api/health

# 查看数据库中的最新数据
python -c "
from models import get_db_session, TradingViewData
session = get_db_session()
latest = session.query(TradingViewData).order_by(TradingViewData.received_at.desc()).limit(5).all()
for data in latest:
    print(f'{data.symbol} {data.timeframe} {data.data_type} {data.action}')
session.close()
"

# 测试报告生成
python -c "
from gemini_report_generator import GeminiReportGenerator
generator = GeminiReportGenerator()
report = generator.generate_enhanced_report('AAPL', '1h')
print(f'报告长度: {len(report)}')
print(f'包含交易解读: {\"📊TDindicator Bot 交易解读\" in report}')
"
```

## 🎯 完整测试流程

1. **启动服务**: 确保Discord Bot和API服务器运行
2. **发送Signal**: 测试技术指标数据接收
3. **发送Trade**: 测试开仓交易数据接收
4. **验证存储**: 检查数据库存储正确性
5. **测试报告**: 在Discord生成完整报告
6. **验证解读**: 确认交易解读部分正确显示

## 📱 Discord测试

发送Signal和Trade数据后，在Discord报告频道发送：
```
AAPL 1h
```

期望看到包含以下部分的完整报告：
- 📈 技术指标概览
- 📉 趋势分析
- 💡 投资建议
- 📊TDindicator Bot 交易解读
- ⚠️ 风险提示

---

现在TradingView webhook集成已完全就绪，可以接收真实的webhook数据！