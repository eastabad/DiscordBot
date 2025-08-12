#!/bin/bash
# 创建VPS部署包

echo "📦 正在创建VPS部署包..."

# 创建部署目录
DEPLOY_DIR="discord-bot-deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# 复制必要文件
echo "📋 复制部署文件..."
cp main.py "$DEPLOY_DIR/"
cp bot.py "$DEPLOY_DIR/"
cp config.py "$DEPLOY_DIR/"
cp *.py "$DEPLOY_DIR/" 2>/dev/null || true
cp Dockerfile "$DEPLOY_DIR/"
cp docker-compose.yml "$DEPLOY_DIR/"
cp docker-requirements.txt "$DEPLOY_DIR/"
cp .env.example "$DEPLOY_DIR/"
cp .dockerignore "$DEPLOY_DIR/"
cp vps-deploy.sh "$DEPLOY_DIR/"
cp VPS_DEPLOYMENT_GUIDE.md "$DEPLOY_DIR/"

# 创建README
cat > "$DEPLOY_DIR/README.md" << 'EOF'
# Discord机器人VPS部署包

## 快速开始

1. **上传到VPS**:
   ```bash
   scp -r discord-bot-deploy/ user@your-vps-ip:~/
   ```

2. **连接VPS并部署**:
   ```bash
   ssh user@your-vps-ip
   cd discord-bot-deploy
   chmod +x vps-deploy.sh
   ./vps-deploy.sh
   ```

3. **配置环境变量**:
   ```bash
   nano .env
   # 至少设置 DISCORD_TOKEN
   ```

4. **启动机器人**:
   ```bash
   docker-compose up -d
   ```

## 文件说明

- `main.py` - 主程序入口 (包含健康检查)
- `Dockerfile` - Docker镜像定义
- `docker-compose.yml` - 服务编排
- `vps-deploy.sh` - 一键部署脚本
- `VPS_DEPLOYMENT_GUIDE.md` - 详细部署指南

## 健康检查

部署成功后访问: `http://your-vps-ip:5000/health`

## 支持系统

- Ubuntu 20.04+
- Debian 11+
- CentOS 8+
- Rocky Linux 8+
EOF

# 创建快速启动脚本
cat > "$DEPLOY_DIR/quick-start.sh" << 'EOF'
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
EOF

chmod +x "$DEPLOY_DIR/quick-start.sh"
chmod +x "$DEPLOY_DIR/vps-deploy.sh"

# 创建压缩包
echo "🗜️ 创建压缩包..."
tar -czf discord-bot-deploy.tar.gz "$DEPLOY_DIR"

echo "✅ 部署包创建完成："
echo "📁 目录: $DEPLOY_DIR/"
echo "📦 压缩包: discord-bot-deploy.tar.gz"
echo ""
echo "📤 上传到VPS命令:"
echo "scp discord-bot-deploy.tar.gz user@your-vps-ip:~/"
echo "ssh user@your-vps-ip"
echo "tar -xzf discord-bot-deploy.tar.gz"
echo "cd discord-bot-deploy"
echo "./vps-deploy.sh"