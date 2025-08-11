# n8n工作流配置指南

## Discord Bot API调用设置

### 1. 基本信息

**API服务器地址:** 您的Replit部署URL + `/api/send-chart`
例如: `https://your-replit-app.replit.app/api/send-chart`

**HTTP方法:** POST
**Content-Type:** application/json

### 2. n8n节点配置

#### 步骤1: 添加HTTP Request节点

1. 在n8n工作流中添加 **HTTP Request** 节点
2. 配置以下参数：

```
Method: POST
URL: https://your-replit-app.replit.app/api/send-chart
Headers:
  Content-Type: application/json
```

#### 步骤2: 配置请求体

在HTTP Request节点的Body部分，选择 **JSON** 格式，使用以下模板：

```json
[
  {
    "chartImgRequest": {
      "symbol": "{{ $json.symbol || 'NASDAQ:AAPL' }}",
      "interval": "{{ $json.interval || '1h' }}",
      "width": 1920,
      "height": 1080,
      "format": "png"
    },
    "discordPayload": {
      "content": "📊 {{ $json.symbol }} {{ $json.interval }} 图表分析",
      "attachments": [
        {
          "id": "0",
          "filename": "{{ $json.symbol }}_{{ $json.interval }}.png",
          "description": "Stock chart for {{ $json.symbol }} ({{ $json.interval }})",
          "url": "{{ $json.chartImageUrl || '' }}"
        }
      ]
    },
    "authorId": {{ $json.authorId || 1145170623354638418 }},
    "symbol": "{{ $json.symbol }}",
    "timeframe": "{{ $json.interval }}",
    "currentCount": 1,
    "channelId": "",
    "messageId": "",
    "guildId": ""
  }
]
```

### 3. 数据映射示例

如果您的上一个节点提供了以下数据：
```json
{
  "symbol": "GOOG",
  "interval": "15m",
  "authorId": 1145170623354638418,
  "chartImageUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### 4. 完整的n8n工作流示例

```
[Trigger] → [获取股票数据] → [生成图表] → [HTTP Request to Discord Bot] → [结果处理]
```

#### 节点详细配置：

**1. Webhook Trigger (触发器)**
- 监听外部请求
- 接收symbol、interval等参数

**2. 数据处理节点**
- 验证和格式化输入数据
- 准备图表请求参数

**3. 图表生成节点**
- 调用TradingView或其他图表API
- 获取图表图片的base64数据或URL

**4. HTTP Request节点 (调用Discord Bot)**
```
Method: POST
URL: https://your-replit-app.replit.app/api/send-chart
Headers:
  Content-Type: application/json
  
Body (JSON):
[
  {
    "chartImgRequest": {
      "symbol": "{{ $('数据处理').item.json.symbol }}",
      "interval": "{{ $('数据处理').item.json.interval }}",
      "width": 1920,
      "height": 1080,
      "format": "png"
    },
    "discordPayload": {
      "content": "📊 {{ $('数据处理').item.json.symbol }} {{ $('数据处理').item.json.interval }} 技术分析图表",
      "attachments": [
        {
          "id": "0",
          "filename": "{{ $('数据处理').item.json.symbol }}_{{ $('数据处理').item.json.interval }}.png",
          "description": "{{ $('数据处理').item.json.symbol }} 技术分析图表",
          "url": "{{ $('图表生成').item.json.imageUrl }}"
        }
      ]
    },
    "authorId": {{ $('数据处理').item.json.userId }},
    "symbol": "{{ $('数据处理').item.json.symbol }}",
    "timeframe": "{{ $('数据处理').item.json.interval }}",
    "currentCount": 1,
    "channelId": "",
    "messageId": "",
    "guildId": ""
  }
]
```

**5. 错误处理节点**
- 处理API调用失败情况
- 记录日志或发送通知

### 5. 测试步骤

1. **健康检查**
   ```
   GET https://your-replit-app.replit.app/api/health
   ```
   应返回: `{"status": "healthy", "bot_status": "online"}`

2. **测试发送**
   使用Postman或curl测试：
   ```bash
   curl -X POST https://your-replit-app.replit.app/api/send-chart \
     -H "Content-Type: application/json" \
     -d '[{"authorId": YOUR_DISCORD_USER_ID, "symbol": "AAPL", "timeframe": "1h", "discordPayload": {"content": "测试消息"}}]'
   ```

### 6. 常见问题排除

**问题1: API调用失败**
- 检查Replit应用是否运行
- 验证URL是否正确
- 检查请求格式是否正确

**问题2: Discord消息未发送**
- 确认authorId是有效的Discord用户ID
- 检查机器人权限
- 查看API响应错误信息

**问题3: 图片未显示**
- 确认图片URL可访问
- 检查base64格式是否正确
- 验证图片大小限制

### 7. 高级配置

**条件发送:**
可以添加IF节点来根据条件决定是否发送：
```
IF (价格变化 > 5%) → 发送Discord消息
```

**批量处理:**
使用Loop节点处理多个股票符号：
```
Loop (股票列表) → 生成图表 → 发送Discord消息
```

**定时任务:**
使用Cron Trigger定期检查和发送：
```
Cron (每小时) → 检查股票 → 生成图表 → 发送消息
```

### 8. 快速开始模板

复制以下JSON到您的n8n工作流编辑器：

```json
{
  "name": "Discord Stock Chart Bot",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "webhook",
        "options": {}
      },
      "id": "webhook",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://your-replit-app.replit.app/api/send-chart",
        "sendHeaders": true,
        "specifyHeaders": "json",
        "jsonHeaders": "{\n  \"Content-Type\": \"application/json\"\n}",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonBody": "[\n  {\n    \"chartImgRequest\": {\n      \"symbol\": \"{{ $json.symbol }}\",\n      \"interval\": \"{{ $json.interval }}\",\n      \"width\": 1920,\n      \"height\": 1080,\n      \"format\": \"png\"\n    },\n    \"discordPayload\": {\n      \"content\": \"📊 {{ $json.symbol }} {{ $json.interval }} 图表分析\",\n      \"attachments\": [\n        {\n          \"id\": \"0\",\n          \"filename\": \"{{ $json.symbol }}_{{ $json.interval }}.png\",\n          \"description\": \"{{ $json.symbol }} 技术分析图表\",\n          \"url\": \"{{ $json.chartUrl || '' }}\"\n        }\n      ]\n    },\n    \"authorId\": {{ $json.userId }},\n    \"symbol\": \"{{ $json.symbol }}\",\n    \"timeframe\": \"{{ $json.interval }}\",\n    \"currentCount\": 1\n  }\n]"
      },
      "id": "discord-api",
      "name": "Send to Discord",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Send to Discord",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### 9. 使用方法

1. **导入工作流:**
   - 复制上面的JSON
   - 在n8n中点击"导入工作流"
   - 粘贴JSON并保存

2. **修改配置:**
   - 将 `your-replit-app` 替换为您的实际Replit应用URL
   - 激活工作流

3. **测试调用:**
   ```bash
   curl -X POST https://your-n8n-webhook-url \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "interval": "1h",
       "userId": 1145170623354638418,
       "chartUrl": "https://example.com/chart.png"
     }'
   ```