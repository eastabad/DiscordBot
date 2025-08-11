"""
频道清理服务模块
自动删除监控频道中的无用消息，保持频道整洁
"""

import asyncio
import logging
import discord
from datetime import datetime, timedelta
import re
from typing import List, Set

class ChannelCleaner:
    """频道清理服务类"""
    
    def __init__(self, bot, config):
        """初始化频道清理服务"""
        self.bot = bot
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 无用消息模式匹配
        self.useless_patterns = [
            r'.*completed.*workflow.*',  # 工作流完成消息
            r'.*workflow.*started.*',    # 工作流启动消息
            r'.*workflow.*stopped.*',    # 工作流停止消息
            r'.*deployment.*successful.*', # 部署成功消息
            r'.*build.*completed.*',     # 构建完成消息
            r'.*test.*passed.*',         # 测试通过消息
            r'.*error.*resolved.*',      # 错误解决消息
            r'.*backup.*created.*',      # 备份创建消息
            r'.*maintenance.*complete.*', # 维护完成消息
            r'.*update.*installed.*',    # 更新安装消息
            r'.*restart.*completed.*',   # 重启完成消息
            r'.*sync.*finished.*',       # 同步完成消息
            r'.*job.*finished.*',        # 任务完成消息
            r'.*process.*completed.*',   # 进程完成消息
            r'.*operation.*successful.*', # 操作成功消息
            r'.*task.*done.*',           # 任务完成消息
            r'.*status.*ok.*',           # 状态正常消息
            r'.*health.*check.*passed.*', # 健康检查通过消息
            r'.*connection.*established.*', # 连接建立消息
            r'.*service.*online.*',      # 服务在线消息
            r'.*system.*ready.*',        # 系统就绪消息
            r'[✅❌⚠️]*\s*(完成|成功|失败|错误|警告).*', # 状态表情符号消息
            r'.*\b(completed|finished|done|success|failed|error|warning)\b.*', # 英文状态词
        ]
        
        # 保留有用消息模式
        self.useful_patterns = [
            r'.*[A-Z]{2,5}[,，]\s*\d+[smhdwMy].*', # 股票命令格式
            r'.*预测.*趋势.*',                      # 预测请求
            r'.*分析.*图表.*',                      # 图表分析请求
            r'.*!vip.*',                           # VIP管理命令
            r'.*!quota.*',                         # 配额查询命令
            r'.*!help.*',                          # 帮助命令
            r'.*问题.*',                           # 问题咨询
            r'.*疑问.*',                           # 疑问询问
            r'.*怎么.*',                           # 操作询问
            r'.*如何.*',                           # 方法询问
            r'.*@.*',                              # 提及消息
        ]
        
        # 清理计划任务状态
        self.cleanup_task = None
        self.is_cleaning = False
        
    async def start_daily_cleanup(self):
        """启动每日清理任务"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._daily_cleanup_loop())
            self.logger.info("每日频道清理任务已启动")
    
    async def stop_daily_cleanup(self):
        """停止每日清理任务"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.logger.info("每日频道清理任务已停止")
    
    async def _daily_cleanup_loop(self):
        """每日清理循环"""
        while True:
            try:
                # 等待到下一个清理时间 (每天凌晨2点)
                now = datetime.now()
                tomorrow_2am = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
                wait_seconds = (tomorrow_2am - now).total_seconds()
                
                self.logger.info(f"下次清理时间: {tomorrow_2am}, 等待 {wait_seconds/3600:.1f} 小时")
                await asyncio.sleep(wait_seconds)
                
                # 执行清理
                await self.cleanup_today_messages()
                
            except asyncio.CancelledError:
                self.logger.info("每日清理任务被取消")
                break
            except Exception as e:
                self.logger.error(f"每日清理任务发生错误: {e}")
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)
    
    async def cleanup_today_messages(self):
        """清理今天的无用消息"""
        if self.is_cleaning:
            self.logger.warning("清理任务正在进行中，跳过")
            return
        
        self.is_cleaning = True
        try:
            self.logger.info("开始清理今天的无用消息")
            
            # 获取监控频道列表
            monitor_channels = self._get_monitor_channels()
            
            total_deleted = 0
            for channel_id in monitor_channels:
                try:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel is None:
                        self.logger.warning(f"找不到频道: {channel_id}")
                        continue
                    
                    deleted_count = await self._cleanup_channel_today(channel)
                    total_deleted += deleted_count
                    
                    # 频道间稍作休息，避免API限制
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"清理频道 {channel_id} 时发生错误: {e}")
            
            self.logger.info(f"清理完成，共删除 {total_deleted} 条无用消息")
            
        except Exception as e:
            self.logger.error(f"清理任务发生错误: {e}")
        finally:
            self.is_cleaning = False
    
    async def _cleanup_channel_today(self, channel) -> int:
        """清理指定频道今天的无用消息"""
        deleted_count = 0
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # 获取今天的消息
            async for message in channel.history(after=today_start, limit=1000):
                try:
                    # 跳过机器人自己的消息
                    if message.author == self.bot.user:
                        continue
                    
                    # 跳过置顶消息
                    if message.pinned:
                        continue
                    
                    # 检查是否为无用消息
                    if await self._is_useless_message(message):
                        await message.delete()
                        deleted_count += 1
                        self.logger.debug(f"删除无用消息: {message.content[:50]}...")
                        
                        # 避免删除过快触发API限制
                        await asyncio.sleep(0.5)
                        
                except discord.NotFound:
                    # 消息已被删除，跳过
                    continue
                except discord.Forbidden:
                    self.logger.warning(f"没有权限删除消息: {message.id}")
                    continue
                except Exception as e:
                    self.logger.error(f"删除消息时发生错误: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取频道消息时发生错误: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"频道 {channel.name} 清理完成，删除了 {deleted_count} 条无用消息")
        
        return deleted_count
    
    async def _is_useless_message(self, message) -> bool:
        """判断消息是否为无用消息"""
        # 删除所有用户消息（非机器人消息）
        # 只保留机器人自己发送的消息
        return not message.author.bot
    
    def _get_monitor_channels(self) -> List[str]:
        """获取监控频道列表"""
        monitor_channels = []
        
        # 支持多频道配置
        if hasattr(self.config, 'monitor_channel_ids') and self.config.monitor_channel_ids:
            # 检查是否为列表格式
            if isinstance(self.config.monitor_channel_ids, list):
                monitor_channels.extend(self.config.monitor_channel_ids)
            else:
                # 字符串格式: "id1,id2,id3"
                channel_ids = [cid.strip() for cid in self.config.monitor_channel_ids.split(',')]
                monitor_channels.extend(channel_ids)
        elif hasattr(self.config, 'monitor_channel_id') and self.config.monitor_channel_id:
            # 单频道格式 (向后兼容)
            monitor_channels.append(self.config.monitor_channel_id)
        
        return monitor_channels
    
    async def manual_cleanup(self, channel_id: str = None, days: int = 1):
        """手动清理指定频道的消息"""
        try:
            if channel_id:
                # 清理指定频道
                channel = self.bot.get_channel(int(channel_id))
                if channel is None:
                    self.logger.error(f"找不到频道: {channel_id}")
                    return 0
                
                deleted_count = await self._cleanup_channel_days(channel, days)
                self.logger.info(f"手动清理频道 {channel.name} 完成，删除了 {deleted_count} 条消息")
                return deleted_count
            else:
                # 清理所有监控频道
                monitor_channels = self._get_monitor_channels()
                total_deleted = 0
                
                for cid in monitor_channels:
                    try:
                        channel = self.bot.get_channel(int(cid.strip()))
                        if channel:
                            deleted_count = await self._cleanup_channel_days(channel, days)
                            total_deleted += deleted_count
                            await asyncio.sleep(1)
                        else:
                            self.logger.warning(f"找不到频道: {cid}")
                    except ValueError as e:
                        self.logger.error(f"无效的频道ID: {cid}, 错误: {e}")
                        continue
                
                self.logger.info(f"手动清理所有监控频道完成，共删除了 {total_deleted} 条消息")
                return total_deleted
                
        except Exception as e:
            self.logger.error(f"手动清理时发生错误: {e}")
            return 0
    
    async def _cleanup_channel_days(self, channel, days: int) -> int:
        """清理指定频道指定天数的无用消息"""
        deleted_count = 0
        start_time = datetime.now() - timedelta(days=days)
        
        try:
            async for message in channel.history(after=start_time, limit=2000):
                try:
                    if message.author == self.bot.user:
                        continue
                    
                    if message.pinned:
                        continue
                    
                    if await self._is_useless_message(message):
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(0.3)
                        
                except (discord.NotFound, discord.Forbidden):
                    continue
                except Exception as e:
                    self.logger.error(f"删除消息时发生错误: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"获取频道消息时发生错误: {e}")
        
        return deleted_count
    
    async def get_cleanup_stats(self) -> dict:
        """获取清理统计信息"""
        stats = {
            'is_running': self.cleanup_task and not self.cleanup_task.done(),
            'is_cleaning': self.is_cleaning,
            'monitor_channels': len(self._get_monitor_channels()),
            'next_cleanup': None
        }
        
        if stats['is_running']:
            now = datetime.now()
            tomorrow_2am = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
            if now.hour >= 2:
                stats['next_cleanup'] = tomorrow_2am
            else:
                today_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
                stats['next_cleanup'] = today_2am
        
        return stats