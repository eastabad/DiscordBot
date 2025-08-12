#!/bin/bash
# Discord机器人VPS部署脚本
# 适用于Ubuntu 20.04/22.04, Debian 11/12, CentOS 8/9

set -e

echo "🚀 开始Discord机器人VPS部署..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        echo -e "${RED}❌ 无法检测操作系统${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 检测到操作系统: $OS $VER${NC}"
}

# 更新系统
update_system() {
    echo -e "${BLUE}📦 更新系统包...${NC}"
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        sudo apt update && sudo apt upgrade -y
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
        sudo dnf update -y
    fi
}

# 安装Docker
install_docker() {
    echo -e "${BLUE}🐳 安装Docker...${NC}"
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker已安装${NC}"
        return
    fi
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # 安装依赖
        sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # 添加Docker官方GPG密钥
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # 添加稳定版仓库
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 安装Docker
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
        sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io
    fi
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
}

# 安装Docker Compose
install_docker_compose() {
    echo -e "${BLUE}🔧 安装Docker Compose...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose已安装${NC}"
        return
    fi
    
    # 下载最新版本的Docker Compose
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose安装完成${NC}"
}

# 安装其他必需工具
install_tools() {
    echo -e "${BLUE}🛠️ 安装必需工具...${NC}"
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        sudo apt install -y curl wget git nano htop ufw
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
        sudo dnf install -y curl wget git nano htop firewalld
    fi
}

# 配置防火墙
setup_firewall() {
    echo -e "${BLUE}🔥 配置防火墙...${NC}"
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 5000/tcp
        echo -e "${GREEN}✅ UFW防火墙配置完成${NC}"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-port=5000/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✅ Firewalld防火墙配置完成${NC}"
    fi
}

# 创建项目目录
setup_project() {
    echo -e "${BLUE}📁 设置项目目录...${NC}"
    
    PROJECT_DIR="$HOME/discord-bot"
    
    if [ -d "$PROJECT_DIR" ]; then
        echo -e "${YELLOW}⚠️  项目目录已存在，备份旧版本...${NC}"
        mv "$PROJECT_DIR" "$PROJECT_DIR-backup-$(date +%Y%m%d-%H%M%S)"
    fi
    
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 创建必要的目录
    mkdir -p daily_logs attached_assets
    
    echo -e "${GREEN}✅ 项目目录创建完成: $PROJECT_DIR${NC}"
}

# 创建环境配置文件
create_env_file() {
    echo -e "${BLUE}⚙️ 创建环境配置文件...${NC}"
    
    cat > .env << 'EOF'
# Discord配置 (必需)
DISCORD_TOKEN=

# TradingView图表API配置 (可选，但推荐)
CHART_IMG_API_KEY=
LAYOUT_ID=
TRADINGVIEW_SESSION_ID=
TRADINGVIEW_SESSION_ID_SIGN=

# Discord频道监控配置 (可选)
MONITOR_CHANNEL_IDS=

# Webhook配置 (可选)
WEBHOOK_URL=
EOF
    
    echo -e "${YELLOW}📝 请编辑 .env 文件并添加您的配置:${NC}"
    echo -e "${BLUE}nano .env${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  至少需要设置 DISCORD_TOKEN${NC}"
}

# 创建部署管理脚本
create_management_scripts() {
    echo -e "${BLUE}📜 创建管理脚本...${NC}"
    
    # 启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 启动Discord机器人..."
docker-compose up -d
echo "✅ 机器人已启动"
echo "🔍 查看日志: docker-compose logs -f"
echo "🌐 健康检查: curl http://localhost:5000/health"
EOF
    
    # 停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "⏹️ 停止Discord机器人..."
docker-compose down
echo "✅ 机器人已停止"
EOF
    
    # 重启脚本
    cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 重启Discord机器人..."
docker-compose down
docker-compose up -d
echo "✅ 机器人已重启"
EOF
    
    # 更新脚本
    cat > update.sh << 'EOF'
#!/bin/bash
echo "📥 更新Discord机器人..."
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ 机器人已更新"
EOF
    
    # 日志查看脚本
    cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 查看Discord机器人日志..."
docker-compose logs -f discord-bot
EOF
    
    # 备份脚本
    cat > backup.sh << 'EOF'
#!/bin/bash
echo "💾 备份数据..."
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r daily_logs "$BACKUP_DIR/"
cp -r attached_assets "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"
docker-compose exec db pg_dump -U postgres discord_bot > "$BACKUP_DIR/database.sql"
echo "✅ 备份完成: $BACKUP_DIR"
EOF
    
    # 设置执行权限
    chmod +x *.sh
    
    echo -e "${GREEN}✅ 管理脚本创建完成${NC}"
}

# 显示部署完成信息
show_completion_info() {
    echo ""
    echo -e "${GREEN}🎉 Discord机器人VPS部署完成！${NC}"
    echo ""
    echo -e "${BLUE}📍 项目位置:${NC} $HOME/discord-bot"
    echo -e "${BLUE}⚙️ 配置文件:${NC} $HOME/discord-bot/.env"
    echo ""
    echo -e "${YELLOW}📝 下一步操作:${NC}"
    echo "1. 编辑配置文件: cd $HOME/discord-bot && nano .env"
    echo "2. 启动机器人: ./start.sh"
    echo "3. 查看日志: ./logs.sh"
    echo "4. 健康检查: curl http://localhost:5000/health"
    echo ""
    echo -e "${BLUE}🛠️ 管理命令:${NC}"
    echo "• 启动: ./start.sh"
    echo "• 停止: ./stop.sh"
    echo "• 重启: ./restart.sh"
    echo "• 更新: ./update.sh"
    echo "• 日志: ./logs.sh"
    echo "• 备份: ./backup.sh"
    echo ""
    echo -e "${GREEN}🌐 机器人将在端口5000提供健康检查服务${NC}"
    echo -e "${GREEN}🔗 外部访问: http://$(curl -s ifconfig.me):5000/health${NC}"
}

# 主函数
main() {
    echo -e "${BLUE}=== Discord机器人VPS自动部署脚本 ===${NC}"
    echo ""
    
    detect_os
    update_system
    install_tools
    install_docker
    install_docker_compose
    setup_firewall
    setup_project
    create_env_file
    create_management_scripts
    show_completion_info
    
    echo ""
    echo -e "${GREEN}✨ 部署脚本执行完成！${NC}"
    echo -e "${YELLOW}⚠️  请记得配置 .env 文件后再启动机器人${NC}"
}

# 运行主函数
main "$@"