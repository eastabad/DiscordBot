# 🎯 Report频道设置说明

## 快速设置步骤

### 1. 获取频道ID
- 在Discord中启用开发者模式（设置 → 高级 → 开发者模式）
- 右键点击您要设置为report频道的频道
- 选择"复制频道ID"

### 2. 配置环境变量
在Replit环境变量中添加以下任一配置：

**单个频道：**
```
REPORT_CHANNEL_ID=您的频道ID
```

**多个频道：**
```
REPORT_CHANNEL_IDS=频道ID1,频道ID2,频道ID3
```

### 3. 重启机器人
- 重启Discord Bot with API workflow
- 检查日志确认配置生效

## 🔍 验证配置

正确配置后，机器人启动日志会显示：
```
Report频道IDs: 1234567890123456789
```

## 🧪 测试功能

在配置的report频道中发送：
```
AAPL 15m
TSLA 1h
NVDA 4h
```

机器人将自动生成AI技术分析报告并通过私信发送。

---

**配置您的report频道ID后，即可享受专业的AI股票分析服务！**