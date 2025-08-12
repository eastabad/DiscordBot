# Discord机器人VPS部署完整指南

## 概述

本指南将帮您在自己的VPS上使用Docker部署Discord机器人，实现完全自主控制和低成本运行。

## VPS要求

### 最低配置
- **CPU**: 1核心
- **内存**: 1GB RAM
- **存储**: 10GB SSD
- **系统**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **网络**: 有公网IP，支持Docker

### 推荐配置
- **CPU**: 2核心
- **内存**: 2GB RAM
- **存储**: 20GB SSD
- **带宽**: 100Mbps+

### 推荐VPS提供商
1. **DigitalOcean** - $5/月起，简单易用
2. **Vultr** - $3.5/月起，全球节点
3. **Linode** - $5/月起，性能稳定
4. **Hetzner** - €3/月起，欧洲服务器
5. **腾讯云/阿里云** - 适合中国用户

## 一键部署方案

### 方法一: 自动部署脚本 (推荐)

```bash
# 下载并运行一键部署脚本
curl -fsSL https://your-domain.com/vps-deploy.sh | bash

# 或者手动下载
wget https://your-domain.com/vps-deploy.sh
chmod +x vps-deploy.sh
./vps-deploy.sh
```

**脚本会自动完成以下操作:**
- ✅ 检测操作系统类型
- ✅ 更新系统包
- ✅ 安装Docker和Docker Compose
- ✅ 配置防火墙规则
- ✅ 创建项目目录和配置文件
- ✅ 生成管理脚本

### 方法二: 手动部署 (详细控制)

#### 1. 连接VPS
```bash
ssh root@your-vps-ip
# 或
ssh your-user@your-vps-ip
```

#### 2. 更新系统
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo dnf update -y
```

#### 3. 安装Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

#### 4. 安装Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 5. 创建项目目录
```bash
mkdir -p ~/discord-bot
cd ~/discord-bot
```

#### 6. 上传项目文件
```bash
# 方法A: 使用scp上传
scp -r ./project-files/* user@your-vps:/home/user/discord-bot/

# 方法B: 使用Git
git clone https://github.com/yourusername/discord-bot.git
cd discord-bot
```

#### 7. 配置环境变量
```bash
cp .env.example .env
nano .env
```

填入以下配置:
```env
DISCORD_TOKEN=your_discord_bot_token
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
```

#### 8. 配置防火墙
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow ssh
sudo ufw allow 5000/tcp
sudo ufw --force enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

#### 9. 构建和启动
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 项目文件结构

部署后的目录结构:
```
~/discord-bot/
├── Dockerfile                 # Docker镜像定义
├── docker-compose.yml         # 服务编排配置
├── docker-requirements.txt    # Python依赖
├── .env                       # 环境变量配置
├── .dockerignore              # Docker忽略文件
├── main.py                    # 主程序入口
├── bot.py                     # Discord机器人核心
├── config.py                  # 配置管理
├── daily_logs/                # 日志目录
├── attached_assets/           # 资源文件
├── start.sh                   # 启动脚本
├── stop.sh                    # 停止脚本
├── restart.sh                 # 重启脚本
├── logs.sh                    # 日志查看脚本
└── backup.sh                  # 备份脚本
```

## 管理和维护

### 日常管理命令

```bash
# 进入项目目录
cd ~/discord-bot

# 启动机器人
./start.sh

# 停止机器人
./stop.sh

# 重启机器人
./restart.sh

# 查看实时日志
./logs.sh

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats
```

### 健康检查

```bash
# 本地检查
curl http://localhost:5000/health

# 外部检查
curl http://your-vps-ip:5000/health
```

健康响应示例:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-12T13:20:00",
  "bot_running": true,
  "started_at": "2025-08-12T13:15:30"
}
```

### 日志管理

```bash
# 查看Discord机器人日志
docker-compose logs discord-bot

# 查看数据库日志
docker-compose logs db

# 实时跟踪日志
docker-compose logs -f discord-bot

# 查看最近100行日志
docker-compose logs --tail=100 discord-bot
```

### 更新部署

```bash
# 自动更新脚本
./update.sh

# 手动更新
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据备份

```bash
# 自动备份脚本
./backup.sh

# 手动备份数据库
docker-compose exec db pg_dump -U postgres discord_bot > backup.sql

# 备份配置和日志
tar -czf backup-$(date +%Y%m%d).tar.gz daily_logs attached_assets .env
```

### 数据恢复

```bash
# 恢复数据库
docker-compose exec db psql -U postgres discord_bot < backup.sql

# 恢复文件
tar -xzf backup-20250812.tar.gz
```

## 性能优化

### 系统优化

```bash
# 增加swap空间 (如果内存不足)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 优化Docker日志
sudo nano /etc/docker/daemon.json
```

Docker配置:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 资源监控

```bash
# 安装监控工具
sudo apt install htop iotop

# 查看系统资源
htop

# 查看Docker资源使用
docker stats

# 查看磁盘使用
df -h
```

### 自动化监控

创建监控脚本 `monitor.sh`:
```bash
#!/bin/bash
# 检查Discord机器人健康状态
if ! curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "$(date): Discord机器人健康检查失败，重启中..." >> monitor.log
    cd ~/discord-bot && ./restart.sh
fi
```

添加到crontab:
```bash
crontab -e
# 每5分钟检查一次
*/5 * * * * /home/user/discord-bot/monitor.sh
```

## 安全配置

### 基础安全

```bash
# 更改SSH端口
sudo nano /etc/ssh/sshd_config
# Port 2222

