#!/usr/bin/env python3
"""测试无效时间框架处理"""

import asyncio
from config import Config
from chart_service import ChartService

async def test_invalid_timeframe():
    """测试无效时间框架"""
    print("=== 测试无效时间框架处理 ===")
    
    config = Config()
    chart_service = ChartService(config)
    
    # 测试解析无效时间框架
    test_cases = [
        "AMZN,15h",  # 15h 不是有效时间框架 
        "AAPL,3h",   # 3h 不是有效时间框架
        "SPY,25m",   # 25m 不是有效时间框架
        "TSLA,2d",   # 2d 不是有效时间框架
        "MSFT,1y",   # 1y 不是有效时间框架
    ]
    
    for test in test_cases:
        result = chart_service.parse_command(test)
        print(f"'{test}' -> {result}")
        
        if result:
            symbol, timeframe = result
            chart_data = await chart_service.get_chart(symbol, timeframe)
            if chart_data:
                print(f"  ✅ 获取图表成功: {len(chart_data)} bytes")
            else:
                print(f"  ❌ 获取图表失败: 无效时间框架")
        else:
            print(f"  ❌ 命令解析失败")
    
    print("\n=== 测试有效时间框架 ===")
    valid_tests = [
        "AMZN,1h",   # 有效
        "AAPL,4h",   # 有效
        "SPY,15m",   # 有效
        "TSLA,1d",   # 有效
    ]
    
    for test in valid_tests:
        result = chart_service.parse_command(test)
        if result:
            symbol, timeframe = result
            print(f"'{test}' -> 解析成功: {symbol}, {timeframe}")
        else:
            print(f"'{test}' -> 解析失败")

if __name__ == "__main__":
    asyncio.run(test_invalid_timeframe())