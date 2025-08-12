#!/usr/bin/env python3
"""
测试每日日志记录器功能
"""

from daily_logger import daily_logger
import time

def test_logger():
    """测试日志记录功能"""
    print("🧪 测试每日日志记录器...")
    
    # 测试记录不同类型的请求
    test_requests = [
        {
            "user_id": "1234567890",
            "username": "TestUser1",
            "request_type": "chart",
            "content": "AAPL 1h",
            "success": True,
            "channel_name": "test-channel",
            "guild_name": "Test Guild"
        },
        {
            "user_id": "2345678901", 
            "username": "TestUser2",
            "request_type": "prediction",
            "content": "TSLA",
            "success": True,
            "channel_name": "test-channel",
            "guild_name": "Test Guild"
        },
        {
            "user_id": "3456789012",
            "username": "TestUser3", 
            "request_type": "analysis",
            "content": "NVDA - chart.png",
            "success": False,
            "error": "图片无法识别",
            "channel_name": "test-channel",
            "guild_name": "Test Guild"
        }
    ]
    
    # 记录测试请求
    for i, request in enumerate(test_requests):
        print(f"📝 记录测试请求 {i+1}: {request['request_type']} - {request['username']}")
        daily_logger.log_request(**request)
        time.sleep(0.1)  # 小延迟
    
    print("\n✅ 测试请求记录完成")
    
    # 打印今日统计
    print("\n" + "="*50)
    print("📊 今日统计测试")
    print("="*50)
    daily_logger.print_today_summary()
    
    # 获取统计数据
    summary = daily_logger.get_today_summary()
    print(f"\n🔍 详细数据检查:")
    print(f"总请求数: {summary['total_requests']}")
    print(f"活跃用户数: {len(summary['users'])}")
    print(f"成功率: {summary['success_rate']}%")
    
    return summary

if __name__ == "__main__":
    test_logger()