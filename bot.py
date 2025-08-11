"""
Discord机器人核心实现
监听@提及并转发到webhook
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from webhook_handler import WebhookHandler

class DiscordBot(commands.Bot):
    """Discord机器人类"""
    
    def __init__(self, config):
        """初始化机器人"""
        # 设置机器人意图
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.config = config
        self.webhook_handler = WebhookHandler(config.webhook_url)
        self.logger = logging.getLogger(__name__)
        
    async def on_ready(self):
        """机器人就绪事件"""
        if self.user:
            self.logger.info(f'机器人已登录: {self.user.name} (ID: {self.user.id})')
            self.logger.info(f'机器人在 {len(self.guilds)} 个服务器中')
            
            # 输出机器人的意图信息用于调试
            self.logger.info(f'机器人意图: message_content={self.intents.message_content}, messages={self.intents.messages}, guild_messages={self.intents.guild_messages}')
        
        # 设置机器人状态
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="@提及消息"
            )
        )
        
    async def on_message(self, message):
        """消息事件处理"""
        # 添加调试日志
        self.logger.debug(f'收到消息: {message.content[:50]}... 来自: {message.author.name}')
        
        # 忽略机器人自己的消息
        if message.author == self.user:
            self.logger.debug('忽略机器人自己的消息')
            return
            
        # 检查是否被@提及
        if self.user in message.mentions:
            self.logger.info(f'检测到@提及，开始处理...')
            await self.handle_mention(message)
        else:
            self.logger.debug(f'消息不包含@提及: {message.content[:30]}')
            
        # 处理命令
        await self.process_commands(message)
        
    async def handle_mention(self, message):
        """处理@提及的消息"""
        try:
            self.logger.info(f'收到来自 {message.author.name} 在 #{message.channel.name} 的@提及')
            
            # 构建消息数据
            message_data = await self.build_message_data(message)
            
            # 发送到webhook
            success = await self.webhook_handler.send_message(message_data)
            
            if success:
                self.logger.info(f'成功转发消息到webhook: {message.id}')
                # 添加反应表示处理成功
                await message.add_reaction('✅')
            else:
                self.logger.error(f'转发消息到webhook失败: {message.id}')
                await message.add_reaction('❌')
                
        except Exception as e:
            self.logger.error(f'处理@提及时发生错误: {e}')
            try:
                await message.add_reaction('❌')
            except:
                pass
                
    async def build_message_data(self, message):
        """构建要发送到webhook的消息数据"""
        # 获取频道信息
        channel_info = {
            'id': message.channel.id,
            'name': message.channel.name,
            'type': str(message.channel.type),
            'guild_id': message.guild.id if message.guild else None,
            'guild_name': message.guild.name if message.guild else None
        }
        
        # 获取作者信息
        author_info = {
            'id': message.author.id,
            'name': message.author.name,
            'display_name': message.author.display_name,
            'discriminator': message.author.discriminator,
            'bot': message.author.bot,
            'avatar_url': str(message.author.avatar.url) if message.author.avatar else None
        }
        
        # 处理附件
        attachments = []
        for attachment in message.attachments:
            attachments.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'url': attachment.url,
                'size': attachment.size,
                'content_type': attachment.content_type
            })
        
        # 处理嵌入内容
        embeds = []
        for embed in message.embeds:
            embed_data = {
                'title': embed.title,
                'description': embed.description,
                'url': embed.url,
                'color': embed.color.value if embed.color else None,
                'type': embed.type
            }
            embeds.append(embed_data)
        
        # 构建完整的消息数据
        message_data = {
            'message_id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'edited_at': message.edited_at.isoformat() if message.edited_at else None,
            'author': author_info,
            'channel': channel_info,
            'attachments': attachments,
            'embeds': embeds,
            'mention_everyone': message.mention_everyone,
            'mentions': [
                {
                    'id': user.id,
                    'name': user.name,
                    'display_name': user.display_name
                } for user in message.mentions
            ],
            'jump_url': message.jump_url,
            'timestamp': datetime.now().isoformat()
        }
        
        return message_data
        
    async def on_error(self, event, *args, **kwargs):
        """错误处理"""
        self.logger.error(f'Discord事件错误 {event}: {args}', exc_info=True)
        
    async def on_command_error(self, ctx, error):
        """命令错误处理"""
        if isinstance(error, commands.CommandNotFound):
            return
            
        self.logger.error(f'命令错误在 {ctx.command}: {error}')
        
        try:
            await ctx.send(f'执行命令时发生错误: {error}')
        except:
            pass
            
    @commands.command(name='ping')
    async def ping_command(self, ctx):
        """测试命令 - 检查机器人延迟"""
        latency = round(self.latency * 1000)
        await ctx.send(f'🏓 Pong! 延迟: {latency}ms')
        
    @commands.command(name='info')
    async def info_command(self, ctx):
        """显示机器人信息"""
        embed = discord.Embed(
            title="机器人信息",
            description="Discord消息转发机器人",
            color=0x00ff00
        )
        embed.add_field(name="服务器数量", value=len(self.guilds), inline=True)
        embed.add_field(name="延迟", value=f"{round(self.latency * 1000)}ms", inline=True)
        embed.add_field(name="版本", value="1.0.0", inline=True)
        embed.add_field(
            name="功能", 
            value="• 监听@提及\n• 转发到Webhook\n• 消息格式化", 
            inline=False
        )
        
        await ctx.send(embed=embed)
