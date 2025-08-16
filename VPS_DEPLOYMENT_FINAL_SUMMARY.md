# VPS部署最终说明 - 今日更新版本 (2025-08-16)

## 🎯 今日重要更新

### 核心修复和优化
1. **AI报告生成系统完全修复**
   - ✅ 修复AI提示模板格式错误 (📊 → 📉 趋势分析)
   - ✅ 确保使用用户指定的准确模板格式
   - ✅ 完善3种数据类型的正确分离使用

2. **智能报告缓存系统**
   - ✅ 实现基于data_id和timeframe的智能缓存
   - ✅ 预计减少50-80%的Google API调用费用
   - ✅ 自动缓存失效和清理机制

3. **数据流程优化**
   - ✅ signal数据专门用于报告主体(5个章节)
   - ✅ trade/close数据仅用于TDindicator Bot交易解读
   - ✅ 消除重复数据库查询，提高性能

## 📦 部署包说明

### 可用的部署包
- `discord-bot-deploy.tar.gz` - 标准部署包
- `discord-bot-deploy-today.tar.gz` - 今日更新专用包 (推荐)

### 包含的重要文件
```
discord-bot-deploy/
├── gemini_report_generator.py     # 修复后的AI报告生成器
├── models.py                      # 包含ReportCache模型
├── bot.py                         # 主机器人逻辑
├── main_with_api.py              # 启动文件
├── VPS_DEPLOY_TODAY_UPDATE.md    # 今日更新部署指南
├── TODAY_UPDATE_CHECKLIST.md     # 部署检查清单
├── vps-update-today.sh           # 今日专用更新脚本
├── vps-deploy.sh                 # 标准部署脚本
└── docker-compose.yml            # Docker配置
```

## 🚀 VPS部署步骤

### 方法1: 全新部署 (推荐新VPS)

```bash
# 1. 上传部署包到VPS
scp discord-bot-deploy-today.tar.gz user@your-vps-ip:~/

# 2. 连接VPS并解压
ssh user@your-vps-ip
tar -xzf discord-bot-deploy-today.tar.gz
cd discord-bot-deploy

# 3. 运行一键部署脚本
chmod +x vps-deploy.sh
./vps-deploy.sh

# 4. 配置环境变量
cp .env.example .env
nano .env
# 填入必要的API密钥和配置

# 5. 启动服务
docker-compose up -d

# 6. 验证部署
curl http://localhost:5000/health
```

### 方法2: 现有VPS更新 (推荐现有部署)

```bash
# 1. 在现有VPS上备份并更新
cd ~/discord-bot-deploy  # 或你的项目目录

# 2. 下载今日更新脚本
wget https://your-domain.com/vps-update-today.sh
chmod +x vps-update-today.sh

# 3. 运行更新脚本
./vps-update-today.sh

# 脚本会自动:
# - 备份现有配置和数据库
# - 停止现有服务
# - 更新代码和镜像
# - 恢复配置
# - 启动新版本
# - 验证更新结果
```

## 🔧 必需的环境变量配置

创建或更新 `.env` 文件:

```env
# Discord配置 (必需)
DISCORD_TOKEN=your_discord_bot_token

# Google Gemini API (必需)
GEMINI_API_KEY=your_gemini_api_key

# 数据库配置 (Docker自动创建)
DATABASE_URL=postgresql://postgres:password@db:5432/discord_bot

# TradingView配置 (可选，用于图表功能)
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign

# Discord频道配置 (推荐)
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
REPORT_CHANNEL_ID=report_channel_id

# Webhook配置 (如使用TradingView集成)
WEBHOOK_URL=http://your-vps-ip:5000/webhook/tradingview
```

### 配置说明
- **DISCORD_TOKEN**: 必需，从Discord Developer Portal获取
- **GEMINI_API_KEY**: 必需，从Google AI Studio获取
- **MONITOR_CHANNEL_IDS**: 机器人监控的Discord频道ID (逗号分隔)
- **REPORT_CHANNEL_ID**: 专门用于AI报告的频道ID

## ✅ 部署验证

### 1. 健康检查
```bash
curl http://your-vps-ip:5000/health

# 期望响应:
{
  "status": "healthy",
  "bot_status": "connected", 
  "database_status": "connected",
  "gemini_status": "available"
}
```

### 2. Discord功能验证
在Discord中发送: `@机器人 !report AAPL 1h`

验证返回的报告包含:
- ✅ 正确的章节标题 (特别是 `📉 趋势分析`)
- ✅ bullishrating和bearishrating格式
- ✅ TDindicator Bot交易解读部分 (如有交易数据)

### 3. 缓存系统验证
重复发送相同的报告请求，第二次应该:
- ✅ 响应更快 (使用缓存)
- ✅ 日志显示缓存命中信息

### 4. 系统状态检查
```bash
# 容器状态
docker-compose ps

# 资源使用
docker stats

# 服务日志
docker-compose logs -f discord-bot
```

## 🔍 故障排除

### 常见问题解决

1. **AI报告生成失败**
```bash
# 检查Gemini API密钥
docker-compose logs discord-bot | grep -i gemini

# 验证API密钥配置
docker-compose exec discord-bot env | grep GEMINI_API_KEY
```

2. **缓存系统问题**
```bash
# 检查缓存表
docker-compose exec db psql -U postgres -d discord_bot -c "SELECT COUNT(*) FROM report_cache;"

# 查看缓存相关日志
docker-compose logs discord-bot | grep -i cache
```

3. **内存使用过高**
```bash
# 查看资源使用
docker stats

# 重启服务释放内存
docker-compose restart
```

## 📊 性能监控

### 自动监控脚本
```bash
# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== $(date) ==="
curl -f http://localhost:5000/health || echo "健康检查失败"
docker-compose ps
docker stats --no-stream
EOF

chmod +x monitor.sh

# 添加到定时任务
crontab -e
# */5 * * * * /path/to/monitor.sh >> /var/log/bot-monitor.log
```

## 🚨 应急措施

如果更新后出现问题:

1. **快速回滚**
```bash
# 停止服务
docker-compose down

# 恢复配置备份
cp .env.backup.* .env

# 使用旧镜像启动
docker-compose up -d
```

2. **完全重置**
```bash
# 清理所有容器和数据
docker-compose down -v
docker system prune -af

# 重新部署
./vps-deploy.sh
```

## 📈 更新效果预期

部署今日更新后，你应该体验到:

1. **AI报告质量提升**
   - 报告格式完全符合要求
   - 章节标题使用正确的emoji
   - 数据来源分离清晰

2. **性能显著改善**
   - 报告生成速度提升50-80%
   - API调用费用大幅降低
   - 系统响应更加稳定

3. **运维体验优化**
   - 更详细的日志记录
   - 更好的错误处理
   - 更智能的缓存管理

## 📞 技术支持

如果部署过程中遇到问题:

1. 检查 `TODAY_UPDATE_CHECKLIST.md` 确保所有步骤完成
2. 查看系统日志: `docker-compose logs -f`
3. 验证环境变量配置: `docker-compose config`
4. 检查网络和防火墙设置

---

**恭喜! 你的Discord交易机器人现在运行着最新版本，包含所有今日的重要修复和优化!**