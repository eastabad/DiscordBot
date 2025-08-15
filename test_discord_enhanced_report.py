#!/usr/bin/env python3
"""
测试Discord机器人的增强版报告生成集成
模拟Discord用户请求报告的流程
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from report_handler import ReportHandler
from rate_limiter import RateLimiter
from gemini_report_generator import GeminiReportGenerator
from tradingview_handler import TradingViewHandler
from models import get_db_session, TradingViewData

class MockDiscordMessage:
    """模拟Discord消息对象"""
    def __init__(self, content: str, user_id: str = "test_user_123"):
        self.content = content
        self.author = MockUser(user_id)
    
    async def reply(self, content):
        print(f"[BOT REPLY] {content}")
        return MockMessage(content)

class MockUser:
    """模拟Discord用户对象"""
    def __init__(self, user_id: str):
        self.id = user_id
        self.display_name = f"TestUser_{user_id[-3:]}"
    
    async def send(self, embed=None, content=None):
        if embed:
            print(f"[PRIVATE MESSAGE - EMBED] 发送给 {self.display_name}")
            print(f"  标题: {embed.title}")
            print(f"  描述长度: {len(embed.description)} 字符")
        else:
            print(f"[PRIVATE MESSAGE] {content}")

class MockMessage:
    """模拟消息对象"""
    def __init__(self, content):
        self.content = content
    
    async def edit(self, content):
        print(f"[MESSAGE EDIT] {content}")

async def test_discord_enhanced_report():
    """测试Discord增强版报告集成"""
    print("🚀 开始测试Discord增强版报告集成...")
    print("=" * 60)
    
    try:
        # 初始化组件
        rate_limiter = RateLimiter()
        tv_handler = TradingViewHandler()
        gemini_generator = GeminiReportGenerator()
        report_handler = ReportHandler(rate_limiter, tv_handler, gemini_generator)
        
        print("✅ 所有组件初始化成功")
        
        # 检查数据库数据
        session = get_db_session()
        
        # 找到有完整数据的股票
        symbols_with_data = session.query(TradingViewData.symbol).filter(
            TradingViewData.data_type == 'signal'
        ).distinct().all()
        
        if not symbols_with_data:
            print("❌ 数据库中没有signal数据，无法进行测试")
            return False
        
        test_symbol = symbols_with_data[0][0]
        signal_data = session.query(TradingViewData).filter(
            TradingViewData.symbol == test_symbol,
            TradingViewData.data_type == 'signal'
        ).first()
        
        timeframe = signal_data.timeframe if signal_data else '15m'
        session.close()
        
        print(f"📊 使用测试数据: {test_symbol} {timeframe}")
        
        # 测试用例1: 标准报告请求
        print(f"\n🧪 测试用例1: 标准报告请求 '{test_symbol} {timeframe}'")
        print("-" * 40)
        
        mock_message = MockDiscordMessage(f"{test_symbol} {timeframe}")
        await report_handler.process_report_request(mock_message)
        
        # 测试用例2: 空格格式请求
        print(f"\n🧪 测试用例2: 空格格式请求 '{test_symbol.lower()} {timeframe}'")
        print("-" * 40)
        
        mock_message2 = MockDiscordMessage(f"{test_symbol.lower()} {timeframe}")
        await report_handler.process_report_request(mock_message2)
        
        # 测试用例3: 错误格式
        print(f"\n🧪 测试用例3: 错误格式 'invalid request'")
        print("-" * 40)
        
        mock_message3 = MockDiscordMessage("invalid request")
        await report_handler.process_report_request(mock_message3)
        
        print("\n" + "=" * 60)
        print("🎉 Discord增强版报告集成测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_discord_enhanced_report())
    sys.exit(0 if success else 1)