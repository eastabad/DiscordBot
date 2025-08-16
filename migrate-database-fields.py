#!/usr/bin/env python3
"""
数据库字段迁移脚本 - 今日更新专用
添加新的评级字段和ReportCache表
用于2025-08-16的VPS更新
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

def get_database_url():
    """获取数据库URL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 错误: DATABASE_URL环境变量未设置")
        return None
    return database_url

def check_column_exists(engine, table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
        return False

def check_table_exists(engine, table_name):
    """检查表是否存在"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception:
        return False

def add_missing_columns(engine):
    """添加缺失的列到tradingview_data表"""
    print("🔧 检查并添加新评级字段...")
    
    # 需要添加的新字段
    new_columns = [
        ('bullish_osc_rating', 'FLOAT'),
        ('bullish_trend_rating', 'FLOAT'),
        ('bearish_osc_rating', 'FLOAT'),
        ('bearish_trend_rating', 'FLOAT'),
        ('current_timeframe', 'VARCHAR(10)')
    ]
    
    added_count = 0
    
    for column_name, column_type in new_columns:
        if not check_column_exists(engine, 'tradingview_data', column_name):
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE tradingview_data ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                print(f"✅ 添加列: {column_name}")
                added_count += 1
            except Exception as e:
                print(f"❌ 添加列{column_name}失败: {e}")
        else:
            print(f"✅ 列已存在: {column_name}")
    
    if added_count > 0:
        print(f"✅ 成功添加{added_count}个新字段")
    else:
        print("✅ 所有字段都已存在")

def create_report_cache_table(engine):
    """创建report_cache表"""
    print("🔧 检查并创建report_cache表...")
    
    if check_table_exists(engine, 'report_cache'):
        print("✅ report_cache表已存在")
        return
    
    create_table_sql = """
    CREATE TABLE report_cache (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        timeframe VARCHAR(10) NOT NULL,
        report_content TEXT NOT NULL,
        report_type VARCHAR(20) DEFAULT 'enhanced' NOT NULL,
        based_on_signal_id INTEGER,
        based_on_trade_id INTEGER,
        data_timestamp TIMESTAMP NOT NULL,
        is_valid BOOLEAN DEFAULT TRUE NOT NULL,
        hit_count INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        expires_at TIMESTAMP
    );
    
    CREATE INDEX idx_report_cache_symbol ON report_cache(symbol);
    CREATE INDEX idx_report_cache_timeframe ON report_cache(timeframe);
    CREATE INDEX idx_report_cache_data_timestamp ON report_cache(data_timestamp);
    CREATE INDEX idx_report_cache_expires_at ON report_cache(expires_at);
    """
    
    try:
        with engine.connect() as conn:
            # 分别执行每个语句
            statements = create_table_sql.strip().split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement.strip()))
            conn.commit()
        print("✅ report_cache表创建成功")
    except Exception as e:
        print(f"❌ 创建report_cache表失败: {e}")

def update_tradingview_data_structure(engine):
    """更新tradingview_data表结构"""
    print("🔧 更新tradingview_data表结构...")
    
    # 检查并添加data_type字段（如果不存在）
    if not check_column_exists(engine, 'tradingview_data', 'data_type'):
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE tradingview_data ADD COLUMN data_type VARCHAR(10) DEFAULT 'signal'"))
                conn.execute(text("CREATE INDEX idx_tradingview_data_type ON tradingview_data(data_type)"))
                conn.commit()
            print("✅ 添加data_type字段")
        except Exception as e:
            print(f"❌ 添加data_type字段失败: {e}")
    else:
        print("✅ data_type字段已存在")

def verify_migration(engine):
    """验证迁移结果"""
    print("🔍 验证迁移结果...")
    
    try:
        # 验证新字段
        inspector = inspect(engine)
        tradingview_columns = inspector.get_columns('tradingview_data')
        column_names = [col['name'] for col in tradingview_columns]
        
        required_fields = [
            'bullish_osc_rating', 'bullish_trend_rating', 
            'bearish_osc_rating', 'bearish_trend_rating', 
            'current_timeframe', 'data_type'
        ]
        
        missing_fields = [field for field in required_fields if field not in column_names]
        
        if missing_fields:
            print(f"❌ 缺失字段: {missing_fields}")
            return False
        else:
            print("✅ 所有必需字段都存在")
        
        # 验证report_cache表
        if check_table_exists(engine, 'report_cache'):
            print("✅ report_cache表存在")
        else:
            print("❌ report_cache表不存在")
            return False
        
        # 验证索引
        indexes = inspector.get_indexes('tradingview_data')
        index_names = [idx['name'] for idx in indexes]
        
        print(f"✅ tradingview_data表有{len(tradingview_columns)}列")
        print(f"✅ tradingview_data表有{len(indexes)}个索引")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def show_migration_summary(engine):
    """显示迁移总结"""
    print("\n📊 迁移后数据库状态:")
    
    try:
        with engine.connect() as conn:
            # TradingView数据统计
            result = conn.execute(text("SELECT COUNT(*) FROM tradingview_data"))
            total_count = result.scalar()
            
            result = conn.execute(text("SELECT data_type, COUNT(*) FROM tradingview_data GROUP BY data_type"))
            type_counts = dict(result.fetchall())
            
            print(f"TradingView数据: 总计{total_count}条")
            for data_type, count in type_counts.items():
                print(f"  - {data_type}: {count}条")
            
            # 缓存表统计
            if check_table_exists(engine, 'report_cache'):
                result = conn.execute(text("SELECT COUNT(*) FROM report_cache"))
                cache_count = result.scalar()
                print(f"报告缓存: {cache_count}条")
            
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")

def main():
    """主函数"""
    print("🚀 数据库字段迁移工具 - 今日更新专用")
    print("=" * 50)
    print("📅 迁移日期: 2025-08-16")
    print("🎯 目标: 添加评级字段和缓存表")
    print()
    
    # 获取数据库连接
    database_url = get_database_url()
    if not database_url:
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
        
        # 执行迁移
        print("\n开始数据库迁移...")
        
        # 1. 更新tradingview_data表结构
        update_tradingview_data_structure(engine)
        
        # 2. 添加新的评级字段
        add_missing_columns(engine)
        
        # 3. 创建缓存表
        create_report_cache_table(engine)
        
        # 4. 验证迁移
        if verify_migration(engine):
            print("\n✅ 数据库迁移成功完成!")
            
            # 5. 显示总结
            show_migration_summary(engine)
            
            print("\n🎉 迁移完成，系统现在支持:")
            print("   ✅ 5个新评级字段 (bullish/bearish rating)")
            print("   ✅ 智能报告缓存系统")
            print("   ✅ 3种数据类型分离 (signal/trade/close)")
            print("   ✅ 优化的数据库索引")
            
        else:
            print("\n❌ 数据库迁移验证失败")
            sys.exit(1)
            
    except OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 迁移过程中出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()