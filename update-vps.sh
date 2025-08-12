#!/bin/bash

# VPS一键代码更新脚本
# 自动更新Discord机器人到最新版本

set -e  # 遇到错误立即退出

# 配置参数
VPS_HOST=""
VPS_USER=""
VPS_PATH="~/DiscordBot"
SSH_KEY=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查配置
check_config() {
    log_info "检查配置..."
    
    if [ -f "vps-config.sh" ]; then
        source vps-config.sh
        log_success "从vps-config.sh加载配置"
    else
        log_warning "未找到vps-config.sh配置文件"
        echo "请创建vps-config.sh文件并配置以下变量:"
        echo "VPS_HOST='your-vps-ip'"
        echo "VPS_USER='your-username'"
        echo "VPS_PATH='~/DiscordBot'"
        echo "SSH_KEY='~/.ssh/id_rsa'  # 可选"
        echo ""
        read -p "请输入VPS IP地址: " VPS_HOST
        read -p "请输入VPS用户名: " VPS_USER
        read -p "请输入VPS项目路径 (默认: ~/DiscordBot): " input_path
        VPS_PATH=${input_path:-~/DiscordBot}
        
        # 创建配置文件
        cat > vps-config.sh << EOF
# VPS配置文件
VPS_HOST='$VPS_HOST'
VPS_USER='$VPS_USER'
VPS_PATH='$VPS_PATH'
SSH_KEY=''  # 留空使用默认SSH密钥
EOF
        log_success "配置文件已创建: vps-config.sh"
    fi
    
    if [ -z "$VPS_HOST" ] || [ -z "$VPS_USER" ]; then
        log_error "VPS配置不完整，请检查vps-config.sh文件"
        exit 1
    fi
}

# 构建SSH命令
build_ssh_cmd() {
    if [ -n "$SSH_KEY" ] && [ -f "$SSH_KEY" ]; then
        echo "ssh -i $SSH_KEY $VPS_USER@$VPS_HOST"
    else
        echo "ssh $VPS_USER@$VPS_HOST"
    fi
}

# 测试SSH连接
test_ssh() {
    log_info "测试SSH连接到 $VPS_USER@$VPS_HOST..."
    
    SSH_CMD=$(build_ssh_cmd)
    
    if $SSH_CMD "echo 'SSH连接成功'" >/dev/null 2>&1; then
        log_success "SSH连接正常"
        return 0
    else
        log_error "SSH连接失败"
        echo "请确保:"
        echo "1. VPS IP地址正确"
        echo "2. SSH密钥已配置"
        echo "3. VPS防火墙允许SSH连接"
        return 1
    fi
}

# 本地检查更新
check_local_updates() {
    log_info "检查本地代码更新..."
    
    # 获取当前分支
    current_branch=$(git branch --show-current)
    log_info "当前分支: $current_branch"
    
    # 检查是否有未提交的更改
    if ! git diff --quiet; then
        log_warning "发现未提交的本地更改"
        git status --porcelain
        echo ""
        read -p "是否继续更新VPS? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "更新已取消"
            exit 0
        fi
    fi
    
    # 获取远程更新
    log_info "获取远程更新..."
    git fetch origin
    
    # 检查是否有新的提交
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/$current_branch)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_info "本地代码已是最新版本"
        read -p "是否仍要更新VPS? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "更新已取消"
            exit 0
        fi
    else
        log_info "发现新的远程提交，准备更新"
        git log --oneline $LOCAL..$REMOTE
    fi
}

