#!/bin/bash
# VPS部署快速测试脚本

echo "🧪 Discord机器人VPS部署快速测试"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    local test_name="$1"
    local command="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "测试: $test_name ... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        return 1
    fi
}

echo ""
echo "🔍 开始系统检查..."

# 1. Docker检查
run_test "Docker安装" "docker --version"
run_test "Docker Compose安装" "docker-compose --version"
run_test "Docker服务状态" "sudo systemctl is-active docker"

# 2. 项目文件检查
run_test "项目目录存在" "[ -d 'DiscordBot' ]"
if [ -d "DiscordBot" ]; then
    cd DiscordBot
    run_test "Docker配置文件" "[ -f 'docker-compose.yml' ]"
    run_test "环境配置文件" "[ -f '.env' ]"
    run_test "主程序文件" "[ -f 'main.py' ]"
else
    echo -e "${YELLOW}⚠️  项目目录不存在，请先克隆项目${NC}"
fi

# 3. 容器状态检查
run_test "Discord机器人容器运行" "docker-compose ps | grep discord-bot | grep -q Up"
run_test "数据库容器运行" "docker-compose ps | grep db | grep -q Up"

# 4. 网络连接检查
run_test "端口5000监听" "netstat -tuln | grep -q ':5000'"
run_test "内部健康检查" "curl -f http://localhost:5000/health"

# 获取VPS外部IP
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "未知")
if [ "$EXTERNAL_IP" != "未知" ]; then
    run_test "外部健康检查" "curl -f http://$EXTERNAL_IP:5000/health --max-time 10"
else
    echo "⚠️  无法获取外部IP，跳过外部访问测试"
fi

# 5. 日志检查
if docker-compose logs discord-bot 2>/dev/null | grep -q "机器人已登录"; then
    run_test "Discord机器人登录成功" "true"
else
    run_test "Discord机器人登录成功" "false"
fi

# 6. 数据库连接检查
run_test "数据库连接正常" "docker-compose exec -T db pg_isready -U postgres"

echo ""
echo "📊 测试结果统计"
echo "=================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "通过测试: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败测试: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo -e "成功率: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

echo ""
if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 恭喜！所有测试通过，Discord机器人部署成功！${NC}"
    echo ""
    echo "📋 部署信息:"
    echo "- 健康检查地址: http://localhost:5000/health"
    if [ "$EXTERNAL_IP" != "未知" ]; then
        echo "- 外部访问地址: http://$EXTERNAL_IP:5000/health"
    fi
    echo "- 查看日志: docker-compose logs -f discord-bot"
    echo "- 管理命令: docker-compose up/down/restart"
    
elif [ $PASSED_TESTS -gt $((TOTAL_TESTS * 7 / 10)) ]; then
    echo -e "${YELLOW}⚠️  大部分测试通过，但仍有问题需要解决${NC}"
    echo ""
    echo "🔧 建议检查:"
    echo "- 查看容器日志: docker-compose logs"
    echo "- 检查环境配置: cat .env"
    echo "- 重启服务: docker-compose restart"
    
else
    echo -e "${RED}❌ 部署可能存在严重问题${NC}"
    echo ""
    echo "🚨 紧急修复建议:"
    echo "1. 检查Docker是否正确安装"
    echo "2. 确认项目文件完整"
    echo "3. 验证环境变量配置"
    echo "4. 查看详细错误日志"
fi

echo ""
echo "🔍 详细诊断命令:"
echo "docker-compose ps              # 查看容器状态"
echo "docker-compose logs discord-bot # 查看机器人日志"
echo "curl http://localhost:5000/health # 健康检查"
echo "cat .env                       # 查看环境配置"

exit $((TOTAL_TESTS - PASSED_TESTS))