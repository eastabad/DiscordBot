# Render部署指南 (免费选择)

## 为什么选择Render
- ✅ 有真正的免费层 (虽然有休眠限制)
- ✅ 免费PostgreSQL数据库 (90天)
- ✅ 自动SSL证书
- ✅ GitHub集成
- ✅ 99.9%正常运行时间保证

## 免费层限制
⚠️ **重要**: 免费层有以下限制
- 15分钟无活动后休眠
- 每月750小时 (够用但需要管理)
- 512MB内存
- 0.1 CPU

## 部署步骤

### 1. 准备GitHub仓库
```bash
git init
git add .
git commit -m "Discord bot for Render deployment"
git remote add origin https://github.com/yourusername/discord-bot.git
git push -u origin main
```

### 2. 注册Render账号
- 访问 [render.com](https://render.com)
- 使用GitHub账号注册
- 连接GitHub仓库

### 3. 创建Web Service
1. 点击 "New +" → "Web Service"
2. 选择您的GitHub仓库
3. 配置如下：
   - **Name**: discord-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### 4. 创建数据库 (免费90天)
1. 点击 "New +" → "PostgreSQL"
2. 选择免费层
3. 记录数据库连接信息

### 5. 环境变量配置
在Service设置的Environment面板中添加：
```
DISCORD_TOKEN=your_discord_bot_token
DATABASE_URL=postgresql://user:pass@host:port/db (从数据库页面复制)
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
WEBHOOK_URL=your_webhook_url
```

### 6. 创建requirements.txt
```txt
discord.py>=2.5.2
aiohttp>=3.12.15
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.43
anthropic>=0.62.0
psutil>=7.0.0
flask>=3.1.1
```

### 7. 解决休眠问题 (可选)
创建简单的ping脚本：
```bash
# ping.sh
#!/bin/bash
while true; do
    curl -f https://your-app.onrender.com/health || exit 1
    sleep 840  # 14分钟ping一次
done
```

## 高级配置

### 1. 使用Render.yaml
创建 `render.yaml`:
```yaml
services:
  - type: web
    name: discord-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    plan: free
    envVars:
      - key: DISCORD_TOKEN
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: discord-bot-db
          property: connectionString

databases:
  - name: discord-bot-db
    plan: free
    databaseName: discord_bot
```

### 2. 健康检查优化
确保您的main.py包含：
```python
# 已经在main.py中实现
async def health_check(request):
    return web.json_response({"status": "healthy"})
```

### 3. 日志配置
```python
import logging
import sys

# 适合Render的日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
```

## 成本优化

### 免费层最大化
1. **监控使用时间**: 每月750小时限制
2. **合理安排休眠**: 利用低活跃时段
3. **数据库管理**: 90天后需要升级或迁移

### 升级时机
考虑升级到付费层 ($7/月) 当：
- 需要24/7运行
- 用户活跃度高
- 需要更多内存/CPU

## 监控和维护

### 查看日志
```bash
# Render CLI
render logs -s your-service-name --tail
```

### 健康监控
免费工具：
- UptimeRobot: 每5分钟ping一次
- StatusCake: 基本监控
- 自建脚本: 定期ping

### 性能监控
监控指标：
- 响应时间
- 内存使用率
- 数据库连接数
- 错误率

## 故障排除

### 常见问题

1. **部署失败**
   - 检查requirements.txt
   - 确认Python版本兼容
   - 查看构建日志

2. **机器人无响应**
   - 检查Discord token
   - 确认环境变量正确
   - 查看应用日志

3. **数据库连接问题**
   - 验证DATABASE_URL格式
   - 检查数据库状态
   - 确认防火墙设置

### 迁移准备
从免费层迁移到付费层：
1. 备份数据库
2. 记录所有环境变量  
3. 测试新配置
4. 更新监控设置

## 总结

Render适合：
- 预算有限的开发者
- 测试和开发环境
- 中等活跃度的机器人

限制：
- 免费层会休眠
- 数据库90天限制
- 性能相对有限

升级建议：当机器人用户增长或需要24/7运行时，考虑升级到付费层或迁移到Railway。