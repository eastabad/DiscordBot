"""
报告处理器
处理report频道的股票分析报告请求
"""
import re
import logging
from typing import Optional, Tuple
from datetime import datetime
import discord
from tradingview_handler import TradingViewHandler
from gemini_report_generator import GeminiReportGenerator
from rate_limiter import RateLimiter

class ReportHandler:
    """报告请求处理器"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.tv_handler = TradingViewHandler()
        self.gemini_generator = GeminiReportGenerator()
        self.rate_limiter = RateLimiter()
    
    def is_report_request(self, message: discord.Message, report_channel_name: str = "report") -> bool:
        """检查是否是report频道的有效请求"""
        # 检查是否在report频道
        if not message.channel.name or report_channel_name not in message.channel.name.lower():
            return False
        
        # 检查是否包含股票代码和时间框架
        content = message.content.strip()
        if not content:
            return False
        
        # 检查是否是机器人自己的消息
        if message.author.bot:
            return False
        
        return True
    
    def parse_report_request(self, content: str) -> Optional[Tuple[str, str]]:
        """解析报告请求，提取股票代码和时间框架"""
        try:
            # 移除多余空格
            content = content.strip().upper()
            
            # 支持的时间框架格式
            timeframe_patterns = [
                r'\b(15M|15分钟|15MIN)\b',
                r'\b(1H|1小时|1HOUR|60M|60MIN)\b', 
                r'\b(4H|4小时|4HOUR|240M|240MIN)\b'
            ]
            
            # 股票代码模式（2-5个字母）
            symbol_pattern = r'\b([A-Z]{1,5})\b'
            
            # 查找时间框架
            timeframe = None
            for pattern in timeframe_patterns:
                match = re.search(pattern, content)
                if match:
                    tf_text = match.group(1)
                    if any(x in tf_text for x in ['15', 'MIN']):
                        timeframe = '15m'
                    elif any(x in tf_text for x in ['1H', '1小时', '1HOUR', '60']):
                        timeframe = '1h'  
                    elif any(x in tf_text for x in ['4H', '4小时', '4HOUR', '240']):
                        timeframe = '4h'
                    break
            
            # 查找股票代码
            symbol = None
            symbol_matches = re.findall(symbol_pattern, content)
            if symbol_matches:
                # 过滤掉时间框架词汇
                excluded = {'H', 'M', 'MIN', 'HOUR'}
                for match in symbol_matches:
                    if match not in excluded:
                        symbol = match
                        break
            
            if symbol and timeframe:
                self.logger.info(f"解析报告请求成功: {symbol} {timeframe}")
                return (symbol, timeframe)
            else:
                self.logger.warning(f"无法解析报告请求: {content}")
                return None
                
        except Exception as e:
            self.logger.error(f"解析报告请求失败: {e}")
            return None
    
    async def process_report_request(self, message: discord.Message):
        """处理报告请求"""
        try:
            # 检查用户限制
            user_id = str(message.author.id)
            username = message.author.display_name
            
            if not self.rate_limiter.can_make_request(user_id, username):
                remaining_time = self.rate_limiter.get_remaining_time(user_id)
                await message.reply(
                    f"⏰ 您今日的请求次数已用完。请等待 {remaining_time} 后再试。"
                )
                return
            
            # 解析请求
            parsed = self.parse_report_request(message.content)
            if not parsed:
                await message.reply(
                    "❌ 请求格式错误。正确格式：`股票代码 时间框架`\n"
                    "例如：`AAPL 1h` 或 `TSLA 15m` 或 `NVDA 4h`"
                )
                return
            
            symbol, timeframe = parsed
            
            # 获取最新TradingView数据
            latest_data = self.tv_handler.get_latest_data(symbol, timeframe)
            if not latest_data:
                await message.reply(
                    f"❌ 未找到 {symbol} ({timeframe}) 的TradingView数据。\n"
                    f"请确保：\n"
                    f"1. 股票代码正确\n"
                    f"2. TradingView已推送该时间框架的数据\n"
                    f"3. 数据在最近时间内更新"
                )
                return
            
            # 发送处理中消息
            processing_msg = await message.reply(
                f"📊 正在生成 {symbol} ({timeframe}) 的AI分析报告..."
            )
            
            # 生成报告
            try:
                report = self.gemini_generator.generate_stock_report(
                    latest_data, 
                    message.content
                )
                
                # 更新用户请求计数
                self.rate_limiter.record_request(user_id, username)
                
                # 发送私信
                try:
                    await message.author.send(f"📋 **{symbol} 分析报告**\n\n{report}")
                    await processing_msg.edit(content=f"✅ {symbol} 分析报告已发送到您的私信中")
                except discord.Forbidden:
                    # 如果无法发送私信，直接在频道回复
                    # 由于报告较长，分段发送
                    await processing_msg.edit(content=f"📋 **{symbol} 分析报告**")
                    
                    # 分段发送报告（Discord消息限制2000字符）
                    report_chunks = self._split_message(report, 1900)
                    for chunk in report_chunks:
                        await message.channel.send(f"```\n{chunk}\n```")
                
            except Exception as e:
                self.logger.error(f"生成报告失败: {e}")
                await processing_msg.edit(
                    content=f"❌ 生成 {symbol} 报告时发生错误，请稍后重试"
                )
                
        except Exception as e:
            self.logger.error(f"处理报告请求失败: {e}")
            await message.reply("❌ 处理请求时发生错误，请稍后重试")
    
    def _split_message(self, text: str, max_length: int = 1900) -> list:
        """将长消息分割成多个部分"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_example_message(self) -> str:
        """获取示例使用说明"""
        return """
📊 **股票分析报告使用指南**

在 #report 频道发送以下格式的消息：
`股票代码 时间框架`

**支持的时间框架：**
• `15m` 或 `15分钟` - 15分钟数据
• `1h` 或 `1小时` - 1小时数据  
• `4h` 或 `4小时` - 4小时数据

**示例：**
• `AAPL 1h` - 获取苹果股票1小时分析
• `TSLA 15m` - 获取特斯拉股票15分钟分析
• `NVDA 4h` - 获取英伟达股票4小时分析

**注意：**
• 每天限制3次请求
• 分析基于最新的TradingView技术指标数据
• 报告将通过私信发送
"""