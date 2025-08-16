#!/usr/bin/env python3
"""
数据库连接检查和修复脚本
解决VPS部署中用户限制功能失效问题
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from models import Base, UserRequestLimit, ExemptUser, TradingViewData, ReportCache, get_db_session, create_tables

def check_database_connection():
    """检查数据库连接"""
    print("🔍 检查数据库连接...")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 错误: DATABASE_URL环境变量未设置")
        print("请检查.env文件或docker-compose.yml配置")
        return False
    
    print(f"数据库URL: {database_url[:20]}...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            return True
    except OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return False

def check_tables_exist():
    """检查数据库表是否存在"""
    print("\n🔍 检查数据库表...")
    
    try:
        db = get_db_session()
        
        # 检查用户请求限制表
        try:
            count = db.query(UserRequestLimit).count()
            print(f"✅ user_request_limits表存在，共{count}条记录")
        except Exception as e:
            print(f"❌ user_request_limits表不存在或有问题: {e}")
            return False
        
        # 检查豁免用户表
        try:
            count = db.query(ExemptUser).count()
            print(f"✅ exempt_users表存在，共{count}条记录")
        except Exception as e:
            print(f"❌ exempt_users表不存在或有问题: {e}")
            return False
        
        # 检查TradingView数据表
        try:
            count = db.query(TradingViewData).count()
            print(f"✅ tradingview_data表存在，共{count}条记录")
        except Exception as e:
            print(f"❌ tradingview_data表不存在或有问题: {e}")
            return False
        
        # 检查报告缓存表
        try:
            count = db.query(ReportCache).count()
            print(f"✅ report_cache表存在，共{count}条记录")
        except Exception as e:
            print(f"❌ report_cache表不存在或有问题: {e}")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查表时出错: {e}")
        return False

def create_missing_tables():
    """创建缺失的数据库表"""
    print("\n🔧 创建数据库表...")
    
    try:
        create_tables()
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        return False

def test_rate_limiter():
    """测试用户限制功能"""
    print("\n🧪 测试用户限制功能...")
    
    try:
        from rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter()
        
        # 测试普通用户
        test_user_id = "123456789"
        test_username = "TestUser"
        
        can_request, current_count, remaining = rate_limiter.check_user_limit(test_user_id, test_username)
        print(f"✅ 用户限制功能测试成功: 可请求={can_request}, 当前={current_count}, 剩余={remaining}")
        
        # 记录请求
        success = rate_limiter.record_request(test_user_id, test_username)
        print(f"✅ 请求记录功能测试成功: {success}")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户限制功能测试失败: {e}")
        return False

def show_database_status():
    """显示数据库状态信息"""
    print("\n📊 数据库状态信息:")
    
    try:
        db = get_db_session()
        
        # 用户请求统计
        total_users = db.query(UserRequestLimit.user_id).distinct().count()
        total_requests = db.query(UserRequestLimit).count()
        print(f"总用户数: {total_users}")
        print(f"总请求记录: {total_requests}")
        
        # 豁免用户统计
        exempt_count = db.query(ExemptUser).count()
        print(f"豁免用户数: {exempt_count}")
        
        # TradingView数据统计
        try:
            tradingview_count = db.query(TradingViewData).count()
            signal_count = db.query(TradingViewData).filter_by(data_type='signal').count()
            trade_count = db.query(TradingViewData).filter_by(data_type='trade').count()
            close_count = db.query(TradingViewData).filter_by(data_type='close').count()
            print(f"TradingView数据: 总计{tradingview_count} (signal:{signal_count}, trade:{trade_count}, close:{close_count})")
        except Exception as e:
            print(f"TradingView数据统计失败: {e}")
        
        # 缓存统计
        try:
            cache_count = db.query(ReportCache).count()
            valid_cache_count = db.query(ReportCache).filter_by(is_valid=True).count()
            print(f"报告缓存: 总计{cache_count} (有效:{valid_cache_count})")
        except Exception as e:
            print(f"缓存数据统计失败: {e}")
        
        # 最近记录
        recent_record = db.query(UserRequestLimit).order_by(UserRequestLimit.last_request_time.desc()).first()
        if recent_record:
            print(f"最近请求: {recent_record.username} ({recent_record.last_request_time})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 获取数据库状态失败: {e}")

def fix_database_issues():
    """修复数据库问题"""
    print("🔧 开始修复数据库问题...")
    
    success = True
    
    # 1. 检查连接
    if not check_database_connection():
        print("\n❌ 数据库连接失败，请检查:")
        print("1. Docker容器是否正在运行: docker-compose ps")
        print("2. 数据库服务是否启动: docker-compose logs db")
        print("3. DATABASE_URL是否正确配置")
        return False
    
    # 2. 检查和创建表
    if not check_tables_exist():
        print("\n🔧 尝试创建缺失的表...")
        if not create_missing_tables():
            success = False
        else:
            # 重新检查
            if check_tables_exist():
                print("✅ 表创建成功")
            else:
                print("❌ 表创建后仍有问题")
                success = False
    
    # 3. 测试功能
    if success:
        if not test_rate_limiter():
            success = False
    
    # 4. 显示状态
    if success:
        show_database_status()
    
    return success

def main():
    """主函数"""
    print("🚀 Discord机器人数据库修复工具")
    print("=" * 40)
    
    if fix_database_issues():
        print("\n✅ 数据库修复完成！用户限制功能应该正常工作了。")
        print("\n建议测试:")
        print("1. 在Discord中使用 !quota 查看配额")
        print("2. 连续发送多个股票查询测试限制")
        print("3. 使用 !exempt_add 测试豁免功能")
    else:
        print("\n❌ 数据库修复失败，请查看错误信息并手动修复。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())