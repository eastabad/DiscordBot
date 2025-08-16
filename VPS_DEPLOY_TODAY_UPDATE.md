# VPS部署指南 - 今日更新版本 (2025-08-16)

## 今日重要更新内容

### 🔧 主要功能更新
1. **AI报告生成系统完全修复**
   - 修复AI提示模板格式错误 (📊趋势分析 → 📉趋势分析)
   - 确保使用用户指定的准确模板格式
   - 完善3种数据类型的正确分离使用

2. **智能报告缓存系统**
   - 实现基于data_id和timeframe的智能缓存
   - 预计减少50-80%的Google API调用
   - 自动缓存失效机制

3. **数据流程优化**
   - signal数据用于报告主体(5个章节)
   - trade/close数据仅用于TDindicator Bot交易解读
   - 消除重复数据库查询

4. **时间格式统一**
   - 全系统使用美国东部时间格式
   - 格式: "2025-08-15 21:29 (美国东部时间)"

## 快速VPS部署步骤

### 1. 准备部署包
```bash
# 在本地创建部署包
./deploy-package.sh
```

### 2. 上传到VPS
```bash
# 上传压缩包到VPS
scp discord-bot-deploy.tar.gz user@your-vps-ip:~/

# 连接VPS
ssh user@your-vps-ip

# 解压部署包
tar -xzf discord-bot-deploy.tar.gz
cd discord-bot-deploy
```

### 3. 快速部署
```bash
# 运行一键部署脚本
chmod +x vps-deploy.sh
./vps-deploy.sh

# 配置环境变量
cp .env.example .env
nano .env
```

### 4. 必需的环境变量
```env
# Discord配置
DISCORD_TOKEN=your_discord_bot_token

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# 数据库 (Docker会自动创建)
DATABASE_URL=postgresql://postgres:password@db:5432/discord_bot

# TradingView配置
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign

# Discord频道配置
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
REPORT_CHANNEL_ID=report_channel_id

# Webhook URL (VPS公网IP)
WEBHOOK_URL=http://your-vps-ip:5000/webhook/tradingview
```

### 5. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f

# 健康检查
curl http://localhost:5000/health
```

## 更新现有VPS部署

如果你已经有VPS部署，可以使用以下步骤更新：

### 方法1: 完全重新部署
```bash
# 在VPS上
cd ~/discord-bot-deploy
docker-compose down

# 备份配置
cp .env .env.backup

# 下载新版本
wget https://your-domain.com/discord-bot-deploy.tar.gz
tar -xzf discord-bot-deploy.tar.gz --strip-components=1

# 恢复配置
cp .env.backup .env

# 重新启动
docker-compose build --no-cache
docker-compose up -d
```

### 方法2: Git更新 (如果使用Git)
```bash
cd ~/discord-bot
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 今日更新验证

部署完成后，验证新功能是否正常：

### 1. 验证AI报告生成
在Discord中发送: `@机器人 !report AAPL 1h`

检查返回的报告是否包含:
- ✅ ## 📉 趋势分析 (正确的emoji)
- ✅ bullishrating和bearishrating格式
- ✅ TDindicator Bot交易解读部分

### 2. 验证缓存系统
```bash
# 查看缓存日志
docker-compose logs discord-bot | grep "缓存"

# 应该看到类似输出:
# "✅ 缓存报告命中: AAPL-1h"
# "💾 保存报告到缓存: AAPL-1h"
```

### 3. 验证数据库连接
```bash
# 检查数据库状态
docker-compose exec db pg_isready -U postgres

# 查看数据表
docker-compose exec db psql -U postgres -d discord_bot -c "\dt"
```

### 4. 验证API健康状态
```bash
curl http://your-vps-ip:5000/health

# 应该返回:
{
  "status": "healthy",
  "bot_status": "connected",
  "database_status": "connected",
  "gemini_status": "available"
}
```

## 故障排除

### 常见问题和解决方案

1. **AI报告生成失败**
```bash
# 检查Gemini API密钥
docker-compose logs discord-bot | grep "Gemini"

# 验证API密钥配置
docker-compose exec discord-bot env | grep GEMINI_API_KEY
```

2. **缓存系统问题**
```bash
# 查看缓存相关日志
docker-compose logs discord-bot | grep -i cache

# 检查ReportCache表
docker-compose exec db psql -U postgres -d discord_bot -c "SELECT COUNT(*) FROM report_cache;"
```

3. **数据库连接问题**
```bash
# 重启数据库
docker-compose restart db

# 检查数据库日志
docker-compose logs db
```

4. **内存使用过高**
```bash
# 查看容器资源使用
docker stats

# 如果需要，重启服务
docker-compose restart
```

## 性能监控

### 监控脚本
```bash
# 创建监控脚本
cat > monitor-bot.sh << 'EOF'
#!/bin/bash
echo "=== Discord Bot 状态监控 ==="
echo "时间: $(date)"
echo ""

# 健康检查
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ 健康检查: 正常"
else
    echo "❌ 健康检查: 失败"
fi

# 容器状态
echo ""
echo "📊 容器状态:"
docker-compose ps

# 资源使用
echo ""
echo "💾 资源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 最近日志
echo ""
echo "📝 最近日志 (最后10行):"
docker-compose logs --tail=10 discord-bot
EOF

chmod +x monitor-bot.sh
```

### 自动化监控
```bash
# 添加到crontab
crontab -e

# 每5分钟检查一次健康状态
*/5 * * * * /home/user/discord-bot-deploy/monitor-bot.sh >> /var/log/bot-monitor.log

# 每天备份一次数据库
0 2 * * * cd /home/user/discord-bot-deploy && docker-compose exec db pg_dump -U postgres discord_bot > backup-$(date +\%Y\%m\%d).sql
```

## 总结

今日更新的主要改进:
- ✅ AI报告生成系统完全修复，使用正确格式
- ✅ 智能缓存减少API调用成本
- ✅ 数据流程优化，提高性能
- ✅ 时间格式统一为美国东部时间

更新后的系统更加稳定、高效，适合长期生产环境运行。