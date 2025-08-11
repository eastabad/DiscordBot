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
        """构建webhook负载"""
        # 格式化消息内容
        content_preview = self.truncate_text(message_data.get('content', ''), 100)
        
        # 构建基本信息
        payload = {
            'timestamp': message_data.get('timestamp'),
            'event_type': 'discord_mention',
            'data': {
                'message': {
                    'id': message_data.get('message_id'),
                    'content': message_data.get('content'),
                    'content_preview': content_preview,
                    'created_at': message_data.get('created_at'),
                    'edited_at': message_data.get('edited_at'),
                    'jump_url': message_data.get('jump_url')
                },
                'author': message_data.get('author', {}),
                'channel': message_data.get('channel', {}),
                'attachments': message_data.get('attachments', []),
                'embeds': message_data.get('embeds', []),
                'mentions': message_data.get('mentions', [])
            },
            'metadata': {
                'bot_name': 'Discord转发机器人',
                'version': '1.0.0',
                'processed_at': datetime.now().isoformat()
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
