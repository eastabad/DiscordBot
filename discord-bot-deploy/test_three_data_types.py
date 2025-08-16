#!/usr/bin/env python3
"""
测试三种TradingView数据类型的存储和解析
验证signal、trade、close数据类型的正确处理
"""

import json
from datetime import datetime
from tradingview_handler import TradingViewHandler
from models import get_db_session, TradingViewData

def test_signal_data():
    """测试信号数据 (每15分钟或1小时发送的周期性数据)"""
    print("🔍 测试信号数据...")
    
    signal_data = {
        "symbol": "TSLA",
        "CVDsignal": "cvdBelowMA",
        "choppiness": "46.4125643135",
        "adxValue": "35.341643694",
        "BBPsignal": "bullpower",
        "RSIHAsignal": "BearishHA",
        "SQZsignal": "no squeeze",
        "choppingrange_signal": "no chopping",
        "rsi_state_trend": "Bearish",
        "center_trend": "Strong Bearish",
        "adaptive_timeframe_1": "60",
        "adaptive_timeframe_2": "240",
        "MAtrend": "-1",
        "MAtrend_timeframe1": "-1",
        "MAtrend_timeframe2": "1",
        "MOMOsignal": "bearishmomo",
        "Middle_smooth_trend": "Bearish +",
        "TrendTracersignal": "-1",
        "TrendTracerHTF": "-1",
        "pmaText": "PMA Bearish",
        "trend_change_volatility_stop": "336.46",
        "AIbandsignal": "red downtrend",
        "HTFwave_signal": "Bearish",
        "wavemarket_state": "Short Strong",
        "ewotrend_state": "Strong Bearish"
    }
    
    handler = TradingViewHandler()
    success = handler.store_enhanced_data(signal_data)
    
    if success:
        print("✅ 信号数据存储成功")
        print(f"   数据类型: {handler._detect_data_type(signal_data)}")
        symbol, timeframe = handler._extract_basic_info(signal_data, 'signal')
        print(f"   股票代码: {symbol}, 时间框架: {timeframe}")
    else:
        print("❌ 信号数据存储失败")
    
    return success

def test_trade_data():
    """测试交易数据 (有交易触发时发送，包含止盈止损)"""
    print("\n🔍 测试交易数据...")
    
    trade_data = {
        "ticker": "TSLA",
        "action": "sell",
        "quantity": 120,
        "data": {
            "symbol": "TSLA",
            "CVDsignal": "cvdBelowMA",
            "choppiness": "46.4125643135",
            "adxValue": "35.341643694",
            "BBPsignal": "bullpower",
            "RSIHAsignal": "BearishHA",
            "SQZsignal": "no squeeze",
            "choppingrange_signal": "no chopping",
            "rsi_state_trend": "Bearish",
            "center_trend": "Strong Bearish",
            "adaptive_timeframe_1": "60",
            "adaptive_timeframe_2": "240",
            "MAtrend": "-1",
            "MAtrend_timeframe1": "-1",
            "MAtrend_timeframe2": "1",
            "MOMOsignal": "bearishmomo",
            "Middle_smooth_trend": "Bearish +",
            "TrendTracersignal": "-1",
            "TrendTracerHTF": "-1",
            "pmaText": "PMA Bearish",
            "trend_change_volatility_stop": "336.46",
            "AIbandsignal": "red downtrend",
            "HTFwave_signal": "Bearish",
            "wavemarket_state": "Short Strong",
            "ewotrend_state": "Strong Bearish"
        },
        "takeProfit": {
            "limitPrice": 322.79
        },
        "stopLoss": {
            "stopPrice": 332.72
        },
        "extras": {
            "indicator": "WaveMatrix shortStrongSignal",
            "timeframe": "15m",
            "oscrating": 90,
            "trendrating": 100,
            "risk": 1
        }
    }
    
    handler = TradingViewHandler()
    success = handler.store_enhanced_data(trade_data)
    
    if success:
        print("✅ 交易数据存储成功")
        print(f"   数据类型: {handler._detect_data_type(trade_data)}")
        symbol, timeframe = handler._extract_basic_info(trade_data, 'trade')
        print(f"   股票代码: {symbol}, 时间框架: {timeframe}")
        print(f"   交易动作: {trade_data['action']}, 数量: {trade_data['quantity']}")
        print(f"   止盈价格: {trade_data['takeProfit']['limitPrice']}")
        print(f"   止损价格: {trade_data['stopLoss']['stopPrice']}")
        print(f"   风险等级: {trade_data['extras']['risk']}")
    else:
        print("❌ 交易数据存储失败")
    
    return success

def test_close_data():
    """测试平仓数据 (sentiment: flat，平仓多头或空头)"""
    print("\n🔍 测试平仓数据...")
    
    close_data = {
        "ticker": "GOOG",
        "action": "sell",
        "sentiment": "flat",
        "extras": {
            "indicator": "TrailingStop Exit Long",
            "timeframe": "1h"
        }
    }
    
    handler = TradingViewHandler()
    success = handler.store_enhanced_data(close_data)
    
    if success:
        print("✅ 平仓数据存储成功")
        print(f"   数据类型: {handler._detect_data_type(close_data)}")
        symbol, timeframe = handler._extract_basic_info(close_data, 'close')
        print(f"   股票代码: {symbol}, 时间框架: {timeframe}")
        print(f"   平仓动作: {close_data['action']} (flat sentiment = 平仓多头)")
        print(f"   触发指标: {close_data['extras']['indicator']}")
    else:
        print("❌ 平仓数据存储失败")
    
    return success

def verify_database_records():
    """验证数据库中的记录"""
    print("\n🔍 验证数据库记录...")
    
    try:
        session = get_db_session()
        
        # 查询所有记录
        records = session.query(TradingViewData).order_by(TradingViewData.received_at.desc()).all()
        
        print(f"📊 数据库中共有 {len(records)} 条记录:")
        
        for record in records:
            print(f"   {record.data_type:>6} | {record.symbol:>6} | {record.timeframe:>4} | {record.action or 'N/A':>6} | {record.received_at}")
            if record.data_type == 'trade':
                print(f"          止盈: {record.take_profit_price}, 止损: {record.stop_loss_price}")
                print(f"          风险: {record.risk_level}, 指标: {record.trigger_indicator}")
            elif record.data_type == 'close':
                print(f"          平仓指标: {record.trigger_indicator}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试三种TradingView数据类型...")
    print("=" * 60)
    
    # 测试三种数据类型
    signal_success = test_signal_data()
    trade_success = test_trade_data()
    close_success = test_close_data()
    
    # 验证数据库记录
    db_success = verify_database_records()
    
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    print(f"   信号数据: {'✅ 成功' if signal_success else '❌ 失败'}")
    print(f"   交易数据: {'✅ 成功' if trade_success else '❌ 失败'}")
    print(f"   平仓数据: {'✅ 成功' if close_success else '❌ 失败'}")
    print(f"   数据库验证: {'✅ 成功' if db_success else '❌ 失败'}")
    
    if all([signal_success, trade_success, close_success, db_success]):
        print("\n🎉 所有测试通过！三种数据类型系统工作正常！")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查系统配置")
        return False

if __name__ == "__main__":
    main()