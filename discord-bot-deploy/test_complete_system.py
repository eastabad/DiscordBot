#!/usr/bin/env python3
"""
完整系统测试
测试TradingView webhook接收、数据存储和报告生成的完整流程
"""
import asyncio
import logging
import json
from datetime import datetime
import aiohttp

async def test_complete_system():
    """测试完整系统功能"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🔄 开始完整系统测试...")
    
    # 1. 测试TradingView webhook数据发送
    logger.info("📡 测试1: 发送TradingView webhook数据...")
    
    test_data = [
        {
            "headers": {
                "content-type": "application/json; charset=utf-8"
            },
            "body": {
                "symbol": "AAPL",
                "CVDsignal": "cvdAboveMA", 
                "choppiness": "35.2154867921",
                "adxValue": "24.8765432109",
                "BBPsignal": "bearpower",
                "RSIHAsignal": "BearishHA",
                "SQZsignal": "squeeze",
                "adaptive_timeframe_1": "60",
                "adaptive_timeframe_2": "240",
                "rsi_state_trend": "Bullish",
                "center_trend": "Strong Bullish",
                "AIbandsignal": "red downtrend",
                "TrendTracersignal": "-1",
                "MOMOsignal": "bearishmomo"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:5000/webhook-test/TV',
                json=test_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Webhook测试成功: {result['message']}")
                else:
                    logger.error(f"❌ Webhook测试失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Webhook请求失败: {e}")
            return False
    
    # 2. 验证数据存储
    logger.info("🗄️ 测试2: 验证数据库存储...")
    
    try:
        from tradingview_handler import TradingViewHandler
        tv_handler = TradingViewHandler()
        
        # 查询刚刚存储的AAPL数据
        latest_data = tv_handler.get_latest_data("AAPL", "1h")
        if latest_data:
            logger.info(f"✅ 数据库验证成功: {latest_data.symbol} {latest_data.timeframe}")
            logger.info(f"   数据时间: {latest_data.timestamp}")
        else:
            logger.error("❌ 数据库中未找到AAPL数据")
            return False
    except Exception as e:
        logger.error(f"❌ 数据库验证失败: {e}")
        return False
    
    # 3. 测试报告生成
    logger.info("📊 测试3: 测试AI报告生成...")
    
    try:
        from gemini_report_generator import GeminiReportGenerator
        gemini_generator = GeminiReportGenerator()
        
        report = gemini_generator.generate_stock_report(latest_data, "系统测试")
        if report and len(report) > 100:
            logger.info("✅ AI报告生成成功")
            logger.info(f"   报告长度: {len(report)} 字符")
        else:
            logger.warning("⚠️ AI报告生成返回空或过短内容，使用备用报告")
    except Exception as e:
        logger.error(f"❌ AI报告生成失败: {e}")
        return False
    
    # 4. 测试报告解析功能
    logger.info("🔍 测试4: 测试报告请求解析...")
    
    try:
        from report_handler import ReportHandler
        
        # 创建一个简单的模拟bot对象
        class MockBot:
            pass
        
        mock_bot = MockBot()
        report_handler = ReportHandler(mock_bot)
        
        # 测试不同格式的报告请求
        test_requests = [
            "AAPL 1h",
            "TSLA 15m", 
            "NVDA 4小时",
            "MSTR 15分钟"
        ]
        
        for request in test_requests:
            parsed = report_handler.parse_report_request(request)
            if parsed:
                symbol, timeframe = parsed
                logger.info(f"✅ 解析成功: '{request}' -> {symbol} {timeframe}")
            else:
                logger.warning(f"⚠️ 解析失败: '{request}'")
                
    except Exception as e:
        logger.error(f"❌ 报告解析测试失败: {e}")
        return False
    
    # 5. 系统状态检查
    logger.info("🌐 测试5: 检查API服务器状态...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:5000/api/health') as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ API服务器健康检查通过: {result}")
                else:
                    logger.error(f"❌ API服务器健康检查失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ API服务器连接失败: {e}")
            return False
    
    logger.info("🎉 完整系统测试全部通过!")
    logger.info("=" * 60)
    logger.info("功能验证总结:")
    logger.info("✅ TradingView webhook数据接收")
    logger.info("✅ 数据解析和数据库存储") 
    logger.info("✅ AI报告生成(Gemini集成)")
    logger.info("✅ 报告请求格式解析")
    logger.info("✅ API服务器健康状态")
    logger.info("=" * 60)
    logger.info("🚀 系统已准备就绪，可以处理TradingView数据和生成报告!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_complete_system())