#!/bin/bash

# VPS Discord机器人服务状态检查脚本

echo "🔍 Discord机器人服务状态检查"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查Docker服务状态
echo -e "${BLUE}1. Docker服务状态:${NC}"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✅ Docker服务运行中${NC}"
else
    echo -e "${RED}❌ Docker服务未运行${NC}"
    echo "启动Docker: sudo systemctl start docker"
fi
echo ""

# 检查Docker Compose容器状态
echo -e "${BLUE}2. 容器运行状态:${NC}"
if [ -f "docker-compose.yml" ]; then
    docker-compose ps
else
    echo -e "${RED}❌ 未找到docker-compose.yml文件${NC}"
fi
echo ""

# 检查端口监听状态
echo -e "${BLUE}3. 端口监听状态:${NC}"
echo "端口5000 (机器人健康检查):"
if netstat -tulpn 2>/dev/null | grep -q ":5000 "; then
    echo -e "${GREEN}✅ 端口5000已监听${NC}"
    netstat -tulpn | grep ":5000 "
else
    echo -e "${RED}❌ 端口5000未监听${NC}"
fi

echo "端口5001 (日志查看器):"
if netstat -tulpn 2>/dev/null | grep -q ":5001 "; then
    echo -e "${GREEN}✅ 端口5001已监听${NC}"
    netstat -tulpn | grep ":5001 "
else
    echo -e "${RED}❌ 端口5001未监听${NC}"
fi
echo ""

# 检查健康状态
echo -e "${BLUE}4. 服务健康检查:${NC}"
echo "机器人健康检查 (端口5000):"
if curl -f -s http://localhost:5000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 机器人健康检查通过${NC}"
    curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/health
else
    echo -e "${RED}❌ 机器人健康检查失败${NC}"
fi

echo ""
echo "日志查看器 (端口5001):"
if curl -f -s http://localhost:5001/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 日志查看器正常${NC}"
else
    echo -e "${RED}❌ 日志查看器无法访问${NC}"
fi
echo ""

# 检查最近日志
echo -e "${BLUE}5. 最近服务日志:${NC}"
if [ -f "docker-compose.yml" ]; then
    echo "Discord机器人最近日志:"
    docker-compose logs discord-bot --tail=10
    echo ""
    echo "数据库最近日志:"
    docker-compose logs db --tail=5
else
    echo -e "${RED}❌ 无法获取容器日志${NC}"
fi
echo ""

# 检查系统资源
echo -e "${BLUE}6. 系统资源使用:${NC}"
echo "内存使用:"
free -h
echo ""
echo "磁盘使用:"
df -h /
echo ""

# 提供修复建议
echo -e "${BLUE}7. 常用修复命令:${NC}"
echo "重启所有服务:"
echo "  docker-compose restart"
echo ""
echo "查看实时日志:"
echo "  docker-compose logs -f discord-bot"
echo ""
echo "重新构建并启动:"
echo "  docker-compose down && docker-compose build --no-cache && docker-compose up -d"
echo ""
echo "检查防火墙:"
echo "  sudo ufw status"
echo "  sudo ufw allow 5000/tcp"
echo "  sudo ufw allow 5001/tcp"
echo ""

# 外部访问信息
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "未知")
if [[ "$EXTERNAL_IP" != "未知" ]]; then
    echo -e "${BLUE}8. 外部访问地址:${NC}"
    echo "机器人健康检查: http://$EXTERNAL_IP:5000/health"
    echo "日志查看器: http://$EXTERNAL_IP:5001/"
    echo ""
fi

echo "=================================="
echo "状态检查完成"