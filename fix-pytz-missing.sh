#!/bin/bash

# 快速修复pytz模块缺失问题
# 用于VPS上立即解决依赖问题

echo "🔧 修复pytz模块缺失问题..."

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在Discord机器人项目目录运行此脚本"
    exit 1
fi

echo "📍 当前目录: $(pwd)"

# 停止服务
echo "⏹️ 停止服务..."
docker-compose down

# 更新docker-requirements.txt
echo "📝 更新依赖文件..."
cat > docker-requirements.txt << 'EOF'
discord.py>=2.5.2
aiohttp>=3.12.15
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.43
anthropic>=0.62.0
psutil>=7.0.0
flask>=3.1.1
pytz>=2025.2
google-genai>=1.30.0
requests>=2.32.4
EOF

echo "✅ docker-requirements.txt已更新"

# 清理旧镜像并重建
echo "🔧 重建Docker镜像..."
docker system prune -f
docker-compose build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待启动
echo "⏳ 等待服务启动..."
sleep 20

# 检查状态
echo "🔍 检查服务状态..."
docker-compose ps
echo ""
echo "📋 检查机器人日志..."
docker-compose logs discord-bot --tail=10

echo ""
echo "✅ pytz模块修复完成!"
echo "💡 如果还有问题，检查日志: docker-compose logs discord-bot"