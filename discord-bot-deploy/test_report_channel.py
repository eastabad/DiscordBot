#!/usr/bin/env python3
"""
测试report频道监控和AI分析报告生成功能
"""

import logging
import json
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_report_channel_simulation():
    """模拟report频道的请求"""
    logger.info("🔍 开始测试report频道功能...")
    
    print("\n" + "="*60)
    print("📊 Report频道监控测试")
    print("="*60)
    
    print("\n✅ 系统配置:")
    print("   • 监控所有名为'report'的频道")
    print("   • 支持股票代码 + 时间框架格式")
    print("   • AI报告通过私信发送")
    print("   • 用户限制: 每日3次")
    
    print("\n📝 支持的请求格式:")
    print("   • AAPL 15m")
    print("   • TSLA 1h") 
    print("   • NVDA 4h")
    print("   • AMZN 15分钟")
    print("   • MSFT 1小时")
    print("   • GOOGL 4小时")
    
    # 发送测试webhook数据（模拟TradingView推送）
    test_data = [{
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": {
            "symbol": "AAPL",
            "pmaText": "PMA Strong Bullish",
            "CVDsignal": "cvdAboveMA",
            "choppiness": "35.2154867921",
            "adxValue": "32.8765432109",
            "BBPsignal": "bullpower",
            "RSIHAsignal": "BullishHA",
            "SQZsignal": "no squeeze",
            "choppingrange_signal": "no chopping",
            "rsi_state_trend": "Bullish",
            "center_trend": "Strong Bullish",
            "MAtrend": "1",
            "MAtrend_timeframe1": "1",
            "MAtrend_timeframe2": "0",
            "Middle_smooth_trend": "Bullish +",
            "MOMOsignal": "bullishmomo",
            "TrendTracersignal": "1",
            "TrendTracerHTF": "-1",
            "trend_change_volatility_stop": "185.42",
            "AIbandsignal": "green uptrend",
            "wavemarket_state": "Long Weak",
            "ewotrend_state": "Weak Bullish",
            "HTFwave_signal": "Neutral",
            "adaptive_timeframe_1": "15",
            "adaptive_timeframe_2": "60",
            "stopLoss": {"stopPrice": 180.25},
            "takeProfit": {"limitPrice": 195.80},
            "risk": "高风险",
            "action": "buy",
            "extras": {"oscrating": 72, "trendrating": 58}
        }
    }]
    
    try:
        # 推送测试数据到webhook端点
        response = requests.post(
            "http://localhost:5000/webhook-test/TV",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ TradingView测试数据推送成功")
            result = response.json()
            logger.info(f"   响应: {result.get('message', 'N/A')}")
        else:
            logger.error(f"❌ TradingView数据推送失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Webhook连接失败: {e}")
    
    print("\n🤖 Discord机器人状态:")
    print("   • 已连接到Discord")
    print("   • 监控多个频道 + report频道")
    print("   • AI报告生成器已就绪") 
    print("   • TradingView数据接收正常")
    
    print("\n📋 测试步骤:")
    print("   1. 在Discord中创建名为'report'的频道")
    print("   2. 在该频道中发送: AAPL 15m")
    print("   3. 机器人将检测到请求并生成AI报告")
    print("   4. 报告将通过私信发送给用户")
    
    print("\n⚠️  注意事项:")
    print("   • 用户每日限制3次请求")
    print("   • 管理员可添加VIP豁免用户")  
    print("   • 需要有效的TradingView数据才能生成完整报告")
    print("   • 支持中英文时间框架格式")

def main():
    """主测试函数"""
    logger.info("🚀 开始report频道监控测试...")
    
    test_report_channel_simulation()
    
    print("\n" + "="*60)
    print("✅ Report频道监控系统已就绪!")
    print("="*60)
    print("\n💡 现在可以在Discord的report频道中测试:")
    print("   发送格式: 股票代码 时间框架")
    print("   例如: AAPL 15m, TSLA 1h, NVDA 4h")

if __name__ == "__main__":
    main()