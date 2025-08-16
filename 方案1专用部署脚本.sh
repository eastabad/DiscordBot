#!/bin/bash

echo "=== Discord Bot + V2Ray 共享443端口部署脚本 ==="
echo "自动在现有v2ray配置中添加Discord Bot功能"
echo ""

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用sudo运行此脚本: sudo bash 方案1专用部署脚本.sh"
    exit 1
fi

# 获取当前日期时间作为备份后缀
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)

echo "🔍 第1步: 检测v2ray nginx配置..."

# 查找可能的v2ray配置文件
V2RAY_CONFIG=""
for config in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf /etc/nginx/nginx.conf; do
    if [ -f "$config" ] && grep -q "443" "$config" && grep -q "tdindicator.top" "$config"; then
        echo "发现tdindicator.top的443端口配置: $config"
        V2RAY_CONFIG="$config"
        break
    fi
done

# 如果没找到tdindicator.top，查找其他443配置
if [ -z "$V2RAY_CONFIG" ]; then
    for config in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
        if [ -f "$config" ] && grep -q "443" "$config"; then
            echo "发现443端口配置文件: $config"
            if grep -q "server_name" "$config"; then
                echo "配置中的域名:"
                grep "server_name" "$config"
                read -p "这是你的v2ray配置文件吗？(y/n): " confirm
                if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                    V2RAY_CONFIG="$config"
                    break
                fi
            fi
        fi
    done
fi

if [ -z "$V2RAY_CONFIG" ]; then
    echo "❌ 未找到443端口的nginx配置文件"
    echo "请手动指定配置文件路径："
    read -p "输入配置文件完整路径: " V2RAY_CONFIG
    if [ ! -f "$V2RAY_CONFIG" ]; then
        echo "❌ 配置文件不存在: $V2RAY_CONFIG"
        exit 1
    fi
fi

echo "✅ 使用配置文件: $V2RAY_CONFIG"

echo ""
echo "📁 第2步: 备份现有配置..."
cp "$V2RAY_CONFIG" "${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX"
echo "✅ 配置已备份为: ${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX"

echo ""
echo "📝 第3步: 分析现有配置结构..."

# 检查是否已经有Discord Bot配置
if grep -q "/webhook/" "$V2RAY_CONFIG" || grep -q "/api/" "$V2RAY_CONFIG"; then
    echo "⚠️  检测到可能已存在Discord Bot配置"
    read -p "是否要覆盖现有配置？(y/n): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "取消部署"
        exit 0
    fi
    # 删除现有Discord Bot配置
    sed -i '/# Discord Bot/,/^    }/d' "$V2RAY_CONFIG"
fi

echo ""
echo "⚡ 第4步: 添加Discord Bot配置到v2ray..."

