#!/usr/bin/env python3
"""
测试股票趋势预测服务
"""

import asyncio
import sys
from config import Config
from prediction_service import StockPredictionService

async def test_prediction_service():
    """测试预测服务"""
    print("=== 测试股票趋势预测服务 ===")
    
    config = Config()
    prediction_service = StockPredictionService(config)
    
    # 测试股票符号列表
    test_symbols = ["AAPL", "TSLA", "GOOGL", "MSFT", "NVDA", "SPY"]
    
    for symbol in test_symbols:
        print(f"\n--- 测试预测: {symbol} ---")
        
        try:
            prediction = await prediction_service.get_prediction(symbol)
            
            if "error" in prediction:
                print(f"❌ {symbol} 预测失败: {prediction['message']}")
            else:
                print(f"✅ {symbol} 预测成功")
                
                # 显示预测详情
                trend = prediction["trend_analysis"]
                print(f"  趋势: {trend['trend']} (信心度: {trend['confidence']:.1f}%)")
                print(f"  价格变化: {trend['price_change']:+.2f}%")
                
                if prediction["technical_indicators"]["rsi"]:
                    rsi = prediction["technical_indicators"]["rsi"]
                    print(f"  RSI: {rsi:.1f} - {prediction['technical_indicators']['rsi_status']}")
                
                signals = prediction["trading_signals"]
                print(f"  整体情绪: {signals['overall_sentiment']}")
                print(f"  风险等级: {signals['risk_level']}")
                
                if signals["signals"]:
                    print("  交易信号:")
                    for signal in signals["signals"]:
                        print(f"    - {signal['type']}: {signal['reason']}")
                
                print(f"  建议: {prediction['recommendation']}")
                
        except Exception as e:
            print(f"❌ 测试 {symbol} 时出错: {e}")
    
    print("\n--- 测试消息格式化 ---")
    try:
        test_prediction = await prediction_service.get_prediction("AAPL")
        formatted_message = prediction_service.format_prediction_message(test_prediction)
        print("Discord消息格式预览:")
        print("-" * 50)
        print(formatted_message)
        print("-" * 50)
    except Exception as e:
        print(f"消息格式化测试失败: {e}")
    
    print("\n=== 预测服务测试完成 ===")

def test_command_detection():
    """测试预测命令检测"""
    print("\n=== 测试预测命令检测 ===")
    
    # 模拟机器人类来测试命令检测
    class MockBot:
        def has_prediction_command(self, content: str) -> bool:
            import re
            prediction_keywords = ['预测', 'predict', '趋势', 'trend', '分析', 'analysis', '预测分析', '走势预测']
            content_lower = content.lower()
            has_keyword = any(keyword in content_lower for keyword in prediction_keywords)
            has_symbol = bool(re.search(r'[A-Z]{2,}', content, re.IGNORECASE))
            return has_keyword and has_symbol
    
    bot = MockBot()
    
    # 测试命令
    test_commands = [
        "@bot 预测 AAPL 趋势",
        "<@1234567890> predict TSLA trend", 
        "分析 GOOGL 走势",
        "MSFT 趋势预测",
        "@bot 预测分析 NVDA",
        "predict SPY analysis",
        "今天天气怎么样",  # 应该不匹配
        "预测今天股市",      # 应该不匹配（无具体股票符号）
        "AAPL,1h",          # 应该不匹配（图表请求）
        "@bot 预测",         # 应该不匹配（无股票符号）
    ]
    
    print("命令检测测试:")
    for cmd in test_commands:
        result = bot.has_prediction_command(cmd)
        status = "✅ 匹配" if result else "❌ 不匹配"
        print(f"  '{cmd}' -> {status}")

if __name__ == "__main__":
    try:
        # 测试命令检测
        test_command_detection()
        
        # 测试预测服务
        asyncio.run(test_prediction_service())
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()