#!/usr/bin/env python3
"""
测试图表分析服务
"""

import asyncio
import sys
from config import Config
from chart_analysis_service import ChartAnalysisService

async def test_chart_analysis():
    """测试图表分析服务"""
    print("=== 测试图表分析服务 ===")
    
    config = Config()
    analysis_service = ChartAnalysisService(config)
    
    # 模拟图片URL测试（使用空字符串模拟）
    test_symbols = ["AAPL", "TSLA", "GOOGL", "NVDA"]
    
    for symbol in test_symbols:
        print(f"\n--- 测试图表分析: {symbol} ---")
        
        try:
            # 使用模拟图片数据测试
            mock_image_data = f"mock_image_data_for_{symbol}".encode()
            analysis = await analysis_service.perform_chart_analysis(mock_image_data, symbol)
            
            if "error" in analysis:
                print(f"❌ {symbol} 分析失败: {analysis['message']}")
            else:
                print(f"✅ {symbol} 分析成功")
                
                # 显示分析详情
                chart = analysis["chart_analysis"]
                
                print(f"  AI趋势带: {chart['ai_trend_bands']['signal']} - {chart['ai_trend_bands']['description']}")
                print(f"  TrendTracer: {chart['trend_tracer']['direction']} - 动量{chart['trend_tracer']['momentum']}%")
                print(f"  EMA带宽: {chart['ema_bands']['width']} - {chart['ema_bands']['color']}")
                print(f"  支撑压力: {chart['support_resistance']['type']} - {chart['support_resistance']['level']}")
                print(f"  评级: 看涨{chart['rating_panel']['bull_rating']}% vs 看跌{chart['rating_panel']['bear_rating']}%")
                print(f"  WaveMatrix: {chart['wave_matrix']['bars']['color']}柱子{chart['wave_matrix']['bars']['percentage']} - 目标{chart['wave_matrix']['target_price']}")
                
                print(f"  整体情绪: {analysis['overall_sentiment']}")
                print(f"  置信度: {analysis['confidence_level']}%")
                print(f"  建议: {analysis['trading_recommendation']}")
                
        except Exception as e:
            print(f"❌ 测试 {symbol} 时出错: {e}")
    
    print("\n--- 测试消息格式化 ---")
    try:
        test_analysis = await analysis_service.perform_chart_analysis(b"mock_data", "AAPL")
        formatted_message = analysis_service.format_analysis_message(test_analysis)
        print("Discord消息格式预览:")
        print("-" * 60)
        print(formatted_message)
        print("-" * 60)
    except Exception as e:
        print(f"消息格式化测试失败: {e}")
    
    print("\n=== 图表分析服务测试完成 ===")

def test_image_detection():
    """测试图片检测逻辑"""
    print("\n=== 测试图片检测逻辑 ===")
    
    # 模拟附件对象
    class MockAttachment:
        def __init__(self, filename, size):
            self.filename = filename
            self.size = size
    
    # 模拟机器人类来测试图片检测
    class MockBot:
        def has_chart_image(self, attachments) -> bool:
            for attachment in attachments:
                filename = attachment.filename.lower()
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    if attachment.size < 10 * 1024 * 1024:  # 10MB限制
                        return True
            return False
    
    bot = MockBot()
    
    # 测试不同的附件
    test_attachments = [
        [MockAttachment("chart.png", 1024*1024)],  # 1MB PNG - 应该通过
        [MockAttachment("screenshot.jpg", 2*1024*1024)],  # 2MB JPG - 应该通过
        [MockAttachment("photo.jpeg", 5*1024*1024)],  # 5MB JPEG - 应该通过
        [MockAttachment("large.png", 12*1024*1024)],  # 12MB PNG - 应该拒绝（太大）
        [MockAttachment("document.pdf", 1024*1024)],  # PDF - 应该拒绝（非图片）
        [MockAttachment("text.txt", 1024)],  # TXT - 应该拒绝（非图片）
        [],  # 无附件 - 应该拒绝
        [MockAttachment("chart.png", 1024*1024), MockAttachment("doc.pdf", 2048)],  # 混合 - 应该通过（有PNG）
    ]
    
    descriptions = [
        "1MB PNG文件",
        "2MB JPG文件", 
        "5MB JPEG文件",
        "12MB PNG文件（过大）",
        "PDF文档",
        "文本文件",
        "无附件",
        "PNG+PDF混合文件"
    ]
    
    print("图片检测测试:")
    for attachments, desc in zip(test_attachments, descriptions):
        result = bot.has_chart_image(attachments)
        status = "✅ 检测到图片" if result else "❌ 未检测到图片"
        print(f"  {desc}: {status}")

if __name__ == "__main__":
    try:
        # 测试图片检测
        test_image_detection()
        
        # 测试图表分析服务
        asyncio.run(test_chart_analysis())
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()