# 创建临时配置片段
cat > /tmp/discord_bot_insert.txt << 'EOF'

    # Discord Bot Webhook - TradingView数据接收
    location /webhook/ {
        proxy_pass http://127.0.0.1:5000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }

    # Discord Bot API - 消息发送等功能
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }

    # Discord Bot状态监控
    location /bot-status {
        proxy_pass http://127.0.0.1:5000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Discord Bot API文档
    location /bot-api {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
EOF

# 智能插入配置 - 找到443端口的server块，在最后一个location之后、}之前插入
python3 << 'PYTHON_EOF'
import re
import sys

config_file = sys.argv[1]
insert_file = '/tmp/discord_bot_insert.txt'

with open(config_file, 'r', encoding='utf-8') as f:
    content = f.read()

with open(insert_file, 'r', encoding='utf-8') as f:
    insert_content = f.read()

# 查找443端口的server块
pattern = r'(server\s*\{[^}]*listen\s+443[^}]*?)(\})'
matches = list(re.finditer(pattern, content, re.DOTALL))

if matches:
    # 在最后一个匹配的server块的}前插入配置
    last_match = matches[-1]
    new_content = content[:last_match.end()-1] + insert_content + '\n' + content[last_match.end()-1:]
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Discord Bot配置已成功添加到443端口server块")
else:
    print("❌ 未找到443端口的server块")
    sys.exit(1)
PYTHON_EOF "$V2RAY_CONFIG"

if [ $? -ne 0 ]; then
    echo "Python配置插入失败，尝试sed方法..."
    
    # 备用sed方法 - 查找包含443的server块
    if grep -q "listen.*443" "$V2RAY_CONFIG"; then
        # 在最后一个}前插入（简单方法）
        sed -i '$i\\n    # Discord Bot Webhook - TradingView数据接收\n    location /webhook/ {\n        proxy_pass http://127.0.0.1:5000/webhook/;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_connect_timeout 60s;\n        proxy_send_timeout 60s;\n        proxy_read_timeout 60s;\n        client_max_body_size 10M;\n    }\n\n    # Discord Bot API - 消息发送等功能\n    location /api/ {\n        proxy_pass http://127.0.0.1:5000/api/;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_connect_timeout 60s;\n        proxy_send_timeout 60s;\n        proxy_read_timeout 60s;\n        client_max_body_size 10M;\n    }\n\n    # Discord Bot状态监控\n    location /bot-status {\n        proxy_pass http://127.0.0.1:5000/api/health;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }\n\n    # Discord Bot API文档\n    location /bot-api {\n        proxy_pass http://127.0.0.1:5000/;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }' "$V2RAY_CONFIG"
        echo "✅ 使用sed方法添加Discord Bot配置"
    else
        echo "❌ 未找到443端口配置，请手动添加"
        cat /tmp/discord_bot_insert.txt
        exit 1
    fi
fi

echo ""
echo "🧪 第5步: 测试nginx配置..."
if nginx -t; then
    echo "✅ nginx配置测试通过"
else
    echo "❌ nginx配置测试失败"
    echo "正在恢复备份..."
    cp "${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX" "$V2RAY_CONFIG"
    echo "已恢复备份，请检查配置后重试"
    echo ""
    echo "可能的问题："
    echo "1. 配置文件格式不正确"
    echo "2. 缺少必要的nginx模块"
    echo "3. 权限问题"
    echo ""
    echo "查看详细错误: sudo nginx -t"
    exit 1
fi

echo ""
echo "🔄 第6步: 重新加载nginx..."
if systemctl reload nginx; then
    echo "✅ nginx已重新加载"
else
    echo "❌ nginx重新加载失败"
    echo "正在恢复备份..."
    cp "${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX" "$V2RAY_CONFIG"
    systemctl reload nginx
    echo "已恢复备份"
    exit 1
fi

echo ""
echo "📊 第7步: 验证部署结果..."

# 检查Discord Bot是否运行
if curl -s http://127.0.0.1:5000/api/health > /dev/null; then
    echo "✅ Discord Bot在5000端口正常运行"
else
    echo "⚠️  Discord Bot未在5000端口运行，请启动Bot"
fi

# 检查外部访问
echo "🧪 测试外部访问..."
sleep 2
if curl -s -k https://www.tdindicator.top/bot-status > /dev/null; then
    echo "✅ 外部HTTPS访问正常"
else
    echo "⚠️  外部访问测试失败，可能需要等待DNS刷新"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "🔗 Discord Bot API地址（与v2ray共享443端口）:"
echo "   • TradingView Webhook:     https://www.tdindicator.top/webhook/tradingview"
echo "   • Bot健康检查:             https://www.tdindicator.top/bot-status"  
echo "   • Bot API文档:             https://www.tdindicator.top/bot-api"
echo "   • 发送Discord消息:         https://www.tdindicator.top/api/send-message"
echo "   • 发送私信:                https://www.tdindicator.top/api/send-dm"
echo "   • 发送图表:                https://www.tdindicator.top/api/send-chart"
echo ""
echo "🧪 测试命令："
echo "   curl https://www.tdindicator.top/bot-status"
echo "   curl -X POST https://www.tdindicator.top/webhook/tradingview \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"symbol\":\"AAPL\",\"action\":\"buy\",\"price\":150.00}'"
echo ""
echo "✅ V2Ray翻墙功能保持完全不变"
echo "✅ 你的现有网站保持完全不变"
echo "✅ Discord Bot功能已添加到相同的443端口"
echo ""
echo "📝 配置备份位置: ${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX"
echo "🔄 如需回滚: sudo cp ${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX $V2RAY_CONFIG && sudo systemctl reload nginx"

# 清理临时文件
rm -f /tmp/discord_bot_insert.txt