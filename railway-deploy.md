# Railway部署指南 (推荐)

## 为什么选择Railway
- ✅ 最简单的部署方式，从GitHub一键部署
- ✅ 自动检测Python项目和依赖
- ✅ 内置PostgreSQL数据库
- ✅ 24/7运行，无休眠问题
- ✅ 自动HTTPS和域名

## 部署步骤

### 1. 准备GitHub仓库
```bash
# 将代码推送到GitHub
git init
git add .
git commit -m "Discord bot ready for deployment"
git remote add origin https://github.com/yourusername/discord-bot.git
git push -u origin main
```

### 2. 登录Railway
- 访问 [railway.app](https://railway.app)
- 使用GitHub账号登录
- 点击 "Deploy from GitHub"

### 3. 选择仓库和配置
- 选择您的Discord机器人仓库
- Railway会自动检测到Python项目
- 确认使用 `main.py` 作为启动文件

### 4. 添加数据库 (如果需要)
```bash
# Railway控制台中
1. 点击 "Add Service"
2. 选择 "PostgreSQL"
3. 等待数据库创建完成
```

### 5. 设置环境变量
在Railway控制台的Variables面板中添加：
```
DISCORD_TOKEN=your_discord_bot_token
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
WEBHOOK_URL=your_webhook_url (可选)
```

### 6. 数据库连接 (自动配置)
Railway会自动设置：
```
DATABASE_URL=postgresql://username:password@host:port/database
```

### 7. 部署确认
- Railway会自动构建并部署
- 查看Logs确认机器人正常启动
- 健康检查端点：`https://your-app.railway.app/health`

## 常见问题

### Q: 如何查看日志？
A: 在Railway控制台点击Logs标签页

### Q: 如何重新部署？
A: 推送新代码到GitHub会自动触发重新部署

### Q: 费用如何计算？
A: 按使用时间计费，$5积分通常可运行1-2个月

### Q: 如何绑定自定义域名？
A: 在Railway控制台的Settings > Domains中添加

## 优化建议

### 1. 启动命令优化
Railway会自动使用：
```bash
python main.py
```

### 2. 资源监控
- CPU使用率保持在合理范围
- 内存使用通常在256MB以下
- 监控数据库连接数

### 3. 日志管理
```python
# 在main.py中已配置适当的日志级别
logging.basicConfig(level=logging.INFO)
```

## 备份和恢复

### 数据库备份
```bash
# Railway CLI命令
railway db:dump > backup.sql
```

### 环境变量备份
建议将环境变量保存在安全的密码管理器中

## 监控和告警

### 健康检查
Railway会自动监控：
- HTTP健康检查端点 `/health`
- 应用响应时间
- 资源使用情况

### 自定义监控
可以集成外部监控服务：
- UptimeRobot (免费)
- Pingdom
- New Relic

## 迁移注意事项

从Replit迁移到Railway：
1. ✅ 代码无需修改 (main.py已经兼容)
2. ✅ 环境变量直接复制
3. ✅ 数据库需要重新创建
4. ✅ 域名会改变，更新webhook URL

总结：Railway是目前最适合您Discord机器人的部署平台，部署简单、维护方便、成本合理。