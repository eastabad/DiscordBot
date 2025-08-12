#!/bin/bash

# 启动日志查看器脚本

echo "🚀 启动Discord机器人日志查看器"
echo "=================================="

# 检查Python3是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: python3未安装"
    echo "安装python3: sudo apt update && sudo apt install -y python3 python3-pip"
    exit 1
fi

# 检查必需的Python包
echo "检查Python依赖..."
python3 -c "import flask, psutil, sqlalchemy, psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装Python依赖..."
    pip3 install flask psutil sqlalchemy psycopg2-binary
fi

# 检查日志查看器文件
if [ ! -f "simple_log_viewer.py" ]; then
    echo "❌ 错误: simple_log_viewer.py文件不存在"
    exit 1
fi

# 检查端口5001是否被占用
if netstat -tulpn 2>/dev/null | grep -q ":5001 "; then
    echo "⚠️ 警告: 端口5001已被占用"
    echo "停止占用进程或使用其他端口"
    netstat -tulpn | grep ":5001 "
    echo ""
    read -p "是否强制终止占用进程? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(netstat -tulpn | grep ":5001 " | awk '{print $7}' | cut -d'/' -f1)
        if [[ -n "$PID" ]]; then
            sudo kill -9 $PID
            echo "已终止进程 $PID"
        fi
    fi
fi

# 启动日志查看器
echo "启动日志查看器在端口5001..."
export FLASK_ENV=production
export FLASK_APP=simple_log_viewer.py

# 后台启动
nohup python3 simple_log_viewer.py > log_viewer.log 2>&1 &
LOG_VIEWER_PID=$!

echo "日志查看器已启动 (PID: $LOG_VIEWER_PID)"
sleep 3

# 检查是否启动成功
if kill -0 $LOG_VIEWER_PID 2>/dev/null; then
    echo "✅ 日志查看器启动成功"
    echo "访问地址: http://localhost:5001/"
    
    # 获取外部IP
    EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null)
    if [[ -n "$EXTERNAL_IP" ]]; then
        echo "外部访问: http://$EXTERNAL_IP:5001/"
    fi
    
    echo ""
    echo "停止日志查看器: kill $LOG_VIEWER_PID"
    echo "查看日志: tail -f log_viewer.log"
else
    echo "❌ 日志查看器启动失败"
    echo "查看错误日志: cat log_viewer.log"
fi