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
from prediction_service import StockPredictionService
from chart_analysis_service import ChartAnalysisService
from channel_cleaner import ChannelCleaner
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
        self.prediction_service = StockPredictionService(config)  # 股票预测服务
        self.chart_analysis_service = ChartAnalysisService(config)  # 图表分析服务
        self.channel_cleaner = ChannelCleaner(self, config)  # 频道清理服务
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
        
        # 启动频道清理服务
        await self.channel_cleaner.start_daily_cleanup()
        self.logger.info("频道清理服务已启动")
        
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
        
        # 检查命令（包括管理员命令） - 优先级最高
        if '!' in message.content:
            # 检查是否包含命令
            content_parts = message.content.split()
            for part in content_parts:
                if part.startswith('!'):
                    command_name = part[1:]  # 移除!前缀
                    self.logger.info(f'检测到命令: {part}')
                    
                    # 直接调用相应的命令处理函数
                    if command_name == 'cleanup_now':
                        await self.manual_cleanup_command_direct(message)
                        return
                    elif command_name == 'cleanup_status':
                        await self.cleanup_status_command_direct(message)
                        return
                    elif command_name == 'cleanup_channel':
                        await self.cleanup_specific_channel_direct(message)
                        return
                    elif command_name == 'help_admin':
                        await self.help_admin_command_direct(message)
                        return
                    else:
                        # 对于其他命令，使用正常的命令处理
                        await self.process_commands(message)
                        return
        
        if is_mentioned and is_monitored_channel and self.has_stock_command(message.content):
            self.logger.info(f'在监控频道中检测到提及和股票命令，开始处理股票图表请求...')
            await self.handle_chart_request(message)
        elif is_mentioned:
            # 检查是否有图片附件需要分析
            if message.attachments and self.has_chart_image(message.attachments):
                self.logger.info(f'检测到图表图片，开始处理图表分析...')
                await self.handle_chart_analysis_request(message)
            # 检查是否是预测请求
            elif self.has_prediction_command(message.content):
                self.logger.info(f'检测到预测请求，开始处理股票预测...')
                await self.handle_prediction_request(message)
            # 检查是否是股票命令（在非监控频道中也支持@提及方式）
            elif self.has_stock_command(message.content):
                self.logger.info(f'检测到@提及的股票命令，开始处理股票图表请求...')
                await self.handle_chart_request(message)
            else:
                self.logger.info(f'检测到@提及，开始处理webhook转发...')
                await self.handle_mention(message)
        elif is_monitored_channel and self.has_stock_command(message.content):
            self.logger.info(f'在监控频道中检测到股票命令，开始处理图表请求...')
            await self.handle_chart_request(message)
        elif is_monitored_channel and self.has_prediction_command(message.content):
            self.logger.info(f'在监控频道中检测到预测请求，开始处理股票预测...')
            await self.handle_prediction_request(message)
        elif is_monitored_channel and message.attachments and self.has_chart_image(message.attachments):
            self.logger.info(f'在监控频道中检测到图表图片，开始处理图表分析...')
            await self.handle_chart_analysis_request(message)
        else:
            self.logger.debug(f'消息不包含提及或股票命令: {message.content[:30]}')
    
    async def handle_chart_request(self, message):
        """处理股票图表请求"""
        try:
            # 检查用户请求限制
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            
            can_request, current_count, remaining = self.rate_limiter.check_user_limit(user_id, username)
            is_exempt = remaining == 999  # 豁免用户的标识
            
            if not can_request:
                # 用户已超过每日限制
                limit_msg = f"⚠️ {username}, 您今日的图表请求已达到限制 (3次/天)。请明天再试。"
                await message.reply(limit_msg)
                await message.add_reaction("❌")
                self.logger.warning(f"用户 {username} ({user_id}) 超过每日请求限制: {current_count}/3")
                return
            
            # 解析命令
            command_result = self.chart_service.parse_command(message.content)
            if not command_result:
                await message.channel.send(
                    f"{message.author.mention} ❌ 命令格式错误！\n" +
                    f"请使用正确格式：\n" +
                    f"• `AAPL,1h` 或 `AAPL，1h`（支持中英文逗号）\n" +
                    f"• `NASDAQ:GOOG,15m`\n" +
                    f"• 支持时间框架：1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M"
                )
                await message.add_reaction("❌")
                return
            
            symbol, timeframe = command_result
            
            # 记录请求（在实际处理前记录，豁免用户跳过）
            if not is_exempt:
                success = self.rate_limiter.record_request(user_id, username)
                remaining_after = remaining - 1
                if success:
                    self.logger.info(f"用户 {username} 请求图表，今日剩余: {remaining_after}/3")
            else:
                remaining_after = 999  # 豁免用户保持无限制
                self.logger.info(f"豁免用户 {username} 请求图表，无限制")
            
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
                    if is_exempt:
                        limit_info = f"（VIP无限制）"
                    else:
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
                detailed_error = (f"{message.author.mention} ❌ 获取图表失败！\n"
                                f"• 符号: {symbol}\n"
                                f"• 时间框架: {timeframe}\n" 
                                f"• 可能原因: API服务暂时不可用，请稍后重试\n"
                                f"• 如果问题持续，请检查股票符号是否正确")
                await message.channel.send(detailed_error)
                
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
    
    def has_prediction_command(self, content: str) -> bool:
        """检查消息是否包含预测请求"""
        prediction_keywords = ['预测', 'predict', '趋势', 'trend', '分析', 'analysis', '预测分析', '走势预测']
        content_lower = content.lower()
        # 检查是否包含预测关键词和股票符号
        has_keyword = any(keyword in content_lower for keyword in prediction_keywords)
        has_symbol = bool(re.search(r'[A-Z]{2,}', content, re.IGNORECASE))
        return has_keyword and has_symbol
    
    async def handle_prediction_request(self, message):
        """处理股票预测请求"""
        try:
            # 检查用户请求限制
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            
            can_request, current_count, remaining = self.rate_limiter.check_user_limit(user_id, username)
            is_exempt = remaining == 999  # 豁免用户的标识
            
            if not can_request:
                # 用户已超过每日限制
                limit_msg = f"⚠️ {username}, 您今日的预测请求已达到限制 (3次/天)。请明天再试。"
                await message.reply(limit_msg)
                await message.add_reaction("❌")
                self.logger.warning(f"用户 {username} ({user_id}) 超过每日请求限制: {current_count}/3")
                return
                
            # 从消息中提取股票符号
            symbol_match = re.search(r'([A-Z][A-Z:]*[A-Z]+)', message.content, re.IGNORECASE)
            if not symbol_match:
                await message.channel.send(
                    f"{message.author.mention} 请提供有效的股票符号，例如：`@bot 预测 AAPL 趋势`"
                )
                return
            
            symbol = symbol_match.group(1).upper()
            
            # 使用chart_service的交易所映射逻辑
            # 这将在chart_service.get_chart()中自动处理
            pass
            
            # 记录请求（在实际处理前记录，豁免用户跳过）
            if not is_exempt:
                success = self.rate_limiter.record_request(user_id, username)
                remaining_after = remaining - 1
                if success:
                    self.logger.info(f"用户 {username} 请求预测，今日剩余: {remaining_after}/3")
            else:
                remaining_after = 999  # 豁免用户保持无限制
                self.logger.info(f"豁免用户 {username} 请求预测，无限制")
            
            # 添加处理中的反应
            await message.add_reaction("🔄")
            
            self.logger.info(f'开始生成预测: {symbol}')
            
            # 生成预测
            prediction = await self.prediction_service.get_prediction(symbol)
            
            # 格式化预测消息
            prediction_message = self.prediction_service.format_prediction_message(prediction)
            
            # 发送私信
            try:
                await message.author.send(f"📈 **{symbol} 股票趋势预测分析**\n\n{prediction_message}")
                
                # 在频道中提示成功（包含剩余次数信息）
                if is_exempt:
                    limit_info = f"（VIP无限制）"
                else:
                    limit_info = f"（今日剩余 {remaining_after}/3 次）"
                await message.channel.send(f"{message.author.mention} 📈 {symbol} 趋势预测已发送到您的私信中 {limit_info}")
                
                # 移除处理中反应，添加成功反应
                await message.remove_reaction("🔄", self.user)
                await message.add_reaction("📈")
                
                self.logger.info(f'成功发送预测: {symbol}')
                
            except discord.Forbidden:
                await message.channel.send(
                    f"{message.author.mention} 无法发送私信，请检查您的隐私设置"
                )
                await message.remove_reaction("🔄", self.user)
                await message.add_reaction("❌")
            
        except Exception as e:
            self.logger.error(f"处理预测请求失败: {e}")
            await message.channel.send(
                f"{message.author.mention} 生成预测时发生错误，请稍后重试"
            )
            try:
                await message.remove_reaction("🔄", self.user)
                await message.add_reaction("❌")
            except:
                pass
    
    def has_chart_image(self, attachments) -> bool:
        """检查附件中是否包含图表图片"""
        for attachment in attachments:
            # 检查文件扩展名
            filename = attachment.filename.lower()
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # 检查文件大小（避免过大的文件）
                if attachment.size < 10 * 1024 * 1024:  # 10MB限制
                    return True
        return False
    
    async def handle_chart_analysis_request(self, message):
        """处理图表分析请求"""
        try:
            # 检查用户请求限制
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            
            can_request, current_count, remaining = self.rate_limiter.check_user_limit(user_id, username)
            is_exempt = remaining == 999  # 豁免用户的标识
            
            if not can_request:
                # 用户已超过每日限制
                limit_msg = f"⚠️ {username}, 您今日的分析请求已达到限制 (3次/天)。请明天再试。"
                await message.reply(limit_msg)
                await message.add_reaction("❌")
                self.logger.warning(f"用户 {username} ({user_id}) 超过每日请求限制: {current_count}/3")
                return
                
            # 找到第一个图片附件
            chart_image = None
            for attachment in message.attachments:
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    chart_image = attachment
                    break
            
            if not chart_image:
                await message.channel.send(
                    f"{message.author.mention} 请上传PNG、JPG或JPEG格式的图表图片"
                )
                return
            
            # 从消息中尝试提取股票符号（可选）
            symbol = ""
            symbol_match = re.search(r'([A-Z][A-Z:]*[A-Z]+)', message.content, re.IGNORECASE)
            if symbol_match:
                symbol = symbol_match.group(1).upper()
                if ':' not in symbol:
                    symbol = f"NASDAQ:{symbol}"
            
            # 记录请求（在实际处理前记录，豁免用户跳过）
            if not is_exempt:
                success = self.rate_limiter.record_request(user_id, username)
                remaining_after = remaining - 1
                if success:
                    self.logger.info(f"用户 {username} 请求图表分析，今日剩余: {remaining_after}/3")
            else:
                remaining_after = 999  # 豁免用户保持无限制
                self.logger.info(f"豁免用户 {username} 请求图表分析，无限制")
            
            # 添加处理中的反应
            await message.add_reaction("🔍")
            
            self.logger.info(f'开始分析图表图片: {chart_image.filename}, Symbol: {symbol}')
            
            # 分析图表
            analysis = await self.chart_analysis_service.analyze_chart_image(chart_image.url, symbol)
            
            # 格式化分析消息
            analysis_message = self.chart_analysis_service.format_analysis_message(analysis)
            
            # 发送私信
            try:
                await message.author.send(f"📊 **TradingView图表分析报告**\n\n{analysis_message}")
                
                # 在频道中提示成功（包含剩余次数信息）
                if is_exempt:
                    limit_info = f"（VIP无限制）"
                else:
                    limit_info = f"（今日剩余 {remaining_after}/3 次）"
                await message.channel.send(f"{message.author.mention} 📊 图表分析报告已发送到您的私信中 {limit_info}")
                
                # 移除处理中反应，添加成功反应
                await message.remove_reaction("🔍", self.user)
                await message.add_reaction("📊")
                
                self.logger.info(f'成功发送图表分析: {symbol}')
                
            except discord.Forbidden:
                await message.channel.send(
                    f"{message.author.mention} 无法发送私信，请检查您的隐私设置"
                )
                await message.remove_reaction("🔍", self.user)
                await message.add_reaction("❌")
            
        except Exception as e:
            self.logger.error(f"处理图表分析请求失败: {e}")
            await message.channel.send(
                f"{message.author.mention} 分析图表时发生错误，请确保图片清晰可读"
            )
            try:
                await message.remove_reaction("🔍", self.user)
                await message.add_reaction("❌")
            except:
                pass
    
    def has_admin_command(self, content: str) -> bool:
        """检查消息是否包含管理员命令"""
        admin_commands = ['!vip_add', '!vip_remove', '!vip_list', '!quota', '!help_admin']
        content_lower = content.lower().strip()
        return any(content_lower.startswith(cmd) for cmd in admin_commands)
    
    def is_admin_user(self, user_id: str) -> bool:
        """检查用户是否有管理员权限"""
        # 定义管理员用户ID列表
        admin_user_ids = [
            '1145170623354638418',  # easton
            '1307107680560873524',  # TestAdmin
            '1257109321947287648'   # easmartalgo
        ]
        return user_id in admin_user_ids
    
    async def handle_admin_command(self, message):
        """处理管理员命令"""
        try:
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            
            # 检查管理员权限
            if not self.is_admin_user(user_id):
                await message.reply("❌ 您没有管理员权限执行此命令")
                return
            
            content = message.content.strip()
            
            if content.lower().startswith('!vip_add'):
                await self.handle_vip_add_command(message, content)
            elif content.lower().startswith('!vip_remove'):
                await self.handle_vip_remove_command(message, content)
            elif content.lower().startswith('!vip_list'):
                await self.handle_vip_list_command(message)
            elif content.lower().startswith('!quota'):
                await self.handle_quota_command(message, content)
            elif content.lower().startswith('!help_admin'):
                await self.handle_admin_help_command(message)
            
        except Exception as e:
            self.logger.error(f"处理管理员命令失败: {e}")
            await message.reply("❌ 执行命令时发生错误")
    
    async def handle_vip_add_command(self, message, content):
        """处理添加VIP命令: !vip_add <user_id> [reason]"""
        try:
            parts = content.split()
            if len(parts) < 2:
                await message.reply("❌ 格式错误！请使用: `!vip_add <用户ID> [原因]`")
                return
            
            target_user_id = parts[1]
            reason = " ".join(parts[2:]) if len(parts) > 2 else "管理员添加VIP"
            
            # 验证用户ID格式
            if not target_user_id.isdigit() or len(target_user_id) < 10:
                await message.reply("❌ 用户ID格式错误！请提供有效的Discord用户ID")
                return
            
            # 检查用户是否已经是VIP
            from models import ExemptUser, get_db_session
            db = get_db_session()
            existing_user = db.query(ExemptUser).filter(ExemptUser.user_id == target_user_id).first()
            
            if existing_user:
                db.close()
                await message.reply(f"⚠️ 用户 {target_user_id} 已经是VIP用户")
                return
            
            # 获取目标用户的用户名（如果可能）
            target_username = "Unknown"
            try:
                target_user = await self.fetch_user(int(target_user_id))
                if target_user:
                    target_username = target_user.display_name or target_user.name
            except:
                pass
            
            # 添加到豁免列表
            new_exempt = ExemptUser(
                user_id=target_user_id,
                username=target_username,
                reason=reason,
                added_by=str(message.author.id)
            )
            
            db.add(new_exempt)
            db.commit()
            db.close()
            
            self.logger.info(f"管理员 {message.author.name} 添加VIP用户: {target_user_id}")
            await message.reply(f"✅ 成功添加VIP用户！\n**用户ID:** {target_user_id}\n**用户名:** {target_username}\n**原因:** {reason}")
            
        except Exception as e:
            self.logger.error(f"处理VIP添加命令失败: {e}")
            await message.reply("❌ 添加VIP用户时发生错误")
    
    async def handle_vip_remove_command(self, message, content):
        """处理移除VIP命令: !vip_remove <user_id>"""
        try:
            parts = content.split()
            if len(parts) != 2:
                await message.reply("❌ 格式错误！请使用: `!vip_remove <用户ID>`")
                return
            
            target_user_id = parts[1]
            
            # 验证用户ID格式
            if not target_user_id.isdigit() or len(target_user_id) < 10:
                await message.reply("❌ 用户ID格式错误！请提供有效的Discord用户ID")
                return
            
            # 查找并删除用户
            from models import ExemptUser, get_db_session
            db = get_db_session()
            exempt_user = db.query(ExemptUser).filter(ExemptUser.user_id == target_user_id).first()
            
            if not exempt_user:
                db.close()
                await message.reply(f"⚠️ 用户 {target_user_id} 不在VIP列表中")
                return
            
            username = exempt_user.username
            db.delete(exempt_user)
            db.commit()
            db.close()
            
            self.logger.info(f"管理员 {message.author.name} 移除VIP用户: {target_user_id}")
            await message.reply(f"✅ 成功移除VIP用户！\n**用户ID:** {target_user_id}\n**用户名:** {username}")
            
        except Exception as e:
            self.logger.error(f"处理VIP移除命令失败: {e}")
            await message.reply("❌ 移除VIP用户时发生错误")
    
    async def handle_vip_list_command(self, message):
        """处理VIP列表命令: !vip_list"""
        try:
            from models import ExemptUser, get_db_session
            db = get_db_session()
            exempt_users = db.query(ExemptUser).order_by(ExemptUser.created_at).all()
            db.close()
            
            if not exempt_users:
                await message.reply("📋 当前没有VIP用户")
                return
            
            vip_list = "📋 **VIP用户列表：**\n\n"
            for i, user in enumerate(exempt_users, 1):
                created_date = user.created_at.strftime("%Y-%m-%d")
                vip_list += f"**{i}.** `{user.user_id}`\n"
                vip_list += f"   • 用户名: {user.username}\n"
                vip_list += f"   • 原因: {user.reason}\n"
                vip_list += f"   • 添加时间: {created_date}\n\n"
            
            # 分割长消息
            if len(vip_list) > 2000:
                # Discord消息长度限制，分割发送
                parts = []
                current_part = "📋 **VIP用户列表：**\n\n"
                
                for i, user in enumerate(exempt_users, 1):
                    created_date = user.created_at.strftime("%Y-%m-%d")
                    user_info = f"**{i}.** `{user.user_id}`\n"
                    user_info += f"   • 用户名: {user.username}\n"
                    user_info += f"   • 原因: {user.reason}\n"
                    user_info += f"   • 添加时间: {created_date}\n\n"
                    
                    if len(current_part + user_info) > 1800:
                        parts.append(current_part)
                        current_part = user_info
                    else:
                        current_part += user_info
                
                if current_part.strip():
                    parts.append(current_part)
                
                for part in parts:
                    await message.reply(part)
            else:
                await message.reply(vip_list)
            
        except Exception as e:
            self.logger.error(f"处理VIP列表命令失败: {e}")
            await message.reply("❌ 获取VIP列表时发生错误")
    
    async def handle_quota_command(self, message, content):
        """处理配额查询命令: !quota [user_id]"""
        try:
            parts = content.split()
            
            # 确定查询目标
            if len(parts) == 1:
                # 查询自己的配额
                target_user_id = str(message.author.id)
                target_username = message.author.display_name or message.author.name
            elif len(parts) == 2:
                # 查询指定用户的配额
                target_user_id = parts[1]
                if not target_user_id.isdigit() or len(target_user_id) < 10:
                    await message.reply("❌ 用户ID格式错误！请提供有效的Discord用户ID")
                    return
                
                # 获取用户名
                target_username = "Unknown"
                try:
                    target_user = await self.fetch_user(int(target_user_id))
                    if target_user:
                        target_username = target_user.display_name or target_user.name
                except:
                    pass
            else:
                await message.reply("❌ 格式错误！请使用: `!quota` 或 `!quota <用户ID>`")
                return
            
            # 检查配额
            can_request, current_count, remaining = self.rate_limiter.check_user_limit(target_user_id, target_username)
            is_vip = remaining == 999
            
            if is_vip:
                status_msg = f"👑 **{target_username}** (`{target_user_id}`)\n"
                status_msg += f"**状态:** VIP无限制 ✨\n"
                status_msg += f"**今日使用:** {current_count} 次\n"
                status_msg += f"**权限:** 无限制使用所有功能"
            else:
                status_msg = f"👤 **{target_username}** (`{target_user_id}`)\n"
                status_msg += f"**状态:** 普通用户\n"
                status_msg += f"**今日使用:** {current_count}/3 次\n"
                status_msg += f"**剩余次数:** {remaining} 次\n"
                status_msg += f"**重置时间:** 每日UTC午夜"
            
            await message.reply(status_msg)
            
        except Exception as e:
            self.logger.error(f"处理配额查询命令失败: {e}")
            await message.reply("❌ 查询配额时发生错误")
    
    async def handle_admin_help_command(self, message):
        """处理管理员帮助命令: !help_admin"""
        help_text = """🛠️ **管理员命令帮助**

**VIP管理命令:**
• `!vip_add <用户ID> [原因]` - 添加VIP用户
• `!vip_remove <用户ID>` - 移除VIP用户
• `!vip_list` - 查看所有VIP用户

**配额管理命令:**
• `!quota` - 查看自己的配额
• `!quota <用户ID>` - 查看指定用户配额

**其他命令:**
• `!help_admin` - 显示此帮助信息

**示例:**
```
!vip_add 1234567890123456789 测试VIP用户
!vip_remove 1234567890123456789
!quota 1234567890123456789
```

**注意:** 只有管理员可以使用这些命令"""
        
        await message.reply(help_text)
        
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
                'default_notifications': str(getattr(guild, 'default_message_notifications', 'unknown')),
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
                if hasattr(guild, 'members') and guild.members:
                    guild_info['statistics'] = {
                        'online_members': sum(1 for m in guild.members if hasattr(m, 'status') and m.status != discord.Status.offline),
                        'bot_count': sum(1 for m in guild.members if m.bot),
                        'human_count': sum(1 for m in guild.members if not m.bot)
                    }
                else:
                    guild_info['statistics'] = {
                        'online_members': 0,
                        'bot_count': 0,
                        'human_count': guild.member_count or 0
                    }
            except Exception as e:
                self.logger.debug(f"计算服务器统计时出错: {e}")
                guild_info['statistics'] = {'error': str(e)}
            
            return guild_info
            
        except Exception as e:
            self.logger.error(f"收集服务器信息时出错: {e}")
            return {
                'id': guild.id,
                'name': getattr(guild, 'name', 'Unknown'),
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
        username = ctx.author.display_name or ctx.author.name
        
        # 检查是否为豁免用户
        can_request, current_count, remaining = self.rate_limiter.check_user_limit(user_id, username)
        if remaining == 999:  # 豁免用户
            embed = discord.Embed(
                title="🌟 豁免用户状态",
                description=f"用户：{username}",
                color=0xffd700
            )
            embed.add_field(name="权限", value="无请求限制", inline=True)
            embed.add_field(name="状态", value="豁免用户", inline=True)
            await ctx.send(embed=embed)
            return
        
        stats = self.rate_limiter.get_user_stats(user_id)
        if stats:
            embed = discord.Embed(
                title="📊 每日请求配额",
                description=f"用户：{username}",
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
                description=f"用户：{username}\n今日尚未使用图表功能",
                color=0x00ff00
            )
            embed.add_field(name="可用次数", value="3/3", inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name='exempt_add')
    @commands.has_permissions(administrator=True)
    async def add_exempt_user(self, ctx, user_id: str, *, reason: str = "管理员豁免"):
        """添加豁免用户（仅管理员）"""
        try:
            # 尝试获取用户信息
            target_user = self.get_user(int(user_id)) or await self.fetch_user(int(user_id))
            username = target_user.display_name or target_user.name
        except:
            username = f"User_{user_id}"
            
        success = self.rate_limiter.add_exempt_user(
            user_id, username, reason, str(ctx.author.id)
        )
        
        if success:
            await ctx.send(f"✅ 成功添加豁免用户: {username} (`{user_id}`)\n原因: {reason}")
        else:
            await ctx.send(f"❌ 添加豁免用户失败，该用户可能已在豁免列表中")
    
    @commands.command(name='exempt_remove')
    @commands.has_permissions(administrator=True)
    async def remove_exempt_user(self, ctx, user_id: str):
        """移除豁免用户（仅管理员）"""
        success = self.rate_limiter.remove_exempt_user(user_id)
        
        if success:
            await ctx.send(f"✅ 成功移除豁免用户: `{user_id}`")
        else:
            await ctx.send(f"❌ 移除豁免用户失败，该用户不在豁免列表中")
    
    @commands.command(name='exempt_list')
    @commands.has_permissions(administrator=True)
    async def list_exempt_users(self, ctx):
        """查看所有豁免用户（仅管理员）"""
        exempt_users = self.rate_limiter.list_exempt_users()
        
        if not exempt_users:
            await ctx.send("📋 当前没有豁免用户")
            return
        
        embed = discord.Embed(
            title="🌟 豁免用户列表",
            description="以下用户不受每日请求限制约束：",
            color=0xffd700
        )
        
        for user in exempt_users[:10]:  # 限制显示10个用户避免消息过长
            embed.add_field(
                name=f"{user['username']}",
                value=f"ID: `{user['user_id']}`\n原因: {user['reason']}\n添加时间: {user['created_at'][:10]}",
                inline=False
            )
        
        if len(exempt_users) > 10:
            embed.set_footer(text=f"显示前10个用户，总计{len(exempt_users)}个豁免用户")
        
        await ctx.send(embed=embed)
    
    async def manual_cleanup_command_direct(self, message):
        """直接处理手动清理命令"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(message.author.id) not in admin_users:
            await message.channel.send("❌ 此命令仅限管理员使用")
            return
            
        days = 1  # 默认清理1天
        await message.channel.send(f"🧹 开始清理最近{days}天的无用消息...")
        
        try:
            deleted_count = await self.channel_cleaner.manual_cleanup(days=days)
            await message.channel.send(f"✅ 清理完成！共删除了 {deleted_count} 条无用消息")
        except Exception as e:
            self.logger.error(f"手动清理失败: {e}")
            await message.channel.send(f"❌ 清理失败: {str(e)}")

    @commands.command(name='cleanup_now')
    async def manual_cleanup_command(self, ctx, days: int = 1):
        """手动清理频道无用消息（仅管理员）"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(ctx.author.id) not in admin_users:
            await ctx.send("❌ 此命令仅限管理员使用")
            return
            
        if days < 1 or days > 7:
            await ctx.send("❌ 清理天数必须在1-7天之间")
            return
        
        await ctx.send(f"🧹 开始清理最近{days}天的无用消息...")
        
        try:
            deleted_count = await self.channel_cleaner.manual_cleanup(days=days)
            await ctx.send(f"✅ 清理完成！共删除了 {deleted_count} 条无用消息")
        except Exception as e:
            self.logger.error(f"手动清理失败: {e}")
            await ctx.send(f"❌ 清理失败: {str(e)}")
    
    async def cleanup_specific_channel_direct(self, message):
        """直接处理清理指定频道命令"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(message.author.id) not in admin_users:
            await message.channel.send("❌ 此命令仅限管理员使用")
            return
        
        await message.channel.send("❌ 请使用格式: `!cleanup_channel <频道ID> [天数]`")

    async def help_admin_command_direct(self, message):
        """直接处理管理员帮助命令"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(message.author.id) not in admin_users:
            await message.channel.send("❌ 此命令仅限管理员使用")
            return
            
        embed = discord.Embed(
            title="🛠️ 管理员命令帮助",
            description="以下是可用的管理员命令：",
            color=0x0099ff
        )
        
        embed.add_field(
            name="🧹 频道清理命令",
            value="`!cleanup_now` - 手动清理今天的无用消息\n"
                  "`!cleanup_status` - 查看清理服务状态\n"
                  "`!cleanup_channel <ID>` - 清理指定频道",
            inline=False
        )
        
        embed.add_field(
            name="👑 VIP管理命令",
            value="`!vip_add <用户ID>` - 添加VIP用户\n"
                  "`!vip_remove <用户ID>` - 移除VIP用户\n"
                  "`!vip_list` - 查看VIP用户列表\n"
                  "`!quota <用户ID>` - 查看用户配额",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ 系统信息",
            value="• 每日自动清理：凌晨2点UTC\n"
                  "• 保留：股票命令、预测、图表分析\n"
                  "• 删除：工作流通知、状态更新",
            inline=False
        )
        
        await message.channel.send(embed=embed)

    async def cleanup_status_command_direct(self, message):
        """直接处理清理状态命令"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(message.author.id) not in admin_users:
            await message.channel.send("❌ 此命令仅限管理员使用")
            return
            
        try:
            embed = discord.Embed(
                title="🧹 频道清理服务状态",
                color=0x00ff00
            )
            
            embed.add_field(
                name="🔄 服务状态",
                value="运行中",
                inline=True
            )
            
            embed.add_field(
                name="⏰ 下次清理时间",
                value="2025-08-12 02:00:00 UTC",
                inline=True
            )
            
            embed.add_field(
                name="📊 清理功能",
                value="• 每日自动清理无用消息\n• 保留股票命令和预测\n• 删除工作流通知",
                inline=False
            )
            
            await message.channel.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"获取清理状态失败: {e}")
            await message.channel.send(f"❌ 获取状态失败: {str(e)}")

    @commands.command(name='cleanup_channel')
    async def cleanup_specific_channel(self, ctx, channel_id: str, days: int = 1):
        """清理指定频道的无用消息（仅管理员）"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(ctx.author.id) not in admin_users:
            await ctx.send("❌ 此命令仅限管理员使用")
            return
            
        if days < 1 or days > 7:
            await ctx.send("❌ 清理天数必须在1-7天之间")
            return
            
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                await ctx.send(f"❌ 找不到频道 ID: {channel_id}")
                return
                
            await ctx.send(f"🧹 开始清理频道 #{channel.name} 最近{days}天的无用消息...")
            
            deleted_count = await self.channel_cleaner.manual_cleanup(channel_id=channel_id, days=days)
            await ctx.send(f"✅ 清理完成！在频道 #{channel.name} 中删除了 {deleted_count} 条无用消息")
        except ValueError:
            await ctx.send("❌ 无效的频道ID")
        except Exception as e:
            self.logger.error(f"清理指定频道失败: {e}")
            await ctx.send(f"❌ 清理失败: {str(e)}")
    
    @commands.command(name='cleanup_status')
    async def cleanup_status_command(self, ctx):
        """查看频道清理服务状态（仅管理员）"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(ctx.author.id) not in admin_users:
            await ctx.send("❌ 此命令仅限管理员使用")
            return
            
        try:
            stats = await self.channel_cleaner.get_cleanup_stats()
            
            embed = discord.Embed(
                title="🧹 频道清理服务状态",
                color=0x00ff00 if stats['is_running'] else 0xff0000
            )
            
            embed.add_field(
                name="服务状态", 
                value="🟢 运行中" if stats['is_running'] else "🔴 已停止", 
                inline=True
            )
            embed.add_field(
                name="清理状态", 
                value="🧹 清理中" if stats['is_cleaning'] else "⏸️ 空闲", 
                inline=True
            )
            embed.add_field(
                name="监控频道数", 
                value=f"{stats['monitor_channels']} 个", 
                inline=True
            )
            
            if stats['next_cleanup']:
                embed.add_field(
                    name="下次清理时间", 
                    value=stats['next_cleanup'].strftime("%Y-%m-%d %H:%M:%S"), 
                    inline=False
                )
            
            embed.set_footer(text="每日自动清理时间: 凌晨2点 (UTC)")
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"获取清理状态失败: {e}")
            await ctx.send(f"❌ 获取状态失败: {str(e)}")
    
    @commands.command(name='help_admin')
    async def help_admin_command(self, ctx):
        """显示管理员命令帮助"""
        # 检查管理员权限
        admin_users = ["1145170623354638418", "1260376806845001778", "1260376806845001779"]  # easton, easmartalgo, TestAdmin
        if str(ctx.author.id) not in admin_users:
            await ctx.send("❌ 此命令仅限管理员使用")
            return
            
        embed = discord.Embed(
            title="🛠️ 管理员命令帮助",
            description="以下是所有可用的管理员命令：",
            color=0x0099ff
        )
        
        # VIP管理命令
        embed.add_field(
            name="👑 VIP管理命令",
            value=(
                "`!exempt_add <用户ID> [原因]` - 添加豁免用户\n"
                "`!exempt_remove <用户ID>` - 移除豁免用户\n"
                "`!exempt_list` - 查看豁免用户列表"
            ),
            inline=False
        )
        
        # 频道清理命令
        embed.add_field(
            name="🧹 频道清理命令",
            value=(
                "`!cleanup_now [天数]` - 手动清理所有监控频道（1-7天）\n"
                "`!cleanup_channel <频道ID> [天数]` - 清理指定频道\n"
                "`!cleanup_status` - 查看清理服务状态"
            ),
            inline=False
        )
        
        # 其他命令
        embed.add_field(
            name="📊 其他命令",
            value=(
                "`!quota` - 查看配额状态\n"
                "`!ping` - 测试机器人延迟\n"
                "`!info` - 查看机器人信息"
            ),
            inline=False
        )
        
        embed.set_footer(text="注意：清理功能会自动识别并保留有用的股票命令和重要消息")
        await ctx.send(embed=embed)
