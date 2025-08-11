"""
用户请求频率限制管理
处理每日请求限制检查和更新
"""
import logging
from datetime import datetime, timezone, date
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import UserRequestLimit, get_db_session

class RateLimiter:
    """用户请求频率限制管理器"""
    
    def __init__(self, daily_limit: int = 3):
        self.daily_limit = daily_limit
        self.logger = logging.getLogger(__name__)
    
    def check_user_limit(self, user_id: str, username: str) -> Tuple[bool, int, int]:
        """
        检查用户是否超过每日请求限制
        
        Args:
            user_id: Discord用户ID
            username: Discord用户名
            
        Returns:
            Tuple[bool, int, int]: (是否允许请求, 当前使用次数, 剩余次数)
        """
        try:
            db = get_db_session()
            today = date.today()
            
            # 查找用户今日记录
            user_record = db.query(UserRequestLimit).filter(
                and_(
                    UserRequestLimit.user_id == user_id,
                    UserRequestLimit.request_date == today
                )
            ).first()
            
            if not user_record:
                # 新用户或新的一天，创建记录
                user_record = UserRequestLimit(
                    user_id=user_id,
                    username=username,
                    request_date=today,
                    request_count=0,
                    last_request_time=datetime.now(timezone.utc)
                )
                db.add(user_record)
                db.commit()
                current_count = 0
            else:
                current_count = user_record.request_count
            
            # 检查是否超过限制
            remaining = max(0, self.daily_limit - current_count)
            can_request = current_count < self.daily_limit
            
            self.logger.info(f"用户 {username} ({user_id}) 今日请求: {current_count}/{self.daily_limit}, 剩余: {remaining}")
            
            db.close()
            return can_request, current_count, remaining
            
        except Exception as e:
            self.logger.error(f"检查用户限制时发生错误: {e}")
            # 发生错误时允许请求，避免阻塞服务
            return True, 0, self.daily_limit
    
    def record_request(self, user_id: str, username: str) -> bool:
        """
        记录用户请求，增加计数
        
        Args:
            user_id: Discord用户ID
            username: Discord用户名
            
        Returns:
            bool: 是否成功记录
        """
        try:
            db = get_db_session()
            today = date.today()
            
            # 查找用户今日记录
            user_record = db.query(UserRequestLimit).filter(
                and_(
                    UserRequestLimit.user_id == user_id,
                    UserRequestLimit.request_date == today
                )
            ).first()
            
            if user_record:
                # 更新现有记录
                user_record.request_count += 1
                user_record.last_request_time = datetime.now(timezone.utc)
                user_record.username = username  # 更新用户名（可能变化）
            else:
                # 创建新记录
                user_record = UserRequestLimit(
                    user_id=user_id,
                    username=username,
                    request_date=today,
                    request_count=1,
                    last_request_time=datetime.now(timezone.utc)
                )
                db.add(user_record)
            
            db.commit()
            self.logger.info(f"记录用户 {username} 请求，今日总计: {user_record.request_count}")
            
            db.close()
            return True
            
        except Exception as e:
            self.logger.error(f"记录用户请求时发生错误: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Optional[dict]:
        """
        获取用户今日请求统计
        
        Args:
            user_id: Discord用户ID
            
        Returns:
            dict: 用户统计信息或None
        """
        try:
            db = get_db_session()
            today = date.today()
            
            user_record = db.query(UserRequestLimit).filter(
                and_(
                    UserRequestLimit.user_id == user_id,
                    UserRequestLimit.request_date == today
                )
            ).first()
            
            if user_record:
                stats = {
                    'user_id': user_record.user_id,
                    'username': user_record.username,
                    'date': user_record.request_date.isoformat(),
                    'request_count': user_record.request_count,
                    'limit': self.daily_limit,
                    'remaining': max(0, self.daily_limit - user_record.request_count),
                    'last_request': user_record.last_request_time.isoformat()
                }
            else:
                stats = {
                    'user_id': user_id,
                    'username': 'Unknown',
                    'date': today.isoformat(),
                    'request_count': 0,
                    'limit': self.daily_limit,
                    'remaining': self.daily_limit,
                    'last_request': None
                }
            
            db.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"获取用户统计时发生错误: {e}")
            return None
    
    def reset_user_limit(self, user_id: str) -> bool:
        """
        重置用户今日限制（管理员功能）
        
        Args:
            user_id: Discord用户ID
            
        Returns:
            bool: 是否成功重置
        """
        try:
            db = get_db_session()
            today = date.today()
            
            user_record = db.query(UserRequestLimit).filter(
                and_(
                    UserRequestLimit.user_id == user_id,
                    UserRequestLimit.request_date == today
                )
            ).first()
            
            if user_record:
                user_record.request_count = 0
                user_record.updated_at = datetime.now(timezone.utc)
                db.commit()
                self.logger.info(f"重置用户 {user_id} 今日限制")
                
            db.close()
            return True
            
        except Exception as e:
            self.logger.error(f"重置用户限制时发生错误: {e}")
            return False