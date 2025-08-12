#!/usr/bin/env python3
"""
测试用户限制功能的脚本
验证数据库连接和限制功能是否正常工作
"""
import os
import sys
from datetime import datetime, timezone
from rate_limiter import RateLimiter
from models import get_db_session, UserRequestLimit, ExemptUser

def test_normal_user_limit():
    """测试普通用户限制功能"""
    print("🧪 测试普通用户限制功能...")
    
    rate_limiter = RateLimiter(daily_limit=3)
    test_user_id = "test_user_123"
    test_username = "TestUser"
    
    print(f"测试用户: {test_username} (ID: {test_user_id})")
    
    # 清除测试用户的历史记录
    try:
        db = get_db_session()
        db.query(UserRequestLimit).filter(UserRequestLimit.user_id == test_user_id).delete()
        db.query(ExemptUser).filter(ExemptUser.user_id == test_user_id).delete()
        db.commit()
        db.close()
        print("✅ 清除测试用户历史记录")
    except Exception as e:
        print(f"⚠️ 清除历史记录失败: {e}")
    
    # 测试第1次请求
    can_request, current, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"第1次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    if can_request:
        success = rate_limiter.record_request(test_user_id, test_username)
        print(f"第1次记录: {success}")
    
    # 测试第2次请求
    can_request, current, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"第2次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    if can_request:
        success = rate_limiter.record_request(test_user_id, test_username)
        print(f"第2次记录: {success}")
    
    # 测试第3次请求
    can_request, current, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"第3次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    if can_request:
        success = rate_limiter.record_request(test_user_id, test_username)
        print(f"第3次记录: {success}")
    
    # 测试第4次请求（应该被限制）
    can_request, current, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
    print(f"第4次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
    
    if can_request:
        print("❌ 错误: 第4次请求应该被限制")
        return False
    else:
        print("✅ 正确: 第4次请求被正确限制")
        return True

def test_exempt_user():
    """测试豁免用户功能"""
    print("\n🧪 测试豁免用户功能...")
    
    rate_limiter = RateLimiter(daily_limit=3)
    exempt_user_id = "exempt_user_456"
    exempt_username = "ExemptUser"
    
    # 添加豁免用户
    try:
        db = get_db_session()
        # 清除现有记录
        db.query(ExemptUser).filter(ExemptUser.user_id == exempt_user_id).delete()
        db.query(UserRequestLimit).filter(UserRequestLimit.user_id == exempt_user_id).delete()
        
        # 添加豁免用户
        exempt_user = ExemptUser(
            user_id=exempt_user_id,
            username=exempt_username,
            reason="测试豁免用户",
            added_by="system"
        )
        db.add(exempt_user)
        db.commit()
        db.close()
        print("✅ 添加豁免用户成功")
    except Exception as e:
        print(f"❌ 添加豁免用户失败: {e}")
        return False
    
    # 测试豁免用户多次请求
    for i in range(1, 6):  # 测试5次请求
        can_request, current, remaining = rate_limiter.check_user_limit(exempt_user_id, exempt_username)
        print(f"豁免用户第{i}次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if not can_request:
            print(f"❌ 错误: 豁免用户第{i}次请求应该被允许")
            return False
        
        success = rate_limiter.record_request(exempt_user_id, exempt_username)
        print(f"豁免用户第{i}次记录: {success}")
    
    print("✅ 豁免用户功能正常")
    return True

def show_database_stats():
    """显示数据库统计信息"""
    print("\n📊 数据库统计信息:")
    
    try:
        db = get_db_session()
        
        # 总记录数
        total_requests = db.query(UserRequestLimit).count()
        total_users = db.query(UserRequestLimit.user_id).distinct().count()
        total_exempt = db.query(ExemptUser).count()
        
        print(f"总请求记录: {total_requests}")
        print(f"总用户数: {total_users}")
        print(f"豁免用户数: {total_exempt}")
        
        # 最近记录
        recent_requests = db.query(UserRequestLimit).order_by(UserRequestLimit.last_request_time.desc()).limit(3).all()
        if recent_requests:
            print("\n最近请求记录:")
            for req in recent_requests:
                print(f"  {req.username}: {req.request_count}次 ({req.last_request_time})")
        
        # 豁免用户列表
        exempt_users = db.query(ExemptUser).all()
        if exempt_users:
            print("\n豁免用户列表:")
            for user in exempt_users:
                print(f"  {user.username} ({user.user_id}): {user.reason}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 获取数据库统计失败: {e}")

def main():
    """主测试函数"""
    print("🚀 Discord机器人用户限制功能测试")
    print("=" * 40)
    
    # 检查环境变量
    if not os.environ.get('DATABASE_URL'):
        print("❌ 错误: DATABASE_URL环境变量未设置")
        print("请确保在Docker环境中运行或设置正确的数据库连接")
        return 1
    
    print(f"数据库URL: {os.environ.get('DATABASE_URL')[:30]}...")
    
    # 运行测试
    try:
        # 测试普通用户限制
        normal_test_passed = test_normal_user_limit()
        
        # 测试豁免用户
        exempt_test_passed = test_exempt_user()
        
        # 显示统计信息
        show_database_stats()
        
        if normal_test_passed and exempt_test_passed:
            print("\n✅ 所有测试通过！用户限制功能正常工作。")
            return 0
        else:
            print("\n❌ 测试失败！用户限制功能有问题。")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())