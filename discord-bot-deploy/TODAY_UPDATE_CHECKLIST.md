# VPS部署检查清单 - 今日更新 (2025-08-16)

## 🚀 部署前准备

### 1. 本地验证
- [ ] AI报告生成功能正常
- [ ] 缓存系统工作正常
- [ ] 数据库连接稳定
- [ ] 环境变量配置完整

### 2. 创建部署包
```bash
# 在项目根目录执行
./deploy-package.sh
```
- [ ] 部署包创建成功 (discord-bot-deploy.tar.gz)
- [ ] 包含所有必要文件

### 3. VPS准备
- [ ] VPS可访问 (SSH连接正常)
- [ ] 足够的磁盘空间 (至少2GB)
- [ ] 网络端口5000开放

## 📤 上传和部署

### 4. 上传部署包
```bash
# 上传到VPS
scp discord-bot-deploy.tar.gz user@your-vps-ip:~/
```
- [ ] 文件上传成功
- [ ] 文件大小正确

### 5. VPS部署
```bash
# 在VPS上执行
ssh user@your-vps-ip
tar -xzf discord-bot-deploy.tar.gz
cd discord-bot-deploy
./vps-deploy.sh
```
- [ ] 系统依赖安装完成
- [ ] Docker和Docker Compose安装成功
- [ ] 防火墙规则配置正确

### 6. 环境配置
```bash
cp .env.example .env
nano .env
```

必须配置的环境变量:
- [ ] DISCORD_TOKEN (Discord机器人令牌)
- [ ] GEMINI_API_KEY (Google Gemini API密钥)
- [ ] DATABASE_URL (数据库连接字符串)
- [ ] MONITOR_CHANNEL_IDS (监控频道ID)
- [ ] CHART_IMG_API_KEY (图表API密钥)
- [ ] LAYOUT_ID (TradingView布局ID)

可选配置:
- [ ] TRADINGVIEW_SESSION_ID
- [ ] TRADINGVIEW_SESSION_ID_SIGN
- [ ] REPORT_CHANNEL_ID
- [ ] WEBHOOK_URL

## 🔧 启动和验证

### 7. 启动服务
```bash
docker-compose up -d
```
- [ ] 所有容器启动成功
- [ ] 无错误日志输出

### 8. 健康检查
```bash
# 本地检查
curl http://localhost:5000/health

# 外部检查
curl http://your-vps-ip:5000/health
```
- [ ] 健康检查接口正常响应
- [ ] 返回状态为 "healthy"
- [ ] 机器人状态为 "connected"
- [ ] 数据库状态为 "connected"

### 9. 功能验证

#### Discord机器人连接
- [ ] 机器人在Discord服务器中显示在线
- [ ] 可以响应@机器人消息

#### AI报告生成
在Discord中测试: `@机器人 !report AAPL 1h`
- [ ] 报告生成成功
- [ ] 格式正确 (包含 📉 趋势分析)
- [ ] 包含所有必需章节
- [ ] TDindicator Bot部分正确显示

#### 缓存系统
重复执行相同的报告请求:
- [ ] 第二次请求使用缓存 (响应更快)
- [ ] 日志显示缓存命中信息

#### TradingView Webhook
```bash
# 测试webhook端点
curl -X POST http://your-vps-ip:5000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```
- [ ] Webhook接口可访问
- [ ] 返回正确响应

## 📊 监控和维护

### 10. 日志检查
```bash
# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs discord-bot
docker-compose logs db
```
- [ ] 无严重错误日志
- [ ] 机器人连接日志正常
- [ ] 数据库连接日志正常

### 11. 性能监控
```bash
# 查看容器资源使用
docker stats

# 查看系统资源
htop
free -h
df -h
```
- [ ] CPU使用率合理 (<50%)
- [ ] 内存使用率正常 (<80%)
- [ ] 磁盘空间充足 (>1GB可用)

### 12. 自动化设置
```bash
# 创建监控脚本
./monitor-bot.sh

# 设置定时任务
crontab -e
# */5 * * * * /path/to/monitor-bot.sh
```
- [ ] 监控脚本工作正常
- [ ] 定时任务设置完成

## 🔒 安全检查

### 13. 安全配置
- [ ] 修改默认SSH端口 (可选)
- [ ] 配置fail2ban (可选)
- [ ] 禁用root登录 (推荐)
- [ ] 更新系统包

### 14. 备份配置
```bash
# 数据库备份
docker-compose exec db pg_dump -U postgres discord_bot > backup.sql

# 配置文件备份
cp .env .env.backup
```
- [ ] 数据库备份成功
- [ ] 配置文件已备份

## ✅ 部署完成确认

### 15. 最终检查
- [ ] 所有服务正常运行
- [ ] 机器人功能完全可用
- [ ] 报告生成使用新的正确格式
- [ ] 缓存系统减少API调用
- [ ] 监控和日志系统正常

### 16. 文档记录
- [ ] VPS IP地址: ________________
- [ ] 部署时间: ________________
- [ ] 版本标识: 2025-08-16-ai-fix
- [ ] 特殊配置: ________________

## 🚨 应急联系

如果部署过程中遇到问题:

1. **检查日志**: `docker-compose logs -f`
2. **重启服务**: `docker-compose restart`
3. **完全重置**: `docker-compose down -v && docker-compose up -d`
4. **恢复备份**: 使用之前的备份文件

## 🎯 部署成功标志

当以下所有项目都完成时，部署即为成功:
- ✅ Discord机器人在线且响应正常
- ✅ AI报告生成使用正确格式 (📉 趋势分析)
- ✅ 缓存系统正常工作
- ✅ 健康检查接口返回正常状态
- ✅ 系统资源使用合理
- ✅ 监控和日志系统就位

**恭喜! 您的Discord机器人已成功部署到VPS并包含所有今日更新!**