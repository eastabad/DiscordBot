#!/usr/bin/env python3
"""
测试升级后的图表机器人功能
"""

from chart_service import ChartService
from config import Config
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

async def test_chart_service():
    """测试图表服务"""
    print("=== 测试图表服务 ===")
    
    config = Config()
    chart_service = ChartService(config)
    
    # 测试命令解析
    test_commands = [
        "@bot AAPL,1h",
        "<@1404173510074564709> NASDAQ:GOOG,15m", 
        "@TDbot TSLA,1d",
        "MSFT,4h invalid",
        "@bot 无效命令",
        "@bot SPY,30m"
    ]
    
    print("\n--- 测试命令解析 ---")
    for cmd in test_commands:
        result = chart_service.parse_command(cmd)
        print(f"命令: '{cmd}' -> {result}")
    
    # 测试时间框架标准化
    print("\n--- 测试时间框架标准化 ---")
    timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"]
    for tf in timeframes:
        normalized = chart_service.normalize_timeframe(tf)
        print(f"{tf} -> {normalized}")
    
    # 测试配置
    print("\n--- 测试配置 ---")
    print(f"Chart API Key: {'已设置' if config.chart_img_api_key else '未设置'}")
    print(f"Layout ID: {config.layout_id}")
    print(f"Monitor Channel: {config.monitor_channel_id}")
    print(f"TradingView Session: {'已设置' if config.tradingview_session_id else '未设置'}")
    
    # 如果配置完整，测试API调用
    if config.chart_img_api_key and config.layout_id:
        print("\n--- 测试API调用 ---")
        try:
            chart_data = await chart_service.get_chart("AAPL", "1h")
            if chart_data:
                print(f"✅ API调用成功，获得图表数据: {len(chart_data)} bytes")
            else:
                print("❌ API调用失败，未获得图表数据")
        except Exception as e:
            print(f"❌ API调用异常: {e}")
    else:
        print("\n⚠️  跳过API测试 - 配置不完整")

def test_parse_commands():
    """测试命令解析（同步版本）"""
    config = Config()
    chart_service = ChartService(config)
    
    test_cases = [
        ("@bot AAPL,1h", ("AAPL", "1h")),
        ("<@1404173510074564709> NASDAQ:GOOG,15m", ("NASDAQ:GOOG", "15m")),
        ("@bot SPY, 1d", ("SPY", "1d")),
        ("@bot MSFT 4h", ("MSFT", "4h")),
        ("@bot invalid", None),
        ("no mention TSLA,1h", None),
    ]
    
    print("=== 命令解析测试 ===")
    for input_text, expected in test_cases:
        result = chart_service.parse_command(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' -> {result} (期望: {expected})")

if __name__ == "__main__":
    # 运行同步测试
    test_parse_commands()
    
    # 运行异步测试
    asyncio.run(test_chart_service())