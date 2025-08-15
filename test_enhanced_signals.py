#!/usr/bin/env python3
"""
测试增强的TradingView信号解析和AI报告生成系统
"""

import logging
import json
import requests
from datetime import datetime
from tradingview_handler import TradingViewHandler
from gemini_report_generator import GeminiReportGenerator
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_signal_parsing():
    """测试增强的信号解析功能"""
    logger.info("🔍 开始测试增强的信号解析功能...")
    
    # 创建完整的测试数据，包含您提供的所有22+技术指标
    test_webhook_data = [{
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
            "MAtrend_timeframe2": "0",  # 观望状态
            "Middle_smooth_trend": "Bullish +",
            "MOMOsignal": "bullishmomo",
            "TrendTracersignal": "1",
            "TrendTracerHTF": "-1",  # 高时间框架下跌
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
    
    # 初始化处理器
    handler = TradingViewHandler()
    
    # 解析webhook数据
    parsed_data = handler.parse_webhook_data(test_webhook_data)
    
    if parsed_data:
        logger.info("✅ Webhook数据解析成功")
        logger.info(f"   股票代码: {parsed_data['symbol']}")
        logger.info(f"   时间框架: {parsed_data['timeframe']}")
        logger.info(f"   信号数量: {len(parsed_data.get('signals', []))}")
        
        # 打印解析的信号
        print("\n📊 解析的交易信号:")
        for i, signal in enumerate(parsed_data.get('signals', []), 1):
            print(f"  {i:2d}. {signal}")
        
        return parsed_data
    else:
        logger.error("❌ Webhook数据解析失败")
        return None

def test_enhanced_ai_report():
    """测试增强的AI报告生成功能"""
    logger.info("🤖 开始测试增强的AI报告生成...")
    
    # 使用之前解析的数据生成报告
    parsed_data = test_enhanced_signal_parsing()
    if not parsed_data:
        return
    
    try:
        # 创建模拟的TradingViewData对象
        tv_data = type('TradingViewData', (), {
            'symbol': parsed_data['symbol'],
            'timeframe': parsed_data['timeframe'],
            'timestamp': parsed_data['timestamp'],
            'raw_data': parsed_data['raw_data']
        })()
        
        # 初始化Gemini报告生成器
        generator = GeminiReportGenerator()
        
        # 生成报告
        report = generator.generate_stock_report(tv_data, "详细技术分析")
        
        logger.info("✅ AI报告生成成功")
        logger.info(f"   报告长度: {len(report)} 字符")
        
        print("\n" + "="*60)
        print("📊 生成的AI分析报告:")
        print("="*60)
        print(report)
        print("="*60)
        
        return report
        
    except Exception as e:
        logger.error(f"❌ AI报告生成失败: {e}")
        return None

def test_webhook_endpoint():
    """测试webhook端点接收增强数据"""
    logger.info("🌐 测试webhook端点...")
    
    # 准备完整的测试数据
    test_data = [{
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": {
            "symbol": "NVDA",
            "pmaText": "PMA Bearish",
            "CVDsignal": "cvdBelowMA",
            "choppiness": "68.7834521098",
            "adxValue": "18.5432109876",
            "BBPsignal": "bearpower",
            "RSIHAsignal": "BearishHA",
            "SQZsignal": "squeeze",
            "choppingrange_signal": "chopping",
            "rsi_state_trend": "Bearish",
            "center_trend": "Weak Bearish",
            "MAtrend": "-1",
            "MAtrend_timeframe1": "0",
            "MAtrend_timeframe2": "-1",
            "Middle_smooth_trend": "Bearish",
            "MOMOsignal": "bearishmomo",
            "TrendTracersignal": "-1",
            "TrendTracerHTF": "-1",
            "trend_change_volatility_stop": "520.15",
            "AIbandsignal": "red downtrend",
            "wavemarket_state": "Short Strong",
            "ewotrend_state": "Strong Bearish",
            "HTFwave_signal": "Bearish",
            "adaptive_timeframe_1": "15",
            "adaptive_timeframe_2": "240",  # 4小时
            "stopLoss": {"stopPrice": 535.75},
            "takeProfit": {"limitPrice": 485.20},
            "risk": "极高风险",
            "action": "sell",
            "extras": {"oscrating": 45, "trendrating": 72}
        }
    }]
    
    try:
        # 发送到webhook端点
        response = requests.post(
            "http://localhost:5000/webhook-test/TV",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Webhook端点测试成功")
            result = response.json()
            logger.info(f"   响应: {result.get('message', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Webhook端点测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook端点连接失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始增强信号解析系统完整测试...")
    
    print("\n" + "="*60)
    print("🔬 增强TradingView信号解析系统测试")
    print("="*60)
    
    # 测试1: 信号解析
    print("\n📝 测试1: 增强信号解析功能")
    signal_result = test_enhanced_signal_parsing()
    
    # 测试2: AI报告生成
    print("\n🤖 测试2: 增强AI报告生成功能")
    report_result = test_enhanced_ai_report()
    
    # 测试3: Webhook端点
    print("\n🌐 测试3: Webhook端点完整数据接收")
    webhook_result = test_webhook_endpoint()
    
    # 总结测试结果
    print("\n" + "="*60)
    print("📊 测试结果总结:")
    print("="*60)
    print(f"✅ 信号解析: {'通过' if signal_result else '失败'}")
    print(f"✅ AI报告生成: {'通过' if report_result else '失败'}")
    print(f"✅ Webhook端点: {'通过' if webhook_result else '失败'}")
    
    if signal_result and report_result and webhook_result:
        print("\n🎉 所有测试通过! 增强信号解析系统工作正常!")
        print("\n💡 系统现在支持:")
        print("   • 22+ 技术指标完整解析")
        print("   • 中文信号映射和说明")
        print("   • 止损止盈价格提取")
        print("   • 风险等级评估")
        print("   • 结构化Markdown报告生成")
        print("   • 多时间框架趋势分析")
    else:
        print("\n⚠️ 部分测试未通过，请检查系统配置")

if __name__ == "__main__":
    main()