# 禁用root登录
# PermitRootLogin no

# 重启SSH服务
sudo systemctl restart sshd

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### Docker安全

```bash
# 限制容器资源
docker-compose.yml中添加:
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
```

### 定期更新

```bash
# 创建自动更新脚本
cat > ~/update-system.sh << 'EOF'
#!/bin/bash
sudo apt update && sudo apt upgrade -y
docker system prune -f
EOF

# 每周执行
crontab -e
0 2 * * 0 /home/user/update-system.sh
```

## 故障排除

### 常见问题

1. **容器启动失败**
```bash
# 查看详细日志
docker-compose logs discord-bot

# 检查配置文件
docker-compose config
```

2. **端口被占用**
```bash
# 查看端口使用
sudo netstat -tulpn | grep 5000

# 杀死占用进程
sudo kill -9 PID
```

3. **内存不足**
```bash
# 查看内存使用
free -h

# 添加swap空间
sudo fallocate -l 1G /swapfile
```

4. **数据库连接问题**
```bash
# 检查数据库状态
docker-compose exec db pg_isready -U postgres

# 重启数据库
docker-compose restart db
```

### 应急恢复

```bash
# 完全重置
docker-compose down -v
docker system prune -af
./start.sh
```

## 成本分析

### 月费用估算 (USD)
- **DigitalOcean Basic**: $5/月
- **Vultr Regular**: $3.5/月
- **Linode Nanode**: $5/月
- **Hetzner CX11**: €3/月 (~$3.3)

### 与其他平台对比
| 平台 | 月费用 | 优势 | 劣势 |
|------|--------|------|------|
| VPS (自建) | $3-5 | 完全控制、低成本 | 需要维护 |
| Railway | $5+ | 零配置 | 按使用量计费 |
| Render | $7+ | 托管服务 | 休眠限制 |
| Heroku | $5+ | 易用 | 价格较高 |

## 总结

VPS部署的优势:
- ✅ 完全控制权
- ✅ 低成本运行
- ✅ 无供应商锁定
- ✅ 高度可定制

适合场景:
- 长期运行的生产环境
- 需要完全控制的企业项目
- 成本敏感的个人项目
- 学习DevOps技能

通过本指南，您可以在任何VPS上成功部署Discord机器人，实现稳定、经济的24/7运行。