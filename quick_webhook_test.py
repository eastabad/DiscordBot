#!/usr/bin/env python3
"""
快速TradingView Webhook测试
"""
import requests
import json

def quick_test():
    """快速测试三种类型的webhook数据"""
    
    base_url = "http://localhost:5000"
    webhook_url = f"{base_url}/webhook/tradingview"
    
    # 1. 测试Signal数据
    print("🧪 测试Signal数据...")
    signal_data = {
        "symbol": "AAPL",
        "timeframe": "1h",
        "CVDsignal": "cvdAboveMA",
        "choppiness": "42.1",
        "adxValue": "58.3",
        "BBPsignal": "bullpower",
        "RSIHAsignal": "BullishHA",
        "SQZsignal": "squeeze",
        "choppingrange_signal": "trending",
        "rsi_state_trend": "Bullish",
        "center_trend": "Strong Bullish",
        "adaptive_timeframe_1": "60",
        "adaptive_timeframe_2": "240",
        "MAtrend": "1",
        "MAtrend_timeframe1": "1", 
        "MAtrend_timeframe2": "1",
        "MOMOsignal": "bullishmomo",
        "Middle_smooth_trend": "Bullish +",
        "TrendTracersignal": "1",
        "TrendTracerHTF": "1",
        "pmaText": "PMA Strong Bullish",
        "trend_change_volatility_stop": "188.50",
        "AIbandsignal": "blue uptrend",
        "HTFwave_signal": "Bullish",
        "wavemarket_state": "Long Strong",
        "ewotrend_state": "Strong Bullish"
    }
    
    try:
        response = requests.post(webhook_url, json=signal_data)
        print(f"Signal响应: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Signal错误: {e}")
    
    # 2. 测试Trade数据（开仓）
    print("\n🧪 测试Trade数据（开仓）...")
    trade_data = {
        "ticker": "AAPL",
        "action": "buy",
        "quantity": 100,
        "takeProfit": {"limitPrice": 195.00},
        "stopLoss": {"stopPrice": 182.50},
        "extras": {
            "indicator": "EMA Crossover Bull",
            "timeframe": "1h",
            "oscrating": 80,
            "trendrating": 85,
            "risk": 2
        }
    }
    
    try:
        response = requests.post(webhook_url, json=trade_data)
        print(f"Trade响应: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Trade错误: {e}")
    
    # 3. 测试Close数据（平仓）
    print("\n🧪 测试Close数据（平仓）...")
    close_data = {
        "ticker": "AAPL",
        "action": "sell",
        "sentiment": "flat",  # 关键：表示平仓
        "extras": {
            "indicator": "TrailingStop Exit Long",
            "timeframe": "1h"
        }
    }
    
    try:
        response = requests.post(webhook_url, json=close_data)
        print(f"Close响应: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Close错误: {e}")
    
    print("\n✅ 快速测试完成!")
    print("现在可以在Discord报告频道测试: AAPL 1h")

if __name__ == "__main__":
    quick_test()