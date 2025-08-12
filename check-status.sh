#!/bin/bash

# Docker部署状态检查脚本
# 检查所有服务状态和数据库连接

echo "🔍 Docker服务状态检查"
echo "======================"

# 检查Docker compose状态
echo "📦 检查Docker容器状态..."
docker-compose ps

echo ""
echo "💾 检查数据库连接..."
docker-compose exec db pg_isready -U postgres -d discord_bot

echo ""
echo "🔧 检查环境变量..."
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    if grep -q "DATABASE_URL" .env; then
        echo "✅ DATABASE_URL已在.env中配置"
    else
        echo "ℹ️  DATABASE_URL通过docker-compose.yml直接配置 (这是正常的)"
    fi
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "🌐 检查应用健康状态..."
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ 应用健康检查通过"
    curl -s http://localhost:5000/health | jq . 2>/dev/null || curl -s http://localhost:5000/health
else
    echo "❌ 应用健康检查失败"
fi

echo ""
echo "📊 检查数据库表..."
docker-compose exec -T db psql -U postgres -d discord_bot -c "\dt" 2>/dev/null || echo "❌ 无法连接数据库"

echo ""
echo "📝 显示最近日志..."
echo "Discord机器人日志:"
docker-compose logs discord-bot --tail=10

echo ""
echo "数据库日志:"
docker-compose logs db --tail=5