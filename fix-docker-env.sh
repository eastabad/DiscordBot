#!/bin/bash

# 修复Docker环境变量映射问题
# 专门解决GEMINI_API_KEY无法传递到容器的问题

echo "🔧 修复Docker环境变量映射..."

# 检查目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在Discord机器人项目目录运行"
    exit 1
fi

echo "📍 当前目录: $(pwd)"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env文件不存在"
    exit 1
fi

# 检查GEMINI_API_KEY是否在.env中
if ! grep -q "GEMINI_API_KEY=" .env; then
    echo "❌ .env文件中缺少GEMINI_API_KEY"
    exit 1
fi

echo "✅ .env文件检查通过"

# 停止服务
echo "⏹️ 停止服务..."
docker-compose down

# 备份原docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

# 更新docker-compose.yml
echo "📝 更新docker-compose.yml环境变量映射..."

# 检查是否已包含GEMINI_API_KEY
if grep -q "GEMINI_API_KEY" docker-compose.yml; then
    echo "✅ GEMINI_API_KEY映射已存在"
else
    echo "➕ 添加GEMINI_API_KEY映射..."
    # 在DISCORD_TOKEN后添加GEMINI_API_KEY
    sed -i '/- DISCORD_TOKEN=/a\      - GEMINI_API_KEY=${GEMINI_API_KEY}' docker-compose.yml
fi

# 检查是否已包含REPORT_CHANNEL_IDS
if grep -q "REPORT_CHANNEL_IDS" docker-compose.yml; then
    echo "✅ REPORT_CHANNEL_IDS映射已存在"
else
    echo "➕ 添加REPORT_CHANNEL_IDS映射..."
    # 在MONITOR_CHANNEL_IDS后添加REPORT_CHANNEL_IDS
    sed -i '/- MONITOR_CHANNEL_IDS=/a\      - REPORT_CHANNEL_IDS=${REPORT_CHANNEL_IDS}' docker-compose.yml
fi

# 显示更新后的环境变量部分
echo ""
echo "📋 当前环境变量映射:"
grep -A 15 "environment:" docker-compose.yml | head -20

# 重启服务
echo ""
echo "🚀 重新启动服务..."
docker-compose up -d

# 等待启动
echo "⏳ 等待服务启动..."
sleep 20

# 验证环境变量
echo ""
echo "🔍 验证容器内环境变量..."
echo "检查GEMINI_API_KEY:"
docker-compose exec discord-bot env | grep GEMINI_API_KEY || echo "❌ GEMINI_API_KEY未找到"

echo "检查DISCORD_TOKEN:"
docker-compose exec discord-bot env | grep DISCORD_TOKEN | cut -c1-30 || echo "❌ DISCORD_TOKEN未找到"

# 检查日志
echo ""
echo "📋 检查启动日志..."
docker-compose logs discord-bot --tail=10

echo ""
echo "✅ Docker环境变量修复完成!"
echo "如果仍有问题，请检查:"
echo "1. .env文件格式: cat .env"
echo "2. 容器环境变量: docker-compose exec discord-bot env | grep -E '(GEMINI|DISCORD)'"