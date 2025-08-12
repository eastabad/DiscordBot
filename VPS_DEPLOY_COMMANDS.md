# VPS部署无限制版本 - 快速命令

## 🚀 一键自动部署 (推荐)

```bash
# 下载并运行自动部署脚本
curl -fsSL https://raw.githubusercontent.com/eastabad/DiscordBot/main/vps-unlimited-deploy.sh -o deploy.sh && chmod +x deploy.sh && ./deploy.sh
```

## 🔧 手动部署步骤

### 1. 环境准备
```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆项目
```bash
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot
```

### 3. 配置环境变量
```bash
# 复制环境配置
cp .env.example .env

# 编辑配置文件
nano .env
```

在`.env`文件中设置：
```env
# 必需配置
DISCORD_TOKEN=your_discord_bot_token_here
VPS_DEPLOYMENT=true

# 可选配置
CHART_IMG_API_KEY=your_chart_api_key
MONITOR_CHANNEL_IDS=1234567890,0987654321
```

### 4. 启动服务
```bash
# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps
```

### 5. 验证部署
```bash
# 检查健康状态
curl http://localhost:5000/health

# 查看机器人日志
docker-compose logs discord-bot

# 查看实时日志
docker-compose logs -f discord-bot
```

## 🔍 管理命令

### 服务管理
```bash
docker-compose ps              # 查看容器状态
docker-compose up -d          # 启动服务
docker-compose down           # 停止服务
docker-compose restart        # 重启服务
docker-compose logs discord-bot # 查看日志
```

### 更新代码
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 备份数据
```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres discord_bot > backup.sql

# 备份日志文件
tar -czf logs_backup.tar.gz daily_logs/
```

## 📊 Discord命令

### 用户命令
```
!quota         # 查看个人配额状态 (显示无限制)
!logs          # 查看今日使用统计
@机器人 AAPL,1h  # 股票图表查询 (无限制)
```

### 管理员命令
```
!vps_status    # 查看VPS部署状态
!exempt_list   # 查看豁免用户列表
!logs          # 查看详细统计
```

## 🌐 Web界面访问

- 健康检查: `http://your-vps-ip:5000/health`
- 日志查看器: `http://your-vps-ip:5001/`

## ✅ 部署验证清单

- [ ] Docker容器正常运行
- [ ] 健康检查返回 `"status": "healthy"`
- [ ] Discord机器人显示在线状态
- [ ] 日志显示 "VPS部署模式" 或 "机器人已登录"
- [ ] 用户可以无限次使用股票查询功能
- [ ] `!vps_status` 命令显示无限制模式

## 🔧 故障排除

### 常见问题
```bash
# 检查Docker状态
sudo systemctl status docker

# 检查端口占用
sudo netstat -tulpn | grep 5000

# 重置Docker环境
docker-compose down -v
docker system prune -a
```

### 防火墙配置
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp

# CentOS/RHEL (Firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

## 📞 获取帮助

如果遇到问题：
1. 查看日志: `docker-compose logs discord-bot`
2. 检查配置: `cat .env`
3. 验证网络: `curl http://localhost:5000/health`
4. 重启服务: `docker-compose restart`

---

**部署完成后，所有用户都可以无限制使用Discord机器人的所有功能！**