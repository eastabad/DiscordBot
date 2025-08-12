"""
用户请求频率限制管理
处理每日请求限制检查和更新
"""
import os
import logging
from datetime import datetime, timezone, date
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import UserRequestLimit, ExemptUser, get_db_session

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
            
            # 检查用户是否在豁免列表中
            exempt_user = db.query(ExemptUser).filter(ExemptUser.user_id == user_id).first()
            if exempt_user:
                self.logger.info(f"用户 {username} ({user_id}) 在豁免列表中，无限制")
                db.close()
                return True, 0, 999  # 豁免用户返回999剩余次数表示无限制
            
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
            self.logger.error(f"数据库URL: {os.environ.get('DATABASE_URL', 'NOT_SET')}")
            try:
                db.close()
            except:
                pass
            # 发生错误时，为了安全起见，拒绝请求
            return False, 0, 0
    
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
            self.logger.error(f"数据库URL: {os.environ.get('DATABASE_URL', 'NOT_SET')}")
            try:
                db.close()
            except:
                pass
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
    
    def add_exempt_user(self, user_id: str, username: str, reason: str = "管理员豁免", added_by: str = "system") -> bool:
        """
        添加豁免用户
        
        Args:
            user_id: Discord用户ID
            username: Discord用户名  
            reason: 豁免原因
            added_by: 添加者ID
            
        Returns:
            bool: 是否成功添加
        """
        try:
            db = get_db_session()
            
            # 检查用户是否已经在豁免列表中
            existing = db.query(ExemptUser).filter(ExemptUser.user_id == user_id).first()
            if existing:
                self.logger.warning(f"用户 {username} ({user_id}) 已在豁免列表中")
                db.close()
                return False
            
            # 添加新的豁免用户
            exempt_user = ExemptUser(
                user_id=user_id,
                username=username,
                reason=reason,
                added_by=added_by
            )
            db.add(exempt_user)
            db.commit()
            
            self.logger.info(f"成功添加豁免用户: {username} ({user_id}), 原因: {reason}")
            db.close()
            return True
            
        except Exception as e:
            self.logger.error(f"添加豁免用户时发生错误: {e}")
            return False
    
    def remove_exempt_user(self, user_id: str) -> bool:
        """
        移除豁免用户
        
        Args:
            user_id: Discord用户ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            db = get_db_session()
            
            # 查找并删除豁免用户
            exempt_user = db.query(ExemptUser).filter(ExemptUser.user_id == user_id).first()
            if exempt_user:
                username = exempt_user.username
                db.delete(exempt_user)
                db.commit()
                self.logger.info(f"成功移除豁免用户: {username} ({user_id})")
                db.close()
                return True
            else:
                self.logger.warning(f"用户 {user_id} 不在豁免列表中")
                db.close()
                return False
                
        except Exception as e:
            self.logger.error(f"移除豁免用户时发生错误: {e}")
            return False
    
    def list_exempt_users(self) -> list:
        """
        获取所有豁免用户列表
        
        Returns:
            list: 豁免用户信息列表
        """
        try:
            db = get_db_session()
            exempt_users = db.query(ExemptUser).all()
            
            result = []
            for user in exempt_users:
                result.append({
                    'user_id': user.user_id,
                    'username': user.username,
                    'reason': user.reason,
                    'added_by': user.added_by,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            db.close()
            return result
            
        except Exception as e:
            self.logger.error(f"获取豁免用户列表时发生错误: {e}")
            return []