#!/bin/bash

# VPS Discord机器人无限制版本一键部署脚本
# 支持Ubuntu/Debian/CentOS系统

set -e  # 遇到错误立即退出

echo "🚀 Discord机器人VPS无限制版本部署"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}警告: 检测到root用户，建议使用普通用户运行此脚本${NC}"
   read -p "是否继续？ (y/N): " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    echo -e "${BLUE}检测到系统: $OS $VER${NC}"
}

# 安装Docker
install_docker() {
    echo -e "${YELLOW}正在安装Docker...${NC}"
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}Docker已安装，跳过安装步骤${NC}"
        return
    fi
    
    # 通用Docker安装
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    
    echo -e "${GREEN}Docker安装完成${NC}"
}

# 安装Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}正在安装Docker Compose...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}Docker Compose已安装，跳过安装步骤${NC}"
        return
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}Docker Compose安装完成${NC}"
}

# 配置防火墙
setup_firewall() {
    echo -e "${YELLOW}配置防火墙规则...${NC}"
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow ssh
        sudo ufw allow 5000/tcp
        sudo ufw allow 5001/tcp
        sudo ufw --force enable
        echo -e "${GREEN}UFW防火墙配置完成${NC}"
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=5000/tcp
        sudo firewall-cmd --permanent --add-port=5001/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}Firewalld防火墙配置完成${NC}"
    else
        echo -e "${YELLOW}未检测到防火墙，请手动开放端口5000和5001${NC}"
    fi
}

# 克隆项目
clone_project() {
    echo -e "${YELLOW}克隆项目代码...${NC}"
    
    if [ -d "DiscordBot" ]; then
        echo -e "${YELLOW}项目目录已存在，是否删除重新克隆？ (y/N): ${NC}"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf DiscordBot
        else
            cd DiscordBot
            echo -e "${GREEN}使用现有项目目录${NC}"
            return
        fi
    fi
    
    git clone https://github.com/eastabad/DiscordBot.git
    cd DiscordBot
    echo -e "${GREEN}项目克隆完成${NC}"
}

# 配置环境变量
setup_environment() {
    echo -e "${YELLOW}配置环境变量...${NC}"
    
    # 复制示例配置
    cp .env.example .env
    
    echo ""
    echo -e "${BLUE}请提供以下配置信息：${NC}"
    echo ""
    
    # Discord Token (必需)
    while true; do
        read -p "Discord Bot Token (必需): " discord_token
        if [[ -n "$discord_token" ]]; then
            sed -i "s/your_discord_bot_token_here/$discord_token/" .env
            break
        else
            echo -e "${RED}Discord Token是必需的，请重新输入${NC}"
        fi
    done
    
    # 可选配置
    echo ""
    echo -e "${BLUE}可选配置 (直接回车跳过)：${NC}"
    
    read -p "TradingView Chart API Key (可选): " chart_api_key
    if [[ -n "$chart_api_key" ]]; then
        sed -i "s/your_chart_img_api_key/$chart_api_key/" .env
    fi
    
    read -p "TradingView Layout ID (可选): " layout_id
    if [[ -n "$layout_id" ]]; then
        sed -i "s/your_layout_id/$layout_id/" .env
    fi
    
    read -p "监控频道IDs (用逗号分隔，可选): " channel_ids
    if [[ -n "$channel_ids" ]]; then
        sed -i "s/1234567890,0987654321/$channel_ids/" .env
    fi
    
    # 确保VPS部署模式已启用
    if ! grep -q "VPS_DEPLOYMENT=true" .env; then
        echo "VPS_DEPLOYMENT=true" >> .env
    fi
    
    echo -e "${GREEN}环境配置完成 - VPS无限制模式已启用${NC}"
    
    # 显示配置摘要
    echo ""
    echo -e "${BLUE}配置摘要：${NC}"
    echo "- Discord Token: ✅ 已设置"
    echo "- VPS无限制模式: ✅ 已启用"
    echo "- Chart API: $([ -n "$chart_api_key" ] && echo "✅ 已设置" || echo "⏭️ 跳过")"
    echo "- 监控频道: $([ -n "$channel_ids" ] && echo "✅ 已设置" || echo "⏭️ 跳过")"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动Discord机器人服务...${NC}"
    
    # 构建并启动容器
    docker-compose build
    docker-compose up -d
    
    echo -e "${GREEN}服务启动完成${NC}"
    echo ""
    echo -e "${BLUE}等待服务初始化...${NC}"
    sleep 10
}

