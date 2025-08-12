#!/usr/bin/env python3
"""
Discord命令测试脚本 - 验证VPS部署版本中的命令功能
"""

import os
import sys
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limiter_functions():
    """测试限制器相关功能"""
    print("🔍 测试用户限制功能...")
    
    try:
        from rate_limiter import RateLimiter
        
        # 创建限制器实例
        limiter = RateLimiter(daily_limit=3)
        print("✅ RateLimiter实例创建成功")
        
        # 测试豁免用户功能
        test_user_id = "1145170623354638418"  # easton的ID
        test_username = "TestUser"
        
        # 测试添加豁免用户
        success = limiter.add_exempt_user(
            user_id=test_user_id,
            username=test_username,
            reason="测试豁免用户",
            added_by="admin_test"
        )
        
        if success:
            print("✅ 豁免用户添加成功")
        else:
            print("⚠️ 豁免用户可能已存在")
        
        # 测试查询豁免用户
        exempt_users = limiter.list_exempt_users()
        print(f"📋 豁免用户列表: {len(exempt_users)} 个用户")
        for user in exempt_users:
            print(f"   - {user['username']} ({user['user_id']}): {user['reason']}")
        
        # 测试用户限制检查
        can_request, current, remaining = limiter.check_user_limit(test_user_id, test_username)
        print(f"📊 用户限制检查: 可请求={can_request}, 当前={current}, 剩余={remaining}")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户限制功能测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接和表结构"""
    print("🔍 测试数据库连接...")
    
    try:
        from models import get_db_session, UserRequestLimit, ExemptUser
        
        db = get_db_session()
        
        # 测试基本连接
        result = db.execute("SELECT 1").fetchone()
        if result and result[0] == 1:
            print("✅ 数据库连接正常")
        
        # 检查表结构
        tables = db.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall()
        table_names = [table[0] for table in tables]
        print(f"📋 数据库表: {table_names}")
        
        # 检查豁免用户表数据
        exempt_count = db.query(ExemptUser).count()
        print(f"👥 豁免用户数量: {exempt_count}")
        
        # 检查请求记录表数据  
        today = datetime.now().date()
        request_count = db.query(UserRequestLimit).filter(UserRequestLimit.request_date == today).count()
        print(f"📊 今日请求记录: {request_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def print_command_help():
    """打印命令使用帮助"""
    print("\n📋 Discord命令使用指南:")
    print("=" * 50)
    print("🔧 管理员命令（仅管理员可用）:")
    print("   !vip_add <用户ID> [原因]     - 添加豁免用户")
    print("   !vip_remove <用户ID>        - 移除豁免用户") 
    print("   !vip_list                   - 查看豁免用户列表")
    print("   !exempt_add <用户ID> [原因]  - 添加豁免用户（别名）")
    print("   !exempt_remove <用户ID>     - 移除豁免用户（别名）")
    print("   !exempt_list                - 查看豁免用户列表（别名）")
    print("")
    print("👤 用户命令（所有用户可用）:")
    print("   !quota                      - 查看自己的每日配额状态")
    print("   !ping                       - 测试机器人响应")
    print("   !test                       - 基本测试命令")
    print("")
    print("💡 管理员用户ID列表:")
    print("   1145170623354638418  (easton)")
    print("   1307107680560873524  (TestAdmin)")
    print("   1257109321947287648  (easmartalgo)")
    print("")
    print("📝 使用示例:")
    print("   !vip_add 1145170623354638418 VIP客户")
    print("   !quota")
    print("   !vip_list")

def main():
    """主测试函数"""
    print("🚀 Discord命令功能测试")
    print("=" * 50)
    
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL环境变量未设置")
        sys.exit(1)
    
    # 运行测试
    tests_passed = 0
    tests_total = 2
    
    if test_database_connection():
        tests_passed += 1
        
    if test_rate_limiter_functions():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {tests_passed}/{tests_total} 通过")
    
    if tests_passed == tests_total:
        print("🎉 所有测试通过！Discord命令功能准备就绪")
        print_command_help()
        print("\n✅ 您现在可以在Discord中测试以下命令:")
        print("   1. 在Discord中发送: !quota")
        print("   2. 在Discord中发送: !vip_list")
        print("   3. 管理员发送: !vip_add 1145170623354638418 测试用户")
        return True
    else:
        print("⚠️ 有测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)