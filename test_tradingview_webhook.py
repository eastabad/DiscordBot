#!/usr/bin/env python3
"""
TradingView Webhook 测试工具
测试三种数据类型：signal, trade, close
"""
import requests
import json
import time
from datetime import datetime

class TradingViewWebhookTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.webhook_endpoint = f"{base_url}/webhook/tradingview"
        
    def test_signal_webhook(self, symbol="AAPL", timeframe="1h"):
        """测试信号数据webhook"""
        signal_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "CVDsignal": "cvdAboveMA",
            "choppiness": "35.2",
            "adxValue": "52.3",
            "BBPsignal": "bullpower",
            "RSIHAsignal": "BullishHA",
            "SQZsignal": "squeeze",
            "choppingrange_signal": "trending",
            "rsi_state_trend": "Bullish",
            "center_trend": "Strong Bullish",
            "adaptive_timeframe_1": timeframe.replace("h", "").replace("m", ""),
            "adaptive_timeframe_2": str(int(timeframe.replace("h", "").replace("m", "")) * 4),
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
        
        return self._send_webhook("Signal", signal_data)
    
    def test_trade_webhook(self, symbol="AAPL", timeframe="1h", action="buy"):
        """测试交易数据webhook（开仓）"""
        trade_data = {
            "ticker": symbol,
            "action": action,
            "quantity": 100,
            "takeProfit": {"limitPrice": 195.50},
            "stopLoss": {"stopPrice": 180.25},
            "extras": {
                "indicator": "EMA Golden Cross",
                "timeframe": timeframe,
                "oscrating": 75,
                "trendrating": 85,
                "risk": 2
            }
        }
        
        return self._send_webhook("Trade", trade_data)
    
    def test_close_webhook(self, symbol="AAPL", timeframe="1h", action="sell"):
        """测试平仓数据webhook"""
        close_data = {
            "ticker": symbol,
            "action": action,
            "sentiment": "flat",  # 关键字段，表示平仓
            "extras": {
                "indicator": f"TrailingStop Exit {'Long' if action == 'sell' else 'Short'}",
                "timeframe": timeframe
            }
        }
        
        return self._send_webhook("Close", close_data)
    
    def _send_webhook(self, data_type, data):
        """发送webhook数据"""
        try:
            print(f"\n📤 发送 {data_type} 数据...")
            print(f"目标: {self.webhook_endpoint}")
            print(f"数据: {json.dumps(data, indent=2)}")
            
            response = requests.post(
                self.webhook_endpoint,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {data_type} 数据发送成功: {result.get('message', 'Success')}")
                return True
            else:
                print(f"❌ {data_type} 数据发送失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ {data_type} 数据发送异常: {e}")
            return False
    
    def test_complete_workflow(self, symbol="MSFT", timeframe="1h"):
        """测试完整的交易流程：信号 -> 开仓 -> 平仓"""
        print(f"\n🧪 开始测试完整交易流程: {symbol} {timeframe}")
        print("=" * 60)
        
        results = []
        
        # 1. 发送信号数据
        print("\n1️⃣ 发送技术指标信号数据")
        signal_success = self.test_signal_webhook(symbol, timeframe)
        results.append(("Signal", signal_success))
        time.sleep(1)
        
        # 2. 发送开仓交易数据
        print("\n2️⃣ 发送开仓交易数据")
        trade_success = self.test_trade_webhook(symbol, timeframe, "buy")
        results.append(("Trade", trade_success))
        time.sleep(1)
        
        # 3. 发送平仓数据
        print("\n3️⃣ 发送平仓数据")
        close_success = self.test_close_webhook(symbol, timeframe, "sell")
        results.append(("Close", close_success))
        
        # 结果汇总
        print(f"\n📊 {symbol} {timeframe} 测试结果:")
        print("-" * 40)
        for data_type, success in results:
            status = "✅" if success else "❌"
            print(f"  {status} {data_type}: {'成功' if success else '失败'}")
        
        all_success = all(result[1] for result in results)
        print(f"\n🎯 整体结果: {'全部成功' if all_success else '存在失败'}")
        
        return all_success
    
    def test_multiple_symbols(self):
        """测试多个股票的webhook数据"""
        symbols = [
            ("TSLA", "15m"),
            ("NVDA", "1h"), 
            ("AMZN", "4h"),
            ("GOOGL", "1h")
        ]
        
        print("\n🚀 批量测试多个股票的webhook数据")
        print("=" * 60)
        
        overall_results = []
        
        for symbol, timeframe in symbols:
            print(f"\n📈 测试 {symbol} {timeframe}")
            success = self.test_complete_workflow(symbol, timeframe)
            overall_results.append((f"{symbol} {timeframe}", success))
            time.sleep(2)  # 避免请求过快
        
        print(f"\n🏆 批量测试总结:")
        print("=" * 40)
        for test_case, success in overall_results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_case}")
        
        total_success = sum(1 for _, success in overall_results if success)
        total_tests = len(overall_results)
        print(f"\n📊 成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        
        return overall_results

def main():
    """主测试函数"""
    print("🧪 TradingView Webhook 测试工具")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = TradingViewWebhookTester()
    
    # 检查API服务器状态
    try:
        health_response = requests.get(f"{tester.base_url}/api/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API服务器运行正常")
        else:
            print("⚠️ API服务器状态异常")
    except:
        print("❌ 无法连接到API服务器，请确保服务已启动")
        return
    
    # 选择测试模式
    print("\n🎯 选择测试模式:")
    print("1. 单个股票完整流程测试")
    print("2. 批量多股票测试")
    print("3. 自定义单项测试")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        symbol = input("输入股票代码 (默认AAPL): ").strip() or "AAPL"
        timeframe = input("输入时间框架 (默认1h): ").strip() or "1h"
        tester.test_complete_workflow(symbol, timeframe)
        
    elif choice == "2":
        tester.test_multiple_symbols()
        
    elif choice == "3":
        print("\n选择测试类型:")
        print("1. Signal数据")
        print("2. Trade数据") 
        print("3. Close数据")
        
        test_type = input("请选择 (1-3): ").strip()
        symbol = input("输入股票代码 (默认AAPL): ").strip() or "AAPL"
        timeframe = input("输入时间框架 (默认1h): ").strip() or "1h"
        
        if test_type == "1":
            tester.test_signal_webhook(symbol, timeframe)
        elif test_type == "2":
            action = input("交易方向 (buy/sell, 默认buy): ").strip() or "buy"
            tester.test_trade_webhook(symbol, timeframe, action)
        elif test_type == "3":
            action = input("平仓方向 (buy/sell, 默认sell): ").strip() or "sell"
            tester.test_close_webhook(symbol, timeframe, action)
    
    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    main()