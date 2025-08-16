#!/usr/bin/env python3
"""
测试TradingView webhook API端点
验证三种数据类型通过HTTP POST的处理
"""

import requests
import json
import time

# API端点配置
BASE_URL = "http://localhost:5000"
WEBHOOK_ENDPOINT = f"{BASE_URL}/webhook/tradingview"

def test_signal_webhook():
    """测试信号数据webhook"""
    print("📡 测试信号数据webhook...")
    
    signal_payload = {
        "symbol": "AAPL",
        "CVDsignal": "cvdAboveMA",
        "choppiness": "25.6789",
        "adxValue": "45.123",
        "BBPsignal": "bearpower",
        "RSIHAsignal": "BullishHA",
        "SQZsignal": "squeeze",
        "choppingrange_signal": "chopping",
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
        "trend_change_volatility_stop": "185.75",
        "AIbandsignal": "blue uptrend",
        "HTFwave_signal": "Bullish",
        "wavemarket_state": "Long Strong",
        "ewotrend_state": "Strong Bullish"
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=signal_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 信号webhook成功: {result['message']}")
            print(f"   数据类型: {result['data_type']}")
            print(f"   股票: {result['symbol']}, 时间框架: {result['timeframe']}")
            return True
        else:
            print(f"❌ 信号webhook失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 信号webhook异常: {e}")
        return False

def test_trade_webhook():
    """测试交易数据webhook"""
    print("\n📡 测试交易数据webhook...")
    
    trade_payload = {
        "ticker": "AAPL",
        "action": "buy",
        "quantity": 100,
        "takeProfit": {
            "limitPrice": 195.50
        },
        "stopLoss": {
            "stopPrice": 180.25
        },
        "extras": {
            "indicator": "RSI Oversold Signal",
            "timeframe": "1h",
            "oscrating": 75,
            "trendrating": 85,
            "risk": 2
        }
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=trade_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 交易webhook成功: {result['message']}")
            print(f"   数据类型: {result['data_type']}")
            print(f"   股票: {result['symbol']}, 时间框架: {result['timeframe']}")
            return True
        else:
            print(f"❌ 交易webhook失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 交易webhook异常: {e}")
        return False

def test_close_webhook():
    """测试平仓数据webhook"""
    print("\n📡 测试平仓数据webhook...")
    
    close_payload = {
        "ticker": "NVDA",
        "action": "buy",
        "sentiment": "flat",
        "extras": {
            "indicator": "TrailingStop Exit Short",
            "timeframe": "4h"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_ENDPOINT, json=close_payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 平仓webhook成功: {result['message']}")
            print(f"   数据类型: {result['data_type']}")
            print(f"   股票: {result['symbol']}, 时间框架: {result['timeframe']}")
            print(f"   平仓类型: flat + {close_payload['action']} = 平仓空头")
            return True
        else:
            print(f"❌ 平仓webhook失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 平仓webhook异常: {e}")
        return False

def test_health_check():
    """测试健康检查端点"""
    print("\n🔍 测试健康检查端点...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 健康检查通过: {result['status']}")
            print(f"   API服务器: {result['api_server']}")
            print(f"   Discord机器人: {result['bot']['status']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试TradingView webhook API...")
    print("=" * 60)
    
    # 等待API服务器启动
    print("⏳ 等待API服务器启动...")
    time.sleep(2)
    
    # 测试健康检查
    health_ok = test_health_check()
    
    if not health_ok:
        print("❌ API服务器未就绪，停止测试")
        return False
    
    # 测试三种webhook数据类型
    signal_ok = test_signal_webhook()
    trade_ok = test_trade_webhook()
    close_ok = test_close_webhook()
    
    print("\n" + "=" * 60)
    print("📋 API测试结果汇总:")
    print(f"   健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"   信号webhook: {'✅ 成功' if signal_ok else '❌ 失败'}")
    print(f"   交易webhook: {'✅ 成功' if trade_ok else '❌ 失败'}")
    print(f"   平仓webhook: {'✅ 成功' if close_ok else '❌ 失败'}")
    
    all_passed = all([health_ok, signal_ok, trade_ok, close_ok])
    
    if all_passed:
        print("\n🎉 所有API测试通过！TradingView webhook系统工作正常！")
    else:
        print("\n⚠️  部分API测试失败，请检查服务器状态")
    
    return all_passed

if __name__ == "__main__":
    main()