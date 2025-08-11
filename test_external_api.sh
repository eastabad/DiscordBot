#!/bin/bash
# 测试外部API访问脚本

echo "=== 测试Discord Bot API ==="
echo "URL: https://workspace.eastabad.replit.dev"
echo ""

echo "1. 测试健康检查："
curl -s https://workspace.eastabad.replit.dev/api/health | python3 -m json.tool

echo ""
echo "2. 测试发送图表消息："
curl -X POST https://workspace.eastabad.replit.dev/api/send-chart \
  -H "Content-Type: application/json" \
  -d '[{
    "authorId": 1145170623354638418,
    "symbol": "AAPL", 
    "timeframe": "1h",
    "discordPayload": {
      "content": "📊 n8n测试：AAPL 1小时图表"
    }
  }]' | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="