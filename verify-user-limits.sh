#!/bin/bash

# 用户限制功能验证脚本
# 在Docker环境中验证数据库连接和用户限制逻辑

echo "🎯 Docker环境用户限制功能验证"
echo "================================"

# 检查Docker容器状态
echo "📦 检查Docker容器..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker容器未运行，请先启动: docker-compose up -d"
    exit 1
fi

echo "✅ Docker容器运行中"

# 运行Python测试脚本
echo ""
echo "🔍 运行完整的用户限制功能测试..."
if docker-compose exec -T discord-bot python test-user-limits.py; then
    echo ""
    echo "🎉 用户限制功能验证成功！"
    echo "✅ 数据库连接正常"
    echo "✅ 用户请求计数正确"
    echo "✅ 每日限制逻辑工作"
    echo "✅ 豁免用户系统正常"
    echo ""
    echo "💡 您的Discord机器人现在具有完全工作的用户限制功能"
    echo "   - 普通用户每天限制3次请求"
    echo "   - 管理员可以通过 !exempt_add 添加豁免用户"
    echo "   - 豁免用户不受请求次数限制"
else
    echo ""
    echo "❌ 用户限制功能验证失败"
    echo "请检查Docker容器日志: docker-compose logs discord-bot"
    exit 1
fi

echo ""
echo "📊 当前数据库状态:"
docker-compose exec -T db psql -U postgres -d discord_bot -c "
SELECT 'user_request_limits' as table_name, count(*) as records FROM user_request_limits
UNION ALL
SELECT 'exempt_users' as table_name, count(*) as records FROM exempt_users;
"

echo ""
echo "✅ 验证完成 - 用户限制功能在Docker环境下完全正常工作"