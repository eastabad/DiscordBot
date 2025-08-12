#!/bin/bash

# 修复Python环境脚本

echo "🔧 修复Python环境"
echo "==================="

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
else
    OS=$(uname -s)
fi

echo "检测到系统: $OS"

# 更新包管理器
echo "更新包管理器..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt update
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    sudo yum update -y
fi

# 安装Python3
echo "安装Python3..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt install -y python3 python3-pip python3-venv
    # 创建python软链接
    if ! command -v python &> /dev/null; then
        sudo apt install -y python-is-python3
    fi
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    sudo yum install -y python3 python3-pip
    # 创建python软链接
    if ! command -v python &> /dev/null; then
        sudo alternatives --install /usr/bin/python python /usr/bin/python3 1
    fi
fi

# 验证安装
echo "验证Python安装..."
python3 --version
pip3 --version

if command -v python &> /dev/null; then
    python --version
else
    echo "创建python软链接..."
    sudo ln -sf /usr/bin/python3 /usr/bin/python
fi

# 安装必需的Python包
echo "安装Python依赖包..."
pip3 install --upgrade pip
pip3 install flask psutil sqlalchemy psycopg2-binary aiohttp discord.py python-dotenv

echo "✅ Python环境修复完成"
echo ""
echo "现在可以使用以下命令:"
echo "python3 simple_log_viewer.py"
echo "或者:"
echo "python simple_log_viewer.py"