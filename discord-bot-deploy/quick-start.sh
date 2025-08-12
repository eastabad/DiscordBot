#!/bin/bash
echo "🚀 Discord机器人快速启动脚本"
echo ""

# 检查环境文件
if [ ! -f .env ]; then
    echo "⚠️  请先配置环境变量："
    echo "cp .env.example .env"
    echo "nano .env"
    exit 1
fi

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，运行部署脚本："
    echo "./vps-deploy.sh"
    exit 1
fi

# 启动服务
echo "🐳 启动Docker服务..."
docker-compose up -d

echo "✅ 启动完成！"
echo "🔍 查看日志: docker-compose logs -f"
echo "🌐 健康检查: curl http://localhost:5000/health"
