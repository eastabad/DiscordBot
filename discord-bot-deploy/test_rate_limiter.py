#!/usr/bin/env python3
"""
测试请求限制功能
"""
import logging
from rate_limiter import RateLimiter
from models import create_tables

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_rate_limiter():
    """测试请求限制功能"""
    print("=== 测试请求限制功能 ===")
    
    # 创建数据库表
    create_tables()
    
    # 创建限制器
    limiter = RateLimiter(daily_limit=3)
    
    # 测试用户
    test_user_id = "123456789"
    test_username = "TestUser"
    
    print(f"\n--- 测试用户: {test_username} ---")
    
    # 第一次检查（新用户）
    can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
    print(f"首次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    # 模拟3次请求
    for i in range(1, 4):
        print(f"\n第{i}次请求:")
        
        # 检查限制
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"  检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if can_request:
            # 记录请求
            success = limiter.record_request(test_user_id, test_username)
            print(f"  记录: 成功={success}")
            
            # 再次检查
            can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
            print(f"  记录后: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        else:
            print(f"  ❌ 请求被拒绝")
    
    # 尝试第4次请求（应该被拒绝）
    print(f"\n第4次请求（超限测试）:")
    can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
    print(f"  检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    if not can_request:
        print("  ✅ 正确拒绝超限请求")
    
    # 获取用户统计
    print(f"\n--- 用户统计 ---")
    stats = limiter.get_user_stats(test_user_id)
    if stats:
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # 测试重置功能
    print(f"\n--- 测试重置功能 ---")
    reset_success = limiter.reset_user_limit(test_user_id)
    print(f"重置结果: {reset_success}")
    
    if reset_success:
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"重置后: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_rate_limiter()