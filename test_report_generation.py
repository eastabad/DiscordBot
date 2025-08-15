#!/usr/bin/env python3
"""
测试报告生成功能
"""
import asyncio
import logging
from tradingview_handler import TradingViewHandler
from gemini_report_generator import GeminiReportGenerator

async def test_report():
    """测试报告生成"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 1. 从数据库获取最新的MSTR数据
        tv_handler = TradingViewHandler()
        latest_data = tv_handler.get_latest_data("MSTR", "15m")
        
        if not latest_data:
            logger.error("❌ 未找到MSTR 15m数据")
            return
        
        logger.info(f"✅ 找到数据: {latest_data.symbol} {latest_data.timeframe} - {latest_data.timestamp}")
        
        # 2. 生成报告
        gemini_generator = GeminiReportGenerator()
        report = gemini_generator.generate_stock_report(latest_data, "测试报告生成")
        
        logger.info("✅ 报告生成成功")
        print("\n" + "="*50)
        print("📊 生成的报告:")
        print("="*50)
        print(report)
        print("="*50)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_report())