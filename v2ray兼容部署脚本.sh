#!/bin/bash

echo "=== V2Ray兼容的Discord Bot部署脚本 ==="
echo "这个脚本将在你现有的v2ray配置中添加Discord Bot功能"
echo ""

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用sudo运行此脚本: sudo bash v2ray兼容部署脚本.sh"
    exit 1
fi

# 获取当前日期时间作为备份后缀
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)

echo "🔍 第1步: 检测v2ray nginx配置..."

# 查找可能的v2ray配置文件
V2RAY_CONFIG=""
for config in /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf; do
    if [ -f "$config" ] && grep -q "443" "$config"; then
        echo "发现443端口配置文件: $config"
        V2RAY_CONFIG="$config"
        break
    fi
done

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
echo "📝 第3步: 生成Discord Bot配置片段..."

# 创建临时配置片段
cat > /tmp/discord_bot_locations.conf << 'EOF'

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

echo "✅ Discord Bot配置片段已生成"

echo ""
echo "⚡ 第4步: 选择部署方式..."
echo "1. 自动添加到现有配置（推荐）"
echo "2. 手动合并（显示配置内容让你手动添加）"
echo "3. 创建独立配置使用8443端口"

read -p "请选择部署方式 (1/2/3): " DEPLOY_METHOD

case $DEPLOY_METHOD in
    1)
        echo "🔧 自动添加Discord Bot配置到现有文件..."
        
        # 查找server块的最后一个}，在它之前插入Discord Bot配置
        if grep -q "server_name.*tdindicator.top" "$V2RAY_CONFIG"; then
            # 找到包含tdindicator.top的server块，在其}前插入配置
            sed -i '/server_name.*tdindicator\.top/,/^}$/{
                /^}$/i\
    # Discord Bot Webhook - TradingView数据接收\
    location /webhook/ {\
        proxy_pass http://127.0.0.1:5000/webhook/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 60s;\
        proxy_read_timeout 60s;\
        client_max_body_size 10M;\
    }\
\
    # Discord Bot API - 消息发送等功能\
    location /api/ {\
        proxy_pass http://127.0.0.1:5000/api/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 60s;\
        proxy_read_timeout 60s;\
        client_max_body_size 10M;\
    }\
\
    # Discord Bot状态监控\
    location /bot-status {\
        proxy_pass http://127.0.0.1:5000/api/health;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }\
\
    # Discord Bot API文档\
    location /bot-api {\
        proxy_pass http://127.0.0.1:5000/;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
    }
            }' "$V2RAY_CONFIG"
            echo "✅ Discord Bot配置已自动添加到现有配置"
        else
            echo "❌ 未找到tdindicator.top的server配置块"
            echo "请选择手动合并方式（选项2）"
            exit 1
        fi
        ;;
    2)
        echo "📋 请手动将以下配置添加到你的nginx配置文件中的server块内："
        echo "────────────────────────────────────────────────────────"
        cat /tmp/discord_bot_locations.conf
        echo "────────────────────────────────────────────────────────"
        echo ""
        echo "添加位置：在你的server块中，其他location之后，}之前"
        echo "配置文件位置：$V2RAY_CONFIG"
        echo ""
        read -p "手动添加完成后按回车继续..."
        ;;
    3)
        echo "🔧 创建8443端口的独立配置..."
        cat > /etc/nginx/sites-available/discord-bot-8443 << 'EOF'
server {
    listen 8443 ssl http2;
    listen [::]:8443 ssl http2;
    server_name www.tdindicator.top tdindicator.top;

    # SSL证书配置（使用现有证书）
    ssl_certificate /etc/letsencrypt/live/www.tdindicator.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.tdindicator.top/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Discord Bot Webhook
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

    # Discord Bot API
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

    # Discord Bot状态和文档
    location /bot-status {
        proxy_pass http://127.0.0.1:5000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /bot-api {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        return 404;
    }
}
EOF
        
        ln -sf /etc/nginx/sites-available/discord-bot-8443 /etc/nginx/sites-enabled/
        echo "✅ 独立配置已创建，使用端口8443"
        echo "需要开放防火墙端口: sudo ufw allow 8443"
        ;;
esac

echo ""
echo "🧪 第5步: 测试nginx配置..."
if nginx -t; then
    echo "✅ nginx配置测试通过"
else
    echo "❌ nginx配置测试失败"
    echo "正在恢复备份..."
    cp "${V2RAY_CONFIG}.backup.$BACKUP_SUFFIX" "$V2RAY_CONFIG"
    echo "已恢复备份，请检查配置后重试"
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
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo ""

if [ "$DEPLOY_METHOD" = "3" ]; then
    echo "🔗 Discord Bot API地址（8443端口）:"
    echo "   • TradingView Webhook:     https://www.tdindicator.top:8443/webhook/tradingview"
    echo "   • Bot健康检查:             https://www.tdindicator.top:8443/bot-status"
    echo "   • Bot API文档:             https://www.tdindicator.top:8443/bot-api"
    echo ""
    echo "⚠️  需要开放8443端口: sudo ufw allow 8443"
else
    echo "🔗 Discord Bot API地址（443端口，与v2ray共享）:"
    echo "   • TradingView Webhook:     https://www.tdindicator.top/webhook/tradingview"
    echo "   • Bot健康检查:             https://www.tdindicator.top/bot-status"
    echo "   • Bot API文档:             https://www.tdindicator.top/bot-api"
fi

echo ""
echo "🧪 测试命令："
if [ "$DEPLOY_METHOD" = "3" ]; then
    echo "   curl https://www.tdindicator.top:8443/bot-status"
else
    echo "   curl https://www.tdindicator.top/bot-status"
fi

echo ""
echo "✅ V2Ray翻墙功能保持完全不变"
echo "✅ Discord Bot功能已添加"
echo "🚀 现在你可以启动Discord Bot了！"

# 清理临时文件
rm -f /tmp/discord_bot_locations.conf