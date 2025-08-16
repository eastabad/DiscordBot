#!/bin/bash

# VPS完整修复脚本 - 解决API密钥和数据库迁移问题
# 2025-08-16 版本

echo "🔧 VPS完整修复工具"
echo "=================="

# 检查目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 请在Discord机器人项目目录运行"
    exit 1
fi

echo "📍 当前目录: $(pwd)"

# 1. 检查.env文件
echo ""
echo "🔍 检查环境变量配置..."
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    
    # 检查必要的环境变量
    if grep -q "GEMINI_API_KEY=" .env; then
        if grep -q "GEMINI_API_KEY=$" .env || grep -q "GEMINI_API_KEY=\"\"" .env; then
            echo "❌ GEMINI_API_KEY为空，需要配置"
            NEED_GEMINI_KEY=1
        else
            echo "✅ GEMINI_API_KEY已配置"
        fi
    else
        echo "❌ 缺少GEMINI_API_KEY"
        NEED_GEMINI_KEY=1
    fi
    
    if grep -q "DISCORD_TOKEN=" .env; then
        echo "✅ DISCORD_TOKEN已配置"
    else
        echo "❌ 缺少DISCORD_TOKEN"
        NEED_DISCORD_TOKEN=1
    fi
else
    echo "❌ .env文件不存在"
    NEED_ENV_FILE=1
fi

# 2. 创建或更新.env文件
if [ "$NEED_ENV_FILE" = "1" ] || [ "$NEED_GEMINI_KEY" = "1" ] || [ "$NEED_DISCORD_TOKEN" = "1" ]; then
    echo ""
    echo "📝 配置环境变量..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# Discord配置
DISCORD_TOKEN=your_discord_bot_token

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# 数据库配置
DATABASE_URL=postgresql://postgres:password@db:5432/discord_bot

# TradingView配置 (可选)
CHART_IMG_API_KEY=
LAYOUT_ID=
TRADINGVIEW_SESSION_ID=
TRADINGVIEW_SESSION_ID_SIGN=

# Discord频道配置
MONITOR_CHANNEL_IDS=
REPORT_CHANNEL_ID=

# Webhook配置
WEBHOOK_URL=http://localhost:5000/webhook/tradingview
EOF
    fi
    
    echo ""
    echo "⚠️  重要: 需要配置API密钥"
    echo "请编辑.env文件，填入以下必要信息:"
    echo ""
    echo "1. DISCORD_TOKEN - 从Discord Developer Portal获取"
    echo "2. GEMINI_API_KEY - 从Google AI Studio获取"
    echo ""
    echo "编辑命令: nano .env"
    echo ""
    read -p "是否现在编辑.env文件? (y/N): " edit_env
    
    if [[ $edit_env == [Yy] ]]; then
        nano .env
    else
        echo "请手动编辑.env文件后重新运行此脚本"
        exit 1
    fi
fi

# 3. 停止现有服务
echo ""
echo "⏹️ 停止现有服务..."
docker-compose down

# 4. 检查数据库表数量
echo ""
echo "🔍 检查数据库状态..."
docker-compose up -d db
sleep 5

table_count=$(docker-compose exec -T db psql -U postgres -d discord_bot -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' \n' || echo "0")

echo "数据库表数量: $table_count"

if [ "$table_count" -lt "4" ]; then
    echo "❌ 数据库表不完整，需要迁移"
    NEED_DB_MIGRATION=1
else
    echo "✅ 数据库表完整"
fi

# 5. 执行数据库迁移（如果需要）
if [ "$NEED_DB_MIGRATION" = "1" ]; then
    echo ""
    echo "🔄 执行数据库迁移..."
    
    # 创建迁移脚本（如果不存在）
    if [ ! -f "migrate-database-fields.py" ]; then
        echo "📥 下载数据库迁移脚本..."
        # 这里应该是从git拉取最新代码
        git pull origin main 2>/dev/null || echo "Git拉取失败，手动创建迁移脚本"
    fi
    
    # 执行迁移
    if [ -f "migrate-database-fields.py" ]; then
        python3 migrate-database-fields.py
    else
        echo "⚠️ 迁移脚本不存在，将在重建时自动创建表"
    fi
fi

# 6. 停止数据库，准备完整重启
docker-compose down

# 7. 清理并重建
echo ""
echo "🔧 重建Docker镜像..."
docker system prune -f
docker-compose build --no-cache

# 8. 启动所有服务
echo ""
echo "🚀 启动所有服务..."
docker-compose up -d

# 9. 等待启动并检查
echo ""
echo "⏳ 等待服务启动..."
for i in {1..30}; do
    echo -n "."
    sleep 2
done
echo ""

# 10. 检查服务状态
echo ""
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "📋 检查机器人日志..."
docker-compose logs discord-bot --tail=15

echo ""
echo "📋 检查数据库表..."
docker-compose exec -T db psql -U postgres -d discord_bot -c "\dt" 2>/dev/null || echo "数据库连接检查失败"

# 11. 健康检查
echo ""
echo "🏥 健康检查..."
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ API健康检查通过"
    curl -s http://localhost:5000/health | head -5
else
    echo "⚠️ API健康检查失败"
fi

echo ""
echo "🎉 VPS修复完成!"
echo ""
echo "如果仍有问题:"
echo "1. 检查环境变量: cat .env"
echo "2. 查看详细日志: docker-compose logs discord-bot"
echo "3. 重启服务: docker-compose restart"