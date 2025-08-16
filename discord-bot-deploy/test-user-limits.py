#!/usr/bin/env python3
"""
用户限制功能完整测试脚本
验证Docker环境下的数据库连接和用户限制逻辑
"""

import os
import sys
from datetime import datetime, date
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        from models import get_db_session, UserRequestLimit, ExemptUser
        db = get_db_session()
        
        # 测试简单查询
        result = db.execute("SELECT 1").fetchone()
        if result and result[0] == 1:
            print("✅ 数据库连接测试成功")
        else:
            print("❌ 数据库连接测试失败")
            return False
        
        # 测试表存在
        tables = db.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall()
        table_names = [table[0] for table in tables]
        
        required_tables = ['user_request_limits', 'exempt_users']
        for table in required_tables:
            if table in table_names:
                print(f"✅ 数据库表 {table} 存在")
            else:
                print(f"❌ 数据库表 {table} 不存在")
                return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def test_rate_limiter():
    """测试用户限制功能"""
    print("\n🔍 测试用户限制功能...")
    try:
        from rate_limiter import RateLimiter
        
        # 创建限制器实例
        limiter = RateLimiter(daily_limit=3)
        print("✅ RateLimiter实例创建成功")
        
        # 测试用户ID
        test_user_id = "test_user_12345"
        test_username = "TestUser"
        
        print(f"\n📊 测试用户限制逻辑 (用户: {test_username})...")
        
        # 清除之前的测试数据
        from models import get_db_session, UserRequestLimit
        from sqlalchemy import and_
        
        db = get_db_session()
        today = date.today()
        existing = db.query(UserRequestLimit).filter(
            and_(
                UserRequestLimit.user_id == test_user_id,
                UserRequestLimit.request_date == today
            )
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
            print("🧹 清除之前的测试数据")
        
        db.close()
        
        # 测试场景1：新用户首次请求
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"首次检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if can_request and current == 0 and remaining == 3:
            print("✅ 新用户限制检查正确")
        else:
            print("❌ 新用户限制检查异常")
            return False
        
        # 测试场景2：记录请求
        success = limiter.record_request(test_user_id, test_username)
        if success:
            print("✅ 请求记录成功")
        else:
            print("❌ 请求记录失败")
            return False
        
        # 测试场景3：检查更新后的限制
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"记录后检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if can_request and current == 1 and remaining == 2:
            print("✅ 请求计数更新正确")
        else:
            print("❌ 请求计数更新异常")
            return False
        
        # 测试场景4：模拟达到限制
        for i in range(2):  # 再记录2次请求，总共3次
            limiter.record_request(test_user_id, test_username)
        
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"达到限制后: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if not can_request and current == 3 and remaining == 0:
            print("✅ 限制逻辑工作正确")
        else:
            print("❌ 限制逻辑异常")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 用户限制功能测试失败: {e}")
        logger.exception("详细错误:")
        return False

def test_exempt_system():
    """测试豁免系统"""
    print("\n🔍 测试豁免用户系统...")
    try:
        from models import get_db_session, ExemptUser
        
        db = get_db_session()
        
        # 测试豁免用户ID
        test_exempt_id = "exempt_user_12345"
        test_exempt_username = "ExemptUser"
        
        # 清除之前的测试数据
        existing = db.query(ExemptUser).filter(ExemptUser.user_id == test_exempt_id).first()
        if existing:
            db.delete(existing)
            db.commit()
            print("🧹 清除之前的豁免测试数据")
        
        # 添加豁免用户
        exempt_user = ExemptUser(
            user_id=test_exempt_id,
            username=test_exempt_username,
            reason="测试豁免用户",
            added_by="admin_test"
        )
        db.add(exempt_user)
        db.commit()
        print("✅ 豁免用户添加成功")
        
        # 测试豁免检查
        from rate_limiter import RateLimiter
        limiter = RateLimiter()
        
        # 豁免用户应该不受限制
        can_request, current, remaining = limiter.check_user_limit(test_exempt_id, test_exempt_username)
        print(f"豁免用户检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        if can_request:
            print("✅ 豁免用户不受限制")
        else:
            print("❌ 豁免用户限制异常")
            db.close()
            return False
        
        # 清除测试数据
        db.delete(exempt_user)
        db.commit()
        db.close()
        print("🧹 清除豁免测试数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 豁免系统测试失败: {e}")
        logger.exception("详细错误:")
        return False

def main():
    """主测试函数"""
    print("🚀 开始用户限制功能完整测试")
    print("=" * 50)
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL环境变量未设置")
        sys.exit(1)
    
    print(f"📊 DATABASE_URL: {database_url}")
    
    # 运行测试
    tests = [
        ("数据库连接", test_database_connection),
        ("用户限制功能", test_rate_limiter),
        ("豁免用户系统", test_exempt_system),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                failed += 1
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！用户限制功能在Docker环境下工作正常")
        return True
    else:
        print("⚠️ 有测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)