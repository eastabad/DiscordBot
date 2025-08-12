#!/bin/bash

# 快速更新脚本 - 简化版本，适合频繁更新使用
# 直接在VPS上运行，无需密码输入

echo "⚡ 快速更新启动"
echo "==============="

# 基本检查
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在Discord机器人项目目录运行"
    exit 1
fi

echo "📍 目录: $(pwd)"

# 快速更新流程
echo "⏹️ 停止服务..."
docker-compose down

echo "🔄 拉取代码..."
git pull origin main || git pull origin master

echo "🚀 启动服务..."
docker-compose up -d

echo "⏳ 等待启动..."
sleep 15

echo "🔍 检查状态..."
docker-compose ps

echo "✅ 快速更新完成!"
echo "💡 详细检查: ./check-status.sh"