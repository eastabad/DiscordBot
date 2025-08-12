"""
Webhook处理器
负责将消息数据发送到指定的webhook URL
"""

import aiohttp
import asyncio
import logging
from datetime import datetime

class WebhookHandler:
    """Webhook处理器类"""
    
    def __init__(self, webhook_url, max_retries=3, timeout=30):
        """初始化webhook处理器"""
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    async def send_message(self, message_data):
        """发送消息到webhook"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # 构建webhook负载
                    payload = self.build_webhook_payload(message_data)
                    
                    # 发送请求
                    async with session.post(
                        self.webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        
                        if response.status == 200:
                            self.logger.info(f'成功发送webhook消息 (尝试 {attempt + 1})')
                            return True
                        else:
                            error_text = await response.text()
                            self.logger.warning(
                                f'Webhook请求失败 (尝试 {attempt + 1}): '
                                f'状态码 {response.status}, 响应: {error_text}'
                            )
                            
            except asyncio.TimeoutError:
                self.logger.warning(f'Webhook请求超时 (尝试 {attempt + 1})')
            except aiohttp.ClientError as e:
                self.logger.warning(f'Webhook客户端错误 (尝试 {attempt + 1}): {e}')
            except Exception as e:
                self.logger.error(f'Webhook请求异常 (尝试 {attempt + 1}): {e}')
                
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                self.logger.info(f'等待 {wait_time} 秒后重试...')
                await asyncio.sleep(wait_time)
                
        self.logger.error(f'Webhook发送失败，已尝试 {self.max_retries} 次')
        return False
        
    def build_webhook_payload(self, message_data):
        """构建详细的webhook负载"""
        # 格式化消息内容
        content_preview = self.truncate_text(message_data.get('content', ''), 100)
        
        # 构建详细信息负载
        payload = {
            'timestamp': message_data.get('timestamp'),
            'event_type': 'discord_mention',
            'version': '2.0',  # 版本号，表示详细信息格式
            'data': {
                'message': {
                    'id': message_data.get('message_id'),
                    'content': message_data.get('content'),
                    'content_preview': content_preview,
                    'created_at': message_data.get('created_at'),
                    'edited_at': message_data.get('edited_at'),
                    'jump_url': message_data.get('jump_url')
                },
                'channel': self.format_channel_info(message_data.get('channel', {})),
                'guild': self.format_guild_info(message_data.get('guild', {})),
                'author': self.format_author_info(message_data.get('author', {})),
                'attachments': message_data.get('attachments', []),
                'embeds': message_data.get('embeds', []),
                'mentions': message_data.get('mentions', [])
            },
            'metadata': {
                'bot_name': 'Discord转发机器人 v2.0',
                'version': '2.0.0',
                'processed_at': datetime.now().isoformat(),
                'enhanced_data': True
            }
        }
        
        # 添加统计信息
        payload['data']['stats'] = {
            'content_length': len(message_data.get('content', '')),
            'attachment_count': len(message_data.get('attachments', [])),
            'embed_count': len(message_data.get('embeds', [])),
            'mention_count': len(message_data.get('mentions', []))
        }
        
        return payload
    
    def format_channel_info(self, channel_data):
        """格式化频道信息用于webhook"""
        if not channel_data:
            return {}
        
        formatted = {
            'basic': {
                'id': channel_data.get('id'),
                'name': channel_data.get('name'),
                'type': channel_data.get('type')
            },
            'details': {
                'created_at': channel_data.get('created_at'),
                'topic': channel_data.get('topic'),
                'position': channel_data.get('position'),
                'nsfw': channel_data.get('nsfw', False),
                'slowmode_delay': channel_data.get('slowmode_delay', 0)
            },
            'category': channel_data.get('category'),
            'permissions': channel_data.get('permissions', {}),
            'member_info': {
                'count': channel_data.get('member_count'),
                'members': channel_data.get('members', [])
            }
        }
        return formatted
    
    def format_guild_info(self, guild_data):
        """格式化服务器信息用于webhook"""
        if not guild_data:
            return {}
        
        formatted = {
            'basic': {
                'id': guild_data.get('id'),
                'name': guild_data.get('name'),
                'owner_id': guild_data.get('owner_id')
            },
            'statistics': {
                'member_count': guild_data.get('member_count'),
                'channels': guild_data.get('channels', {}),
                'roles_count': guild_data.get('roles_count'),
                'emojis_count': guild_data.get('emojis_count'),
                'boost_level': guild_data.get('boost_level'),
                'boost_count': guild_data.get('boost_count')
            },
            'settings': {
                'verification_level': guild_data.get('verification_level'),
                'explicit_content_filter': guild_data.get('explicit_content_filter'),
                'default_notifications': guild_data.get('default_notifications')
            },
            'features': guild_data.get('features', []),
            'active_members': guild_data.get('active_members', []),
            'member_stats': guild_data.get('statistics', {})
        }
        return formatted
    
    def format_author_info(self, author_data):
        """格式化作者信息用于webhook"""
        if not author_data:
            return {}
        
        formatted = {
            'basic': {
                'id': author_data.get('id'),
                'name': author_data.get('name'),
                'display_name': author_data.get('display_name'),
                'bot': author_data.get('bot', False)
            },
            'profile': {
                'avatar_url': author_data.get('avatar_url'),
                'created_at': author_data.get('created_at'),
                'discriminator': author_data.get('discriminator'),
                'public_flags': author_data.get('public_flags', 0)
            },
            'server_info': {
                'joined_server_at': author_data.get('joined_server_at'),
                'premium_since': author_data.get('premium_since'),
                'roles': author_data.get('roles', []),
                'permissions': author_data.get('permissions', {})
            },
            'activity': author_data.get('recent_activity', {})
        }
        return formatted
        
    def truncate_text(self, text, max_length):
        """截断文本到指定长度"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
        
    async def test_webhook(self):
        """测试webhook连接"""
        test_payload = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'webhook_test',
            'data': {
                'message': 'Discord机器人webhook测试',
                'status': 'testing'
            },
            'metadata': {
                'bot_name': 'Discord转发机器人',
                'version': '1.0.0'
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        self.logger.info('Webhook测试成功')
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f'Webhook测试失败: {response.status} - {error_text}')
                        return False
                        
        except Exception as e:
            self.logger.error(f'Webhook测试异常: {e}')
            return False
