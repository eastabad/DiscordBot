# Discord机器人VPS部署 - 完整解决方案 ✅

## 🎯 部署已准备完成

我已经为您创建了完整的VPS Docker部署解决方案！您现在有两种方式部署到自己的VPS：

### 方案一：一键部署包 (推荐) 🚀

我已经创建了完整的部署包：`discord-bot-deploy.tar.gz`

**部署步骤**：
```bash
# 1. 上传部署包到您的VPS
scp discord-bot-deploy.tar.gz user@your-vps-ip:~/

# 2. 登录VPS并解压
ssh user@your-vps-ip
tar -xzf discord-bot-deploy.tar.gz
cd discord-bot-deploy

# 3. 运行一键部署脚本
./vps-deploy.sh

# 4. 配置环境变量
nano .env
# 设置 DISCORD_TOKEN 和其他配置

# 5. 启动机器人
docker-compose up -d
```

### 方案二：手动部署 🔧

按照 `VPS_DEPLOYMENT_GUIDE.md` 中的详细步骤操作。

## 📦 部署包内容

```
discord-bot-deploy/
├── main.py                    # 主程序(含健康检查)
├── bot.py                     # Discord机器人核心
├── config.py                  # 配置管理
├── Dockerfile                 # Docker镜像定义
├── docker-compose.yml         # 服务编排
├── docker-requirements.txt    # Python依赖
├── .env.example              # 环境变量模板
├── vps-deploy.sh             # 一键部署脚本
├── quick-start.sh            # 快速启动脚本
├── VPS_DEPLOYMENT_GUIDE.md   # 详细部署指南
└── README.md                 # 快速开始指南
```

## 🔧 VPS要求

### 最低配置
- **CPU**: 1核心
- **内存**: 1GB RAM
- **存储**: 10GB SSD
- **系统**: Ubuntu 20.04+, Debian 11+, CentOS 8+

### 推荐VPS服务商 💰
1. **DigitalOcean** - $5/月，简单易用
2. **Vultr** - $3.5/月，全球节点
3. **Linode** - $5/月，性能稳定
4. **Hetzner** - €3/月，欧洲服务器

## ⚙️ 自动化功能

### 一键部署脚本功能
- ✅ 自动检测操作系统(Ubuntu/Debian/CentOS)
- ✅ 安装Docker和Docker Compose
- ✅ 配置防火墙规则
- ✅ 创建项目目录和配置文件
- ✅ 生成管理脚本(启动/停止/重启/备份)

### 管理脚本
```bash
./start.sh      # 启动机器人
./stop.sh       # 停止机器人
./restart.sh    # 重启机器人
./logs.sh       # 查看日志
./backup.sh     # 备份数据
```

## 🏥 健康检查

部署成功后，机器人会在端口5000提供健康检查：
```bash
curl http://your-vps-ip:5000/health
```

返回示例：
```json
{
  "status": "healthy",
  "bot_running": true,
  "timestamp": "2025-08-12T13:20:00"
}
```

## 🔐 环境变量配置

在`.env`文件中配置：
```env
# 必需配置
DISCORD_TOKEN=your_discord_bot_token

# 可选配置 (推荐)
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
```

## 📊 服务组件

Docker Compose包含以下服务：
- **discord-bot**: 主要机器人服务(端口5000)
- **db**: PostgreSQL数据库(端口5432)

## 🔄 自动重启

配置了`restart: unless-stopped`，确保：
- VPS重启后自动恢复
- 容器异常退出后自动重启
- 24/7稳定运行

## 💾 数据持久化

配置了数据卷：
- `daily_logs/`: 日志文件
- `attached_assets/`: 附件资源
- `postgres_data`: 数据库数据

## 🛠️ 故障排除

### 常见问题和解决方案

1. **容器启动失败**
```bash
docker-compose logs discord-bot
```

2. **端口被占用**
```bash
sudo netstat -tulpn | grep 5000
```

3. **内存不足**
```bash
free -h
# 添加swap空间
sudo fallocate -l 1G /swapfile
```

4. **数据库连接问题**
```bash
docker-compose exec db pg_isready -U postgres
```

## 📈 性能监控

### 资源使用查看
```bash
docker stats                    # 容器资源使用
htop                           # 系统资源使用
df -h                          # 磁盘使用
```

### 日志管理
```bash
docker-compose logs -f         # 实时日志
docker-compose logs --tail=100 # 最近100行日志
```

## 🔒 安全配置

### 防火墙
- SSH端口(22)：允许
- 健康检查端口(5000)：允许
- 其他端口：拒绝

### Docker安全
- 使用非root用户运行
- 限制容器资源使用
- 定期更新基础镜像

## 💰 成本分析

### 月费用对比
| 方案 | 费用 | 优势 | 劣势 |
|------|------|------|------|
| VPS自建 | $3-5/月 | 完全控制、低成本 | 需要维护 |
| Railway | $5+/月 | 零配置 | 按使用量计费 |
| Render | $7+/月 | 托管服务 | 有休眠限制 |

## 🚀 立即开始部署

1. **选择VPS服务商**并创建服务器
2. **下载部署包**：`discord-bot-deploy.tar.gz`
3. **上传到VPS**：`scp discord-bot-deploy.tar.gz user@vps-ip:~/`
4. **执行部署**：解压后运行`./vps-deploy.sh`
5. **配置环境**：编辑`.env`文件
6. **启动服务**：`docker-compose up -d`

## ✅ 部署完成验证

部署成功后应该看到：
- ✅ 容器正常运行：`docker-compose ps`
- ✅ 健康检查通过：`curl localhost:5000/health`
- ✅ Discord机器人在线
- ✅ 日志无错误：`docker-compose logs`

## 📞 技术支持

如遇到问题：
1. 查看 `VPS_DEPLOYMENT_GUIDE.md` 详细指南
2. 检查容器日志：`docker-compose logs`
3. 验证环境变量配置
4. 确认防火墙设置

---

**总结**：您现在拥有完整的VPS Docker部署解决方案，可以在任何VPS上实现低成本、高可控的24/7 Discord机器人运行。