# 验证部署
verify_deployment() {
    echo -e "${YELLOW}验证部署状态...${NC}"
    
    # 检查容器状态
    echo "检查容器状态..."
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ 容器运行正常${NC}"
    else
        echo -e "${RED}❌ 容器启动失败${NC}"
        echo "查看错误日志:"
        docker-compose logs discord-bot
        return 1
    fi
    
    # 检查健康状态
    echo "检查健康状态..."
    if curl -f http://localhost:5000/health &> /dev/null; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"
    else
        echo -e "${YELLOW}⚠️ 健康检查暂时失败，可能还在启动中${NC}"
    fi
    
    # 检查VPS模式
    echo "验证VPS无限制模式..."
    if docker-compose logs discord-bot 2>/dev/null | grep -q "VPS部署模式" || docker-compose logs discord-bot 2>/dev/null | grep -q "机器人已登录"; then
        echo -e "${GREEN}✅ VPS无限制模式已启用${NC}"
    else
        echo -e "${YELLOW}⚠️ 正在启动中，请稍后查看日志${NC}"
    fi
}

# 显示部署信息
show_deployment_info() {
    # 获取外部IP
    EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "未知")
    
    echo ""
    echo -e "${GREEN}🎉 Discord机器人部署完成！${NC}"
    echo "=================================="
    echo ""
    echo -e "${BLUE}部署信息：${NC}"
    echo "- 部署模式: VPS无限制版本"
    echo "- 所有用户: 无使用次数限制"
    echo "- 健康检查: http://localhost:5000/health"
    if [[ "$EXTERNAL_IP" != "未知" ]]; then
        echo "- 外部访问: http://$EXTERNAL_IP:5000/health"
        echo "- 日志查看: http://$EXTERNAL_IP:5001/"
    fi
    echo ""
    echo -e "${BLUE}管理命令：${NC}"
    echo "docker-compose ps              # 查看容器状态"
    echo "docker-compose logs discord-bot # 查看机器人日志"
    echo "docker-compose restart         # 重启服务"
    echo "docker-compose down            # 停止服务"
    echo ""
    echo -e "${BLUE}Discord机器人命令：${NC}"
    echo "!vps_status    # 查看VPS部署状态"
    echo "!logs          # 查看使用统计"
    echo "!quota         # 查看个人配额 (显示无限制)"
    echo ""
    echo -e "${YELLOW}注意事项：${NC}"
    echo "- 确保Discord机器人已被邀请到服务器"
    echo "- 在Discord中测试: @机器人 AAPL,1h"
    echo "- 所有用户都可以无限次使用功能"
    echo ""
    
    # 提示查看日志
    echo -e "${BLUE}实时查看启动日志：${NC}"
    echo "docker-compose logs -f discord-bot"
}

# 主函数
main() {
    echo -e "${BLUE}开始VPS无限制版本部署...${NC}"
    echo ""
    
    detect_os
    install_docker
    install_docker_compose
    setup_firewall
    clone_project
    setup_environment
    start_services
    verify_deployment
    show_deployment_info
    
    echo ""
    echo -e "${GREEN}✅ 部署流程已完成！${NC}"
    echo ""
    
    # 询问是否查看实时日志
    read -p "是否现在查看机器人启动日志？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "按 Ctrl+C 退出日志查看"
        sleep 2
        docker-compose logs -f discord-bot
    fi
}

# 运行主函数
main "$@"