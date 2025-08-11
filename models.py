"""
数据库模型定义
用于跟踪用户每日请求限制和使用统计
"""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date
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

# 数据库连接设置
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

def get_db_session():
    """获取数据库会话"""
    return SessionLocal()

if __name__ == "__main__":
    # 创建表
    create_tables()