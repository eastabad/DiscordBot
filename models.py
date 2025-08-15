"""
数据库模型定义
用于跟踪用户每日请求限制和使用统计，以及TradingView数据存储
"""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, text, Text, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class UserRequestLimit(Base):
    """用户每日请求限制跟踪表"""
    __tablename__ = 'user_request_limits'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)  # Discord用户ID
    username = Column(String(100), nullable=False)  # Discord用户名
    request_date = Column(Date, nullable=False, index=True)  # 请求日期
    request_count = Column(Integer, default=0, nullable=False)  # 当日请求次数
    last_request_time = Column(DateTime, default=func.now(), nullable=False)  # 最后请求时间
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserRequestLimit(user_id='{self.user_id}', date='{self.request_date}', count={self.request_count})>"


class ExemptUser(Base):
    """豁免用户表 - 这些用户不受每日请求限制约束"""
    __tablename__ = 'exempt_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True, index=True)  # Discord用户ID
    username = Column(String(100), nullable=False)  # Discord用户名
    reason = Column(String(200), nullable=True)  # 豁免原因
    added_by = Column(String(50), nullable=True)  # 添加者ID
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ExemptUser(user_id='{self.user_id}', username='{self.username}', reason='{self.reason}')>"


class TradingViewData(Base):
    """TradingView推送数据存储表"""
    __tablename__ = 'tradingview_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)  # 股票代码，如 AAPL
    timeframe = Column(String(10), nullable=False, index=True)  # 时间框架，如 15m, 1h, 4h
    
    # TradingView推送的原始数据字段
    timestamp = Column(DateTime, nullable=False, index=True)  # 数据时间戳
    open_price = Column(Float, nullable=True)  # 开盘价
    high_price = Column(Float, nullable=True)  # 最高价
    low_price = Column(Float, nullable=True)   # 最低价
    close_price = Column(Float, nullable=True) # 收盘价
    volume = Column(Float, nullable=True)      # 成交量
    
    # 技术指标数据
    rsi = Column(Float, nullable=True)         # RSI指标
    macd = Column(Float, nullable=True)        # MACD指标
    sma_20 = Column(Float, nullable=True)      # 20日简单移动平均线
    sma_50 = Column(Float, nullable=True)      # 50日简单移动平均线
    
    # 原始JSON数据存储（用于保存完整信息）
    raw_data = Column(Text, nullable=True)     # 原始JSON字符串
    
    # 系统字段
    received_at = Column(DateTime, default=func.now(), nullable=False)  # 接收时间
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<TradingViewData(symbol='{self.symbol}', timeframe='{self.timeframe}', timestamp='{self.timestamp}', close='{self.close_price}')>"

# 数据库连接设置
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL环境变量未设置，用户限制功能将无法工作")

try:
    # 创建引擎，添加连接池配置
    engine = create_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,  # 验证连接有效性
        pool_recycle=300,    # 5分钟回收连接
        connect_args={"connect_timeout": 10}  # 10秒连接超时
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 测试数据库连接
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ 数据库连接成功")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print(f"DATABASE_URL: {DATABASE_URL}")
    raise

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

def get_db_session():
    """获取数据库会话"""
    try:
        session = SessionLocal()
        # 测试连接
        session.execute(text("SELECT 1"))
        return session
    except Exception as e:
        print(f"❌ 获取数据库会话失败: {e}")
        raise

if __name__ == "__main__":
    # 创建表
    create_tables()