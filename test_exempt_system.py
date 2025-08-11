#!/usr/bin/env python3
"""
豁免用户系统测试脚本
测试豁免用户的添加、移除和限制检查功能
"""

import sys
from rate_limiter import RateLimiter

def test_exempt_system():
    """测试豁免用户系统"""
    print("🧪 开始测试豁免用户系统...")
    
    # 创建限制管理器
    rate_limiter = RateLimiter(daily_limit=3)
    
    # 测试用户
    test_user_id = "test_user_123"
    test_username = "TestUser"
    
    print(f"\n1. 测试普通用户限制检查...")
    can_request, current_count, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"   普通用户: 可请求={can_request}, 已用={current_count}, 剩余={remaining}")
    assert remaining != 999, "普通用户应该有限制"
    
    print(f"\n2. 添加豁免用户...")
    success = rate_limiter.add_exempt_user(test_user_id, test_username, "测试豁免", "admin_test")
    print(f"   添加结果: {success}")
    assert success, "应该成功添加豁免用户"
    
    print(f"\n3. 检查豁免用户限制...")
    can_request, current_count, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"   豁免用户: 可请求={can_request}, 已用={current_count}, 剩余={remaining}")
    assert remaining == 999, "豁免用户应该显示999剩余次数"
    assert can_request == True, "豁免用户应该允许请求"
    
    print(f"\n4. 获取豁免用户列表...")
    exempt_list = rate_limiter.list_exempt_users()
    print(f"   豁免用户数量: {len(exempt_list)}")
    found_test_user = any(user['user_id'] == test_user_id for user in exempt_list)
    assert found_test_user, "应该在豁免列表中找到测试用户"
    
    print(f"\n5. 移除豁免用户...")
    success = rate_limiter.remove_exempt_user(test_user_id)
    print(f"   移除结果: {success}")
    assert success, "应该成功移除豁免用户"
    
    print(f"\n6. 验证移除后的限制...")
    can_request, current_count, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"   移除后: 可请求={can_request}, 已用={current_count}, 剩余={remaining}")
    assert remaining != 999, "移除后应该恢复限制"
    
    print(f"\n✅ 所有测试通过！豁免用户系统工作正常")

if __name__ == "__main__":
    try:
        test_exempt_system()
        print(f"\n🎉 豁免用户系统测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)