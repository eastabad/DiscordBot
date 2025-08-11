#!/bin/bash

# 测试Shared Layout API调用
echo "测试chart-img Shared Layout API..."

API_KEY="$CHART_IMG_API_KEY"
LAYOUT_ID="$LAYOUT_ID" 

if [ -z "$API_KEY" ] || [ -z "$LAYOUT_ID" ]; then
    echo "❌ 缺少API密钥或Layout ID"
    exit 1
fi

echo "🔑 API Key: ${API_KEY:0:10}..."
echo "📊 Layout ID: $LAYOUT_ID"

# 测试API调用
curl -X POST https://api.chart-img.com/v2/tradingview/shared-layout \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "layout": "'$LAYOUT_ID'",
    "symbol": "NASDAQ:AAPL",
    "interval": "1h",
    "width": 1920,
    "height": 1080,
    "format": "png"
  }' \
  --output test_chart.png \
  --silent \
  --write-out "HTTP Status: %{http_code}\nSize: %{size_download} bytes\n"

if [ -f "test_chart.png" ] && [ -s "test_chart.png" ]; then
    echo "✅ 图表生成成功: test_chart.png ($(du -h test_chart.png | cut -f1))"
    ls -la test_chart.png
else
    echo "❌ 图表生成失败"
    if [ -f "test_chart.png" ]; then
        echo "文件内容:"
        cat test_chart.png
        rm test_chart.png
    fi
fi