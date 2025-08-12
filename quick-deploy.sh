#!/bin/bash

# 快速部署脚本 - 本地开发到VPS一键部署
# 包含代码提交、推送和VPS更新

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

main() {
    echo "⚡ Discord机器人快速部署工具"
    echo "=============================="
    echo ""
    
    # 检查Git状态
    log_info "检查Git状态..."
    if ! git diff --quiet; then
        log_info "发现未提交的更改:"
        git status --porcelain
        echo ""
        
        # 自动提交
        read -p "请输入提交信息 (回车使用默认): " commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="自动更新 $(date '+%Y-%m-%d %H:%M:%S')"
        fi
        
        log_info "提交更改..."
        git add .
        git commit -m "$commit_msg"
        log_success "代码已提交"
    else
        log_info "没有待提交的更改"
    fi
    
    # 推送到远程仓库
    current_branch=$(git branch --show-current)
    log_info "推送到远程仓库 ($current_branch)..."
    git push origin $current_branch
    log_success "代码已推送到GitHub"
    
    # 更新VPS
    log_info "开始更新VPS..."
    if [ -f "update-vps.sh" ]; then
        ./update-vps.sh
    else
        log_warning "未找到update-vps.sh文件"
        exit 1
    fi
    
    log_success "快速部署完成！"
}

# 运行主函数
main "$@"