#!/usr/bin/env python3
"""
Discord Bot API Server
为n8n工作流提供HTTP API接口，用于发送消息和图片
"""

import asyncio
import logging
import json
import aiohttp
from aiohttp import web, ClientSession
import discord
from datetime import datetime
import base64
import io

class DiscordAPIServer:
    """Discord机器人API服务器"""
    
    def __init__(self, bot):
        """初始化API服务器"""
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_post('/api/send-message', self.send_message_handler)
        self.app.router.add_post('/api/send-dm', self.send_dm_handler)
        self.app.router.add_post('/api/send-chart', self.send_chart_handler)
        self.app.router.add_get('/api/health', self.health_check)
        self.app.router.add_get('/', self.api_docs)
        
    async def api_docs(self, request):
        """API文档页面"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Discord Bot API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { color: #fff; padding: 3px 8px; border-radius: 3px; font-weight: bold; }
                .post { background: #28a745; }
                .get { background: #007bff; }
                code { background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Discord Bot API 文档</h1>
            <p>Discord机器人API服务器，支持n8n工作流集成</p>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /api/health</h3>
                <p>健康检查端点</p>
                <p><strong>响应:</strong> JSON状态信息</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span> /api/send-message</h3>
                <p>发送消息到指定频道</p>
                <p><strong>请求体:</strong> <code>{"channelId": "123", "content": "消息内容"}</code></p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span> /api/send-dm</h3>
                <p>发送私信给指定用户</p>
                <p><strong>请求体:</strong> <code>{"userId": "123", "content": "消息内容"}</code></p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span> /api/send-chart</h3>
                <p>发送图表图片 (n8n工作流专用)</p>
                <p><strong>请求体:</strong> 数组格式，包含authorId、symbol、timeframe等字段</p>
                <p><strong>功能:</strong> 自动将图表图片发送给指定用户的私信</p>
            </div>
            
            <h2>n8n工作流示例</h2>
            <p>您可以在n8n工作流中使用以下URL调用API：</p>
            <p><code>POST https://your-replit-domain.replit.app/api/send-chart</code></p>
            
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
        
    async def health_check(self, request):
        """健康检查端点"""
        return web.json_response({
            'status': 'healthy',
            'bot_status': 'online' if self.bot.is_ready() else 'offline',
            'timestamp': datetime.now().isoformat()
        })
        
    async def send_message_handler(self, request):
        """发送消息到指定频道"""
        try:
            data = await request.json()
            
            # 验证必需字段
            if 'channelId' not in data or 'content' not in data:
                return web.json_response({
                    'error': 'Missing required fields: channelId, content'
                }, status=400)
                
            channel_id = int(data['channelId'])
            content = data['content']
            
            # 获取频道
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return web.json_response({
                    'error': f'Channel {channel_id} not found'
                }, status=404)
                
            # 发送消息
            message = await channel.send(content)
            
            return web.json_response({
                'success': True,
                'messageId': str(message.id),
                'channelId': str(channel.id),
                'timestamp': message.created_at.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f'发送消息API错误: {e}')
            return web.json_response({
                'error': str(e)
            }, status=500)
            
    async def send_dm_handler(self, request):
        """发送私信给指定用户"""
        try:
            data = await request.json()
            
            # 验证必需字段
            if 'userId' not in data or 'content' not in data:
                return web.json_response({
                    'error': 'Missing required fields: userId, content'
                }, status=400)
                
            user_id = int(data['userId'])
            content = data['content']
            
            # 获取用户
            user = self.bot.get_user(user_id)
            if not user:
                user = await self.bot.fetch_user(user_id)
                
            if not user:
                return web.json_response({
                    'error': f'User {user_id} not found'
                }, status=404)
                
            # 发送私信
            message = await user.send(content)
            
            return web.json_response({
                'success': True,
                'messageId': str(message.id),
                'userId': str(user.id),
                'timestamp': message.created_at.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f'发送私信API错误: {e}')
            return web.json_response({
                'error': str(e)
            }, status=500)
            
    async def send_chart_handler(self, request):
        """发送图表图片（n8n工作流专用）"""
        try:
            data = await request.json()
            
            # 验证数据格式
            if not isinstance(data, list) or len(data) == 0:
                return web.json_response({
                    'error': 'Data must be a non-empty array'
                }, status=400)
                
            item = data[0]  # 取第一个项目
            
            # 验证必需字段
            required_fields = ['authorId', 'symbol', 'timeframe']
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                return web.json_response({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
                
            author_id = int(item['authorId'])
            symbol = item['symbol']
            timeframe = item['timeframe']
            
            # 获取用户
            user = self.bot.get_user(author_id)
            if not user:
                user = await self.bot.fetch_user(author_id)
                
            if not user:
                return web.json_response({
                    'error': f'User {author_id} not found'
                }, status=404)
                
            # 处理Discord负载
            discord_payload = item.get('discordPayload', {})
            content = discord_payload.get('content', f'📊 {symbol} {timeframe} 图表')
            
            # 处理附件
            attachments = discord_payload.get('attachments', [])
            files = []
            
            if attachments:
                for attachment in attachments:
                    url = attachment.get('url')
                    filename = attachment.get('filename', f'{symbol}_{timeframe}.png')
                    
                    if url:
                        # 如果URL是base64数据
                        if url.startswith('data:'):
                            # 解析base64数据
                            header, encoded = url.split(',', 1)
                            image_data = base64.b64decode(encoded)
                            files.append(discord.File(io.BytesIO(image_data), filename=filename))
                        else:
                            # 从URL下载图片
                            async with ClientSession() as session:
                                async with session.get(url) as resp:
                                    if resp.status == 200:
                                        image_data = await resp.read()
                                        files.append(discord.File(io.BytesIO(image_data), filename=filename))
            
            # 发送消息
            if files:
                message = await user.send(content=content, files=files)
            else:
                message = await user.send(content=content)
                
            # 记录成功发送
            self.logger.info(f'成功发送图表给用户 {user.name}: {symbol} {timeframe}')
            
            return web.json_response({
                'success': True,
                'messageId': str(message.id),
                'userId': str(user.id),
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': message.created_at.isoformat(),
                'filesSent': len(files)
            })
            
        except Exception as e:
            self.logger.error(f'发送图表API错误: {e}')
            return web.json_response({
                'error': str(e)
            }, status=500)
            
    async def start_server(self, host='0.0.0.0', port=5000):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        self.logger.info(f'Discord API服务器已启动: http://{host}:{port}')
        self.logger.info(f'可用端点:')
        self.logger.info(f'  POST /api/send-message - 发送频道消息')
        self.logger.info(f'  POST /api/send-dm - 发送私信')
        self.logger.info(f'  POST /api/send-chart - 发送图表 (n8n工作流)')
        self.logger.info(f'  GET  /api/health - 健康检查')
        
        return runner