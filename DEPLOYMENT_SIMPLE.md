# 简化版Discord机器人部署指南

## 概述

此版本专注于三个核心功能：
- 📊 股票图表生成
- 📈 股票分析和预测  
- 🖼️ 图表图像分析
- 👥 用户请求限制管理
- 🧹 自动频道清理

API服务器已被移除，专注于纯Discord机器人功能。

## 环境变量配置

### 必需变量
```bash
DISCORD_TOKEN=your_discord_bot_token
```

### 图表服务变量
```bash
CHART_IMG_API_KEY=your_chart_img_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_id_sign
```

### 可选变量
```bash
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2  # 监控频道ID
WEBHOOK_URL=your_webhook_url  # 消息转发webhook（可选）
```

## 启动命令

简化版机器人使用以下命令启动：
```bash
python simple_bot.py
```

## 核心功能

### 1. 股票图表请求
- 格式：`AAPL,1h` 或 `NVDA 15m`
- 支持多种时间周期：1m, 5m, 15m, 30m, 1h, 4h, 1d
- 自动检测交易所（NASDAQ, NYSE, AMEX等）

### 2. 股票分析预测
- 格式：`@机器人 AAPL预测` 或 `TSLA prediction`
- 提供技术分析和趋势预测
- AI驱动的投资建议

### 3. 图表图像分析
- 上传图表图片并@机器人
- 自动识别技术指标和信号
- 提供专业的分析建议

### 4. 用户管理
- 每用户每日3次请求限制
- 管理员可设置VIP/豁免用户
- 命令：`!exempt_add`, `!exempt_remove`, `!exempt_list`

### 5. 频道清理
- 每日凌晨2点UTC自动清理
- 智能保留有价值的消息
- 管理员命令：`!cleanup_now`, `!cleanup_status`

## 部署优势

- ✅ 启动速度更快（无需启动API服务器）
- ✅ 资源占用更少
- ✅ 更简单的配置和维护
- ✅ 专注核心功能，稳定性更高
- ✅ 无端口依赖，纯Discord连接

## 注意事项

- 此版本移除了API服务器，无法与外部系统（如n8n）集成
- 如需API功能，请使用完整版本（app.py）
- 数据库连接用于用户限制和VIP管理功能
- 保留所有核心的股票分析功能