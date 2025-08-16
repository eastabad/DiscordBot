#!/bin/bash

echo "=== Discord Bot Nginx 一键部署脚本 ==="
echo "这个脚本将为你的Discord Bot配置nginx反向代理"
echo ""

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用sudo运行此脚本: sudo bash 一键部署脚本.sh"
    exit 1
fi

# 获取当前日期时间作为备份后缀
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)

echo "📁 第1步: 备份现有nginx配置..."
if [ -f "/etc/nginx/sites-available/default" ]; then
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$BACKUP_SUFFIX
    echo "✅ 默认配置已备份为: default.backup.$BACKUP_SUFFIX"
else
    echo "⚠️  未找到默认nginx配置文件"
fi

echo ""
echo "📝 第2步: 创建Discord Bot nginx配置..."

# 创建nginx配置文件
cat > /etc/nginx/sites-available/tdindicator.top << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name www.tdindicator.top tdindicator.top;
    
    # 重定向HTTP到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.tdindicator.top tdindicator.top;

    # SSL证书配置（使用你现有的证书路径）
    ssl_certificate /etc/letsencrypt/live/www.tdindicator.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.tdindicator.top/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 现有网站根目录（保持你当前的网站）
    root /var/www/html;
    index index.html index.htm index.php;

    # 现有网站默认location
    location / {
        try_files $uri $uri/ =404;
        # 如果你有PHP，取消注释下面的行
        # location ~ \.php$ {
        #     include snippets/fastcgi-php.conf;
        #     fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        # }
    }

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
        
        # 允许大的请求体（用于复杂的TradingView数据）
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

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

echo "✅ nginx配置文件已创建: /etc/nginx/sites-available/tdindicator.top"

echo ""
echo "⚡ 第3步: 激活配置..."
ln -sf /etc/nginx/sites-available/tdindicator.top /etc/nginx/sites-enabled/
echo "✅ 配置已激活"

echo ""
echo "🧪 第4步: 测试nginx配置..."
if nginx -t; then
    echo "✅ nginx配置测试通过"
else
    echo "❌ nginx配置测试失败，请检查配置文件"
    echo "   你可以检查日志: sudo tail -f /var/log/nginx/error.log"
    exit 1
fi

echo ""
echo "🔄 第5步: 重新加载nginx..."
if systemctl reload nginx; then
    echo "✅ nginx已重新加载"
else
    echo "❌ nginx重新加载失败"
    echo "   请检查nginx状态: sudo systemctl status nginx"
    exit 1
fi

echo ""
echo "📊 第6步: 检查nginx状态..."
systemctl status nginx --no-pager

echo ""
echo "🎉 部署完成！"
echo ""
echo "🔗 你的Discord Bot API现在可以通过以下地址访问："
echo "   • 主站点（保持不变）:      https://www.tdindicator.top/"
echo "   • TradingView Webhook:     https://www.tdindicator.top/webhook/tradingview"
echo "   • Bot健康检查:             https://www.tdindicator.top/bot-status"
echo "   • Bot API文档:             https://www.tdindicator.top/bot-api"
echo "   • 发送Discord消息:         https://www.tdindicator.top/api/send-message"
echo "   • 发送私信:                https://www.tdindicator.top/api/send-dm"
echo "   • 发送图表:                https://www.tdindicator.top/api/send-chart"
echo ""
echo "🧪 测试命令："
echo "   curl https://www.tdindicator.top/bot-status"
echo ""
echo "⚠️  重要提醒："
echo "   1. 确保你的Discord Bot在端口5000上运行"
echo "   2. 如果遇到问题，检查错误日志: sudo tail -f /var/log/nginx/error.log"
echo "   3. 这个配置保持你现有网站功能不变，只是添加了Bot的API端点"
echo ""
echo "🚀 现在你可以启动Discord Bot了！"