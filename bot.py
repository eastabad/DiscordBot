"""
Discord机器人核心实现
监听@提及并转发到webhook
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from webhook_handler import WebhookHandler
from chart_service import ChartService
from rate_limiter import RateLimiter
import io
import re

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
        self.chart_service = ChartService(config)
        self.rate_limiter = RateLimiter(daily_limit=3)  # 每日限制3次
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
                name="股票图表请求"
            )
        )
        
        # 输出监控频道信息
        if self.config.monitor_channel_ids:
            self.logger.info(f'监控频道IDs: {", ".join(self.config.monitor_channel_ids)}')
        else:
            self.logger.warning('未设置监控频道ID')
        
    async def on_message(self, message):
        """消息事件处理"""
        # 添加调试日志
        self.logger.debug(f'收到消息: {message.content[:50]}... 来自: {message.author.name}')
        
        # 忽略机器人自己的消息
        if message.author == self.user:
            self.logger.debug('忽略机器人自己的消息')
            return
            
        # 检查是否被@提及（检查机器人角色是否被提及）
        bot_role_mentioned = False
        if message.guild:
            bot_member = message.guild.get_member(self.user.id)
            if bot_member:
                bot_role_mentioned = any(role in message.role_mentions for role in bot_member.roles)
        
        is_mentioned = (self.user in message.mentions or 
                       bot_role_mentioned or
                       f'<@{self.user.id}>' in message.content or
                       f'<@!{self.user.id}>' in message.content)
        
        # 检查是否在监控频道中
        is_monitored_channel = (
            self.config.monitor_channel_ids and 
            str(message.channel.id) in self.config.monitor_channel_ids
        )
        
        if is_mentioned and is_monitored_channel:
            self.logger.info(f'在监控频道中检测到提及，开始处理股票图表请求...')
            await self.handle_chart_request(message)
        elif is_mentioned:
            self.logger.info(f'检测到@提及，开始处理webhook转发...')
            await self.handle_mention(message)
        elif is_monitored_channel and self.has_stock_command(message.content):
            self.logger.info(f'在监控频道中检测到股票命令，开始处理图表请求...')
            await self.handle_chart_request(message)
        else:
            self.logger.debug(f'消息不包含提及或股票命令: {message.content[:30]}')
            
        # 处理命令
        await self.process_commands(message)
    
    async def handle_chart_request(self, message):
        """处理股票图表请求"""
        try:
            # 检查用户请求限制
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            
            can_request, current_count, remaining = self.rate_limiter.check_user_limit(user_id, username)
            
            if not can_request:
                # 用户已超过每日限制
                limit_msg = f"⚠️ {username}, 您今日的图表请求已达到限制 (3次/天)。请明天再试。"
                await message.reply(limit_msg)
                self.logger.warning(f"用户 {username} ({user_id}) 超过每日请求限制: {current_count}/3")
                return
            
            # 解析命令
            command_result = self.chart_service.parse_command(message.content)
            if not command_result:
                await message.channel.send(
                    f"{message.author.mention} 请使用正确格式：`AAPL,1h` 或 `NASDAQ:GOOG,15m`"
                )
                return
            
            symbol, timeframe = command_result
            
            # 记录请求（在实际处理前记录）
            success = self.rate_limiter.record_request(user_id, username)
            remaining_after = remaining - 1
            
            if success:
                self.logger.info(f"用户 {username} 请求图表，今日剩余: {remaining_after}/3")
            
            # 添加处理中的反应
            await message.add_reaction("⏳")
            
            # 获取图表
            self.logger.info(f"开始获取图表: {symbol} {timeframe}")
            chart_data = await self.chart_service.get_chart(symbol, timeframe)
            
            if chart_data:
                # 发送私信
                try:
                    dm_content = self.chart_service.format_chart_dm_content(symbol, timeframe)
                    file = discord.File(
                        io.BytesIO(chart_data), 
                        filename=f"{symbol}_{timeframe}.png"
                    )
                    
                    await message.author.send(content=dm_content, file=file)
                    
                    # 在频道中提示成功（包含剩余次数信息）
                    success_msg = self.chart_service.format_success_message(symbol, timeframe)
                    limit_info = f"（今日剩余 {remaining_after}/3 次）"
                    await message.channel.send(f"{message.author.mention} {success_msg} {limit_info}")
                    
                    # 更新反应为成功
                    await message.remove_reaction("⏳", self.user)
                    await message.add_reaction("✅")
                    
                    self.logger.info(f"成功发送图表: {symbol} {timeframe} 给用户 {message.author.name}")
                    
                except discord.Forbidden:
                    await message.channel.send(
                        f"{message.author.mention} 无法发送私信，请检查您的隐私设置"
                    )
                    await message.remove_reaction("⏳", self.user)
                    await message.add_reaction("❌")
                    
            else:
                # 获取图表失败
                error_msg = self.chart_service.format_error_message(symbol, timeframe, "API调用失败")
                await message.channel.send(f"{message.author.mention} {error_msg}")
                
                await message.remove_reaction("⏳", self.user)
                await message.add_reaction("❌")
                
        except Exception as e:
            self.logger.error(f"处理图表请求失败: {e}")
            await message.channel.send(
                f"{message.author.mention} 处理请求时发生错误，请稍后重试"
            )
            try:
                await message.remove_reaction("⏳", self.user)
                await message.add_reaction("❌")
            except:
                pass
    
    def has_stock_command(self, content: str) -> bool:
        """检查消息是否包含股票命令格式"""
        # 简单检查是否包含股票符号和时间框架格式
        return bool(re.search(r'[A-Z:]+[,\s]+\d+[smhdwMy]', content, re.IGNORECASE))
        
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
        # 获取详细的频道信息
        channel_info = await self.collect_detailed_channel_info(message.channel)
        
        # 获取服务器信息
        guild_info = await self.collect_guild_info(message.guild) if message.guild else None
        
        # 获取详细的作者信息
        author_info = {
            'id': message.author.id,
            'name': message.author.name,
            'display_name': message.author.display_name,
            'discriminator': message.author.discriminator,
            'bot': message.author.bot,
            'avatar_url': str(message.author.avatar.url) if message.author.avatar else None,
            'created_at': message.author.created_at.isoformat() if message.author.created_at else None,
            'public_flags': message.author.public_flags.value if hasattr(message.author, 'public_flags') else 0
        }
        
        # 获取用户上下文信息
        user_context = await self.collect_user_context_info(message.author, message.guild)
        author_info.update(user_context)
        
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
            'guild': guild_info,
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
    
    async def collect_detailed_channel_info(self, channel):
        """收集详细的频道信息"""
        try:
            channel_info = {
                'id': channel.id,
                'name': channel.name,
                'type': str(channel.type),
                'created_at': channel.created_at.isoformat() if channel.created_at else None,
                'category': None,
                'position': getattr(channel, 'position', None),
                'topic': getattr(channel, 'topic', None),
                'nsfw': getattr(channel, 'nsfw', False),
                'permissions': {},
                'member_count': None,
                'slowmode_delay': getattr(channel, 'slowmode_delay', 0),
                'guild_id': channel.guild.id if hasattr(channel, 'guild') and channel.guild else None
            }
            
            # 获取分类信息
            if hasattr(channel, 'category') and channel.category:
                channel_info['category'] = {
                    'id': channel.category.id,
                    'name': channel.category.name,
                    'position': channel.category.position
                }
            
            # 获取权限信息（针对文字频道）
            if hasattr(channel, 'guild') and channel.guild:
                try:
                    # 获取机器人在该频道的权限
                    bot_member = channel.guild.get_member(self.user.id)
                    if bot_member:
                        perms = channel.permissions_for(bot_member)
                        channel_info['permissions'] = {
                            'read_messages': perms.read_messages,
                            'send_messages': perms.send_messages,
                            'manage_messages': perms.manage_messages,
                            'embed_links': perms.embed_links,
                            'attach_files': perms.attach_files,
                            'read_message_history': perms.read_message_history,
                            'add_reactions': perms.add_reactions,
                            'use_external_emojis': perms.use_external_emojis
                        }
                except Exception as e:
                    self.logger.debug(f"获取频道权限时出错: {e}")
            
            # 获取成员数量（针对语音频道）
            if hasattr(channel, 'members'):
                channel_info['member_count'] = len(channel.members)
                channel_info['members'] = [
                    {
                        'id': member.id,
                        'name': member.name,
                        'display_name': member.display_name
                    } for member in channel.members[:10]  # 限制最多10个成员信息
                ]
            
            return channel_info
            
        except Exception as e:
            self.logger.error(f"收集频道信息时出错: {e}")
            return {
                'id': channel.id,
                'name': getattr(channel, 'name', 'Unknown'),
                'type': str(channel.type),
                'error': str(e)
            }
    
    async def collect_guild_info(self, guild):
        """收集详细的服务器信息"""
        if not guild:
            return None
            
        try:
            guild_info = {
                'id': guild.id,
                'name': guild.name,
                'owner_id': guild.owner_id,
                'member_count': guild.member_count,
                'created_at': guild.created_at.isoformat() if guild.created_at else None,
                'verification_level': str(guild.verification_level),
                'explicit_content_filter': str(guild.explicit_content_filter),
                'default_notifications': str(guild.default_message_notifications),
                'features': list(guild.features),
                'boost_level': guild.premium_tier,
                'boost_count': guild.premium_subscription_count or 0,
                'icon_url': str(guild.icon.url) if guild.icon else None,
                'banner_url': str(guild.banner.url) if guild.banner else None,
                'channels': {
                    'total': len(guild.channels),
                    'text': len([c for c in guild.channels if c.type.name == 'text']),
                    'voice': len([c for c in guild.channels if c.type.name == 'voice']),
                    'categories': len([c for c in guild.channels if c.type.name == 'category'])
                },
                'roles_count': len(guild.roles),
                'emojis_count': len(guild.emojis),
                'region': getattr(guild, 'region', 'unknown')
            }
            
            # 获取活跃成员信息（最近在线的前5位）
            active_members = []
            try:
                for member in guild.members[:5]:  # 限制数量
                    if not member.bot:
                        active_members.append({
                            'id': member.id,
                            'name': member.name,
                            'display_name': member.display_name,
                            'status': str(member.status) if hasattr(member, 'status') else 'unknown',
                            'joined_at': member.joined_at.isoformat() if member.joined_at else None
                        })
                guild_info['active_members'] = active_members
            except Exception as e:
                self.logger.debug(f"获取活跃成员时出错: {e}")
            
            # 获取服务器统计信息
            try:
                guild_info['statistics'] = {
                    'online_members': sum(1 for m in guild.members if hasattr(m, 'status') and m.status != discord.Status.offline),
                    'bot_count': sum(1 for m in guild.members if m.bot),
                    'human_count': sum(1 for m in guild.members if not m.bot)
                }
            except Exception as e:
                self.logger.debug(f"计算服务器统计时出错: {e}")
            
            return guild_info
            
        except Exception as e:
            self.logger.error(f"收集服务器信息时出错: {e}")
            return {
                'id': guild.id,
                'name': guild.name,
                'error': str(e)
            }
    
    async def collect_user_context_info(self, user, guild=None):
        """收集用户上下文信息"""
        try:
            user_info = {
                'recent_activity': {},
                'permissions': {},
                'roles': []
            }
            
            # 如果是服务器成员，获取角色和权限信息
            if guild:
                member = guild.get_member(user.id)
                if member:
                    user_info['roles'] = [
                        {
                            'id': role.id,
                            'name': role.name,
                            'color': role.color.value,
                            'permissions': role.permissions.value,
                            'position': role.position
                        } for role in member.roles[1:]  # 跳过@everyone角色
                    ]
                    
                    # 获取用户在服务器中的权限
                    perms = member.guild_permissions
                    user_info['permissions'] = {
                        'administrator': perms.administrator,
                        'manage_guild': perms.manage_guild,
                        'manage_channels': perms.manage_channels,
                        'manage_messages': perms.manage_messages,
                        'kick_members': perms.kick_members,
                        'ban_members': perms.ban_members
                    }
                    
                    user_info['joined_server_at'] = member.joined_at.isoformat() if member.joined_at else None
                    user_info['premium_since'] = member.premium_since.isoformat() if member.premium_since else None
            
            return user_info
            
        except Exception as e:
            self.logger.error(f"收集用户上下文信息时出错: {e}")
            return {'error': str(e)}
        
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
        await ctx.send(embed=embed)
        
    @commands.command(name='quota', aliases=['限制', '配额'])
    async def quota_command(self, ctx):
        """查看用户每日请求配额"""
        user_id = str(ctx.author.id)
        stats = self.rate_limiter.get_user_stats(user_id)
        
        if stats:
            embed = discord.Embed(
                title="📊 每日请求配额",
                description=f"用户：{ctx.author.display_name}",
                color=0x00aaff
            )
            embed.add_field(name="今日已使用", value=f"{stats['request_count']}/3", inline=True)
            embed.add_field(name="剩余次数", value=f"{stats['remaining']}", inline=True)
            embed.add_field(name="配额重置", value="每日0点（UTC）", inline=True)
            
            if stats['last_request']:
                embed.add_field(name="最后请求", value=stats['last_request'][:19], inline=False)
        else:
            embed = discord.Embed(
                title="📊 每日请求配额",
                description=f"用户：{ctx.author.display_name}\n今日尚未使用图表功能",
                color=0x00ff00
            )
            embed.add_field(name="可用次数", value="3/3", inline=True)
            
        await ctx.send(embed=embed)
