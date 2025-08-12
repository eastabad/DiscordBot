#!/bin/bash
# Discord机器人VPS一键部署命令生成器
# GitHub仓库: https://github.com/eastabad/DiscordBot

echo "🚀 Discord机器人VPS部署命令"
echo "GitHub仓库: https://github.com/eastabad/DiscordBot"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 方案一：完全自动化部署 (推荐)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "复制以下命令到您的VPS终端中执行："
echo ""
cat << 'EOF'
# 1. 安装Docker (如果未安装)
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER

# 2. 安装Docker Compose (如果未安装)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose

# 3. 克隆项目
git clone https://github.com/eastabad/DiscordBot.git && cd DiscordBot

# 4. 配置环境变量
cp .env.example .env && echo "请编辑 .env 文件设置 DISCORD_TOKEN: nano .env"

# 5. 配置防火墙
sudo ufw allow ssh && sudo ufw allow 5000/tcp && sudo ufw --force enable

# 6. 启动服务
docker-compose up -d

# 7. 查看状态
docker-compose ps && docker-compose logs -f discord-bot
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 方案二：如果已安装Docker"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << 'EOF'
# 快速部署命令
git clone https://github.com/eastabad/DiscordBot.git && cd DiscordBot && cp .env.example .env && echo "请设置 .env 文件后运行: docker-compose up -d"
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 环境变量配置示例"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "在 .env 文件中设置："
cat << 'EOF'
DISCORD_TOKEN=your_discord_bot_token_here
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
WEBHOOK_URL=your_webhook_url
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 部署验证命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << 'EOF'
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs discord-bot

# 健康检查
curl http://localhost:5000/health

# 外部访问测试 (用您的VPS IP替换 YOUR_VPS_IP)
curl http://YOUR_VPS_IP:5000/health
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠️ 管理命令"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << 'EOF'
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新代码
git pull origin main && docker-compose down && docker-compose build --no-cache && docker-compose up -d

# 查看实时日志
docker-compose logs -f discord-bot

# 备份数据
docker-compose exec db pg_dump -U postgres discord_bot > backup.sql
EOF

echo ""
echo "✅ 命令已生成！复制上述命令到您的VPS执行即可完成部署。"
echo "📞 如有问题，请检查 DEPLOYMENT_SIMPLE.md 获取详细说明。"