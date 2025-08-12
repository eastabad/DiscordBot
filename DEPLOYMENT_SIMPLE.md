# Discord机器人VPS一键部署指南

## 🚀 从GitHub直接部署到VPS

既然您的项目已经在GitHub上，我们可以直接从仓库部署，这是最简单的方式！

### GitHub仓库地址
```
https://github.com/eastabad/DiscordBot
```

## 📋 VPS部署命令 (复制粘贴即可)

### 方案一：完全自动化部署 (推荐)

在您的VPS上运行以下命令：

```bash
# 1. 下载并运行自动部署脚本
curl -fsSL https://raw.githubusercontent.com/eastabad/DiscordBot/main/vps-deploy.sh | bash

# 2. 克隆项目
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot

# 3. 配置环境变量
cp .env.example .env
nano .env
# 设置您的 DISCORD_TOKEN 和其他配置

# 4. 启动服务
docker-compose up -d

# 5. 查看日志确认运行
docker-compose logs -f
```

### 方案二：手动安装Docker后部署

如果您的VPS已经安装了Docker：

```bash
# 1. 克隆项目
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot

# 2. 配置环境变量
cp .env.example .env
nano .env
# 添加您的配置信息

# 3. 构建并启动
docker-compose up -d

# 4. 验证部署
curl http://localhost:5000/health
docker-compose ps
```

### 方案三：分步详细部署

```bash
# 步骤1: 连接到您的VPS
ssh user@your-vps-ip

# 步骤2: 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo dnf update -y  # CentOS/RHEL

# 步骤3: 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 步骤4: 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 步骤5: 克隆项目
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot

# 步骤6: 配置环境变量
cp .env.example .env
nano .env

# 步骤7: 配置防火墙
sudo ufw allow ssh
sudo ufw allow 5000/tcp
sudo ufw --force enable

# 步骤8: 启动服务
docker-compose up -d

# 步骤9: 验证部署
docker-compose logs -f discord-bot
curl http://localhost:5000/health
```

## 🔐 环境变量配置

在 `.env` 文件中设置以下变量：

```env
# 必需配置
DISCORD_TOKEN=your_discord_bot_token_here

# 可选配置 (推荐设置)
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
WEBHOOK_URL=your_webhook_url
```

## 🏥 部署验证

部署完成后，验证以下内容：

```bash
# 1. 检查容器状态
docker-compose ps

# 2. 查看日志
docker-compose logs discord-bot

# 3. 健康检查
curl http://localhost:5000/health
# 应该返回: {"status":"healthy","bot_running":true}

# 4. 检查Discord机器人是否在线
# 在Discord中查看机器人状态

# 5. 测试外部访问 (可选)
curl http://your-vps-ip:5000/health
```

## 🛠️ 管理命令

项目包含以下管理脚本：

```bash
# 如果不存在管理脚本，可以创建：
echo '#!/bin/bash
docker-compose up -d
echo "✅ 机器人已启动"' > start.sh

echo '#!/bin/bash
docker-compose down
echo "✅ 机器人已停止"' > stop.sh

echo '#!/bin/bash
docker-compose restart
echo "✅ 机器人已重启"' > restart.sh

echo '#!/bin/bash
docker-compose logs -f discord-bot' > logs.sh

chmod +x *.sh

# 使用管理脚本
./start.sh    # 启动
./stop.sh     # 停止
./restart.sh  # 重启
./logs.sh     # 查看日志
```

## 🔄 更新部署

当您更新GitHub代码后，在VPS上运行：

```bash
cd DiscordBot
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🚨 故障排除

### 常见问题解决

1. **Docker未安装**
```bash
# 重新安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

2. **端口被占用**
```bash
sudo netstat -tulpn | grep 5000
sudo kill -9 <PID>
```

3. **权限问题**
```bash
sudo chown -R $USER:$USER ~/DiscordBot
sudo chmod +x ~/DiscordBot/*.sh
```

4. **内存不足**
```bash
# 添加swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

5. **防火墙问题**
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 5000/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

## 💰 推荐VPS服务商

根据需求选择：

1. **DigitalOcean** - $5/月
   - 简单易用，文档完善
   - 一键安装Docker镜像

2. **Vultr** - $3.5/月
   - 价格便宜，性能不错
   - 全球多个数据中心

3. **Linode** - $5/月
   - 老牌服务商，稳定可靠
   - 优质技术支持

4. **Hetzner** - €3/月
   - 欧洲服务商，性价比极高
   - 适合欧洲用户

## 📞 获取支持

如果遇到问题：

1. 查看容器日志：`docker-compose logs discord-bot`
2. 检查环境变量配置
3. 确认Discord Token有效
4. 验证防火墙设置
5. 检查VPS资源使用情况

---

**总结**：通过GitHub仓库，您可以在任何VPS上快速部署Discord机器人，实现低成本、高可控的24/7运行。