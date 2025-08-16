#!/usr/bin/env python3
"""
添加测试数据 - 创建同一个股票和时间级别的signal和trade数据匹配
"""
import requests
import json
import time

def add_matching_test_data():
    """添加匹配的测试数据"""
    
    base_url = "http://localhost:5000"
    
    # 测试用例1: TSLA 15m - 添加signal数据匹配现有trade数据
    tsla_15m_signal = {
        "symbol": "TSLA",
        "CVDsignal": "cvdAboveMA",
        "choppiness": "32.5",
        "adxValue": "55.8",
        "BBPsignal": "bullpower",
        "RSIHAsignal": "BullishHA",
        "SQZsignal": "squeeze",
        "choppingrange_signal": "trending",
        "rsi_state_trend": "Bullish",
        "center_trend": "Strong Bullish",
        "adaptive_timeframe_1": "15",
        "adaptive_timeframe_2": "60",
        "MAtrend": "1",
        "MAtrend_timeframe1": "1",
        "MAtrend_timeframe2": "1",
        "MOMOsignal": "bullishmomo",
        "Middle_smooth_trend": "Bullish +",
        "TrendTracersignal": "1",
        "TrendTracerHTF": "1",
        "pmaText": "PMA Strong Bullish",
        "trend_change_volatility_stop": "310.25",
        "AIbandsignal": "blue uptrend",
        "HTFwave_signal": "Bullish",
        "wavemarket_state": "Long Strong",
        "ewotrend_state": "Strong Bullish"
    }
    
    # 测试用例2: AAPL 1h - 添加trade数据匹配现有signal数据
    aapl_1h_trade = {
        "ticker": "AAPL",
        "action": "sell",
        "quantity": 150,
        "takeProfit": {"limitPrice": 175.80},
        "stopLoss": {"stopPrice": 190.15},
        "extras": {
            "indicator": "WaveMatrix Bear Signal",
            "timeframe": "1h",
            "oscrating": 85,
            "trendrating": 70,
            "risk": 3
        }
    }
    
    # 测试用例3: NVDA 4h - 添加signal数据
    nvda_4h_signal = {
        "symbol": "NVDA",
        "CVDsignal": "cvdBelowMA",
        "choppiness": "45.2",
        "adxValue": "42.1",
        "BBPsignal": "bearpower", 
        "RSIHAsignal": "BearishHA",
        "SQZsignal": "no_squeeze",
        "choppingrange_signal": "chopping",
        "rsi_state_trend": "Bearish",
        "center_trend": "Bearish",
        "adaptive_timeframe_1": "240",
        "adaptive_timeframe_2": "1440",
        "MAtrend": "-1",
        "MAtrend_timeframe1": "-1",
        "MAtrend_timeframe2": "0",
        "MOMOsignal": "bearishmomo",
        "Middle_smooth_trend": "Bearish",
        "TrendTracersignal": "-1",
        "TrendTracerHTF": "-1",
        "pmaText": "PMA Bearish",
        "trend_change_volatility_stop": "125.75",
        "AIbandsignal": "red downtrend",
        "HTFwave_signal": "Bearish",
        "wavemarket_state": "Short Moderate",
        "ewotrend_state": "Bearish"
    }
    
    # 测试用例4: GOOG 1h - 添加signal和trade数据
    goog_1h_signal = {
        "symbol": "GOOG",
        "CVDsignal": "cvdAboveMA",
        "choppiness": "38.9",
        "adxValue": "48.5",
        "BBPsignal": "bullpower",
        "RSIHAsignal": "BullishHA", 
        "SQZsignal": "squeeze",
        "choppingrange_signal": "trending",
        "rsi_state_trend": "Bullish",
        "center_trend": "Bullish",
        "adaptive_timeframe_1": "60",
        "adaptive_timeframe_2": "240",
        "MAtrend": "1",
        "MAtrend_timeframe1": "1",
        "MAtrend_timeframe2": "1",
        "MOMOsignal": "bullishmomo",
        "Middle_smooth_trend": "Bullish",
        "TrendTracersignal": "1",
        "TrendTracerHTF": "1",
        "pmaText": "PMA Bullish",
        "trend_change_volatility_stop": "165.40",
        "AIbandsignal": "blue uptrend",
        "HTFwave_signal": "Bullish",
        "wavemarket_state": "Long Moderate",
        "ewotrend_state": "Bullish"
    }
    
    goog_1h_trade = {
        "ticker": "GOOG",
        "action": "buy",
        "quantity": 75,
        "takeProfit": {"limitPrice": 175.50},
        "stopLoss": {"stopPrice": 158.80},
        "extras": {
            "indicator": "EMA Crossover Bullish",
            "timeframe": "1h",
            "oscrating": 78,
            "trendrating": 82,
            "risk": 2
        }
    }
    
    # 发送数据
    test_data = [
        ("TSLA 15m Signal", tsla_15m_signal),
        ("AAPL 1h Trade", aapl_1h_trade), 
        ("NVDA 4h Signal", nvda_4h_signal),
        ("GOOG 1h Signal", goog_1h_signal),
        ("GOOG 1h Trade", goog_1h_trade)
    ]
    
    print("🚀 开始添加匹配的测试数据...")
    print("=" * 50)
    
    for name, data in test_data:
        try:
            response = requests.post(
                f"{base_url}/webhook/tradingview",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {name}: {result.get('message', 'Success')}")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
            time.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 数据添加完成！现在可以测试完整的报告生成功能")

if __name__ == "__main__":
    add_matching_test_data()