#!/bin/bash

echo "=== Discord Bot Nginx反向代理部署脚本 ==="

# 1. 备份现有nginx配置
echo "📁 备份现有nginx配置..."
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# 2. 复制新配置
echo "📝 部署新的nginx配置..."
sudo cp nginx_simple_config.conf /etc/nginx/sites-available/tdindicator.top

# 3. 激活配置
echo "⚡ 激活配置..."
sudo ln -sf /etc/nginx/sites-available/tdindicator.top /etc/nginx/sites-enabled/

# 4. 测试nginx配置
echo "🧪 测试nginx配置..."
if sudo nginx -t; then
    echo "✅ nginx配置测试通过"
else
    echo "❌ nginx配置测试失败，请检查配置文件"
    exit 1
fi

# 5. 重新加载nginx
echo "🔄 重新加载nginx..."
sudo systemctl reload nginx

# 6. 检查nginx状态
echo "📊 检查nginx状态..."
sudo systemctl status nginx --no-pager

echo ""
echo "🎉 部署完成！"
echo ""
echo "📡 你的TradingView Webhook地址现在是："
echo "   https://www.tdindicator.top/webhook/tradingview"
echo ""
echo "🔗 其他可用端点："
echo "   • 健康检查: https://www.tdindicator.top/bot-status"
echo "   • API文档:  https://www.tdindicator.top/bot-api"
echo "   • 发送消息: https://www.tdindicator.top/api/send-message"
echo "   • 发送私信: https://www.tdindicator.top/api/send-dm"
echo "   • 发送图表: https://www.tdindicator.top/api/send-chart"
echo ""
echo "🧪 测试命令："
echo "   curl https://www.tdindicator.top/bot-status"
echo "   curl -X POST https://www.tdindicator.top/webhook/tradingview \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"symbol\":\"AAPL\",\"action\":\"buy\",\"price\":150.00}'"