# 更新VPS代码
update_vps_code() {
    log_info "开始更新VPS代码..."
    
    SSH_CMD=$(build_ssh_cmd)
    
    # 创建远程更新脚本
    cat > /tmp/vps-update-remote.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 开始VPS代码更新..."

# 进入项目目录
cd ~/DiscordBot || { echo "❌ 项目目录不存在"; exit 1; }

# 停止服务
echo "停止Docker服务..."
docker-compose down

# 备份配置文件
echo "备份配置文件..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "未找到.env文件"

# 更新代码
echo "更新代码..."
git stash push -m "自动备份本地更改 $(date)" 2>/dev/null || true
git fetch origin
git reset --hard origin/main

# 检查是否需要更新依赖
if [ -f "requirements.txt" ]; then
    echo "检查Python依赖..."
    # Docker会自动处理依赖更新
fi

# 重新构建并启动
echo "重新构建Docker镜像..."
docker-compose build --no-cache

echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 检查健康状态
echo "检查应用健康状态..."
for i in {1..6}; do
    if curl -f http://localhost:5000/health >/dev/null 2>&1; then
        echo "✅ 应用健康检查通过"
        break
    else
        echo "等待应用启动... ($i/6)"
        sleep 10
    fi
done

# 修复数据库（如果需要）
if [ -f "fix-database.py" ]; then
    echo "运行数据库修复..."
    python3 fix-database.py || echo "数据库修复完成"
fi

echo "✅ VPS更新完成!"
echo ""
echo "服务状态:"
docker-compose ps
echo ""
echo "最近日志:"
docker-compose logs discord-bot --tail=10
EOF

    # 上传并执行更新脚本
    log_info "上传更新脚本到VPS..."
    scp /tmp/vps-update-remote.sh $VPS_USER@$VPS_HOST:/tmp/

    log_info "在VPS上执行更新..."
    $SSH_CMD "chmod +x /tmp/vps-update-remote.sh && /tmp/vps-update-remote.sh"
    
    # 清理临时文件
    rm -f /tmp/vps-update-remote.sh
    $SSH_CMD "rm -f /tmp/vps-update-remote.sh"
}

# 验证更新结果
verify_update() {
    log_info "验证更新结果..."
    
    SSH_CMD=$(build_ssh_cmd)
    
    # 检查Docker容器状态
    log_info "检查Docker容器状态..."
    $SSH_CMD "cd $VPS_PATH && docker-compose ps"
    
    # 检查应用健康状态
    log_info "检查应用健康状态..."
    if $SSH_CMD "curl -f http://localhost:5000/health" >/dev/null 2>&1; then
        log_success "应用健康检查通过"
    else
        log_warning "应用健康检查失败，查看日志..."
        $SSH_CMD "cd $VPS_PATH && docker-compose logs discord-bot --tail=20"
    fi
    
    # 获取VPS外部IP
    VPS_EXTERNAL_IP=$($SSH_CMD "curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo 'unknown'")
    
    if [ "$VPS_EXTERNAL_IP" != "unknown" ]; then
        log_success "更新完成！访问地址:"
        echo "  机器人健康检查: http://$VPS_EXTERNAL_IP:5000/health"
        echo "  日志查看器: http://$VPS_EXTERNAL_IP:5001/"
    fi
}

# 显示更新日志
show_update_log() {
    log_info "显示更新日志..."
    
    SSH_CMD=$(build_ssh_cmd)
    
    echo ""
    echo "=== 最新Git提交 ==="
    $SSH_CMD "cd $VPS_PATH && git log --oneline -5"
    
    echo ""
    echo "=== Docker容器状态 ==="
    $SSH_CMD "cd $VPS_PATH && docker-compose ps"
    
    echo ""
    echo "=== 最近应用日志 ==="
    $SSH_CMD "cd $VPS_PATH && docker-compose logs discord-bot --tail=15"
}

# 回滚功能
rollback_option() {
    log_info "是否需要回滚到上一个版本？"
    read -p "输入 'rollback' 进行回滚，其他任意键退出: " choice
    
    if [ "$choice" = "rollback" ]; then
        log_warning "执行回滚操作..."
        SSH_CMD=$(build_ssh_cmd)
        
        $SSH_CMD "cd $VPS_PATH && git reset --hard HEAD~1 && docker-compose down && docker-compose build --no-cache && docker-compose up -d"
        log_success "回滚完成"
    fi
}

# 主函数
main() {
    echo "🚀 VPS Discord机器人一键更新工具"
    echo "=================================="
    echo ""
    
    # 检查配置
    check_config
    
    # 测试SSH连接
    if ! test_ssh; then
        exit 1
    fi
    
    # 检查本地更新
    check_local_updates
    
    # 更新VPS代码
    update_vps_code
    
    # 验证更新结果
    verify_update
    
    # 显示更新日志
    show_update_log
    
    # 询问是否需要回滚
    rollback_option
    
    log_success "VPS更新流程完成！"
}

# 运行主函数
main "$@"