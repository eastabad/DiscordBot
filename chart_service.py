"""
图表服务模块
处理chart-img API调用和股票图表生成
"""

import aiohttp
import logging
import re
import base64
from typing import Optional, Tuple
import asyncio

class ChartService:
    """图表服务类"""
    
    def __init__(self, config):
        """初始化图表服务"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_url = f"https://api.chart-img.com/v2/tradingview/layout-chart/{self.config.layout_id}"
        
    def parse_command(self, content: str) -> Optional[Tuple[str, str]]:
        """
        解析用户输入的命令
        格式: AAPL,15h 或 NASDAQ:AAPL,1d 等
        返回: (symbol, timeframe) 或 None
        """
        # 移除@bot提及和其他多余内容
        cleaned_content = re.sub(r'<@!?\d+>', '', content).strip()
        cleaned_content = re.sub(r'@\w+', '', cleaned_content).strip()
        
        # 移除@提及检查，直接解析命令
        
        # 匹配模式: 股票符号,时间框架
        patterns = [
            r'([A-Z][A-Z:]*[A-Z]),\s*(\d+[smhdwMy])',  # AAPL,15h 或 NASDAQ:AAPL,1d
            r'([A-Z][A-Z:]*[A-Z])\s+(\d+[smhdwMy])',   # AAPL 15h
            r'([A-Z][A-Z:]*[A-Z]),(\d+[smhdwMy])',     # AAPL,15h (无空格)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_content, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                timeframe = match.group(2).lower()
                
                # 验证时间框架格式 - 检查是否为支持的时间框架
                valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']
                if timeframe in valid_timeframes:
                    self.logger.info(f'解析命令成功: symbol={symbol}, timeframe={timeframe}')
                    return symbol, timeframe
                else:
                    self.logger.warning(f'无效时间框架: {timeframe}，支持的格式: {valid_timeframes}')
                    return None
        
        self.logger.warning(f'无法解析命令: {content}')
        return None
    
    def normalize_timeframe(self, timeframe: str) -> str:
        """
        标准化时间框架格式
        """
        # 映射表：用户输入 -> chart-img API格式
        timeframe_map = {
            # 分钟
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            # 小时  
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '12h': '12h',
            # 天
            '1d': '1D', '1D': '1D',
            # 周
            '1w': '1W', '1W': '1W',
            # 月
            '1M': '1M'
        }
        
        normalized = timeframe_map.get(timeframe)
        if normalized is None:
            self.logger.warning(f'不支持的时间框架: {timeframe}')
        return normalized
    
    async def get_chart(self, symbol: str, timeframe: str) -> Optional[bytes]:
        """
        调用chart-img API获取图表
        返回图片的bytes数据
        """
        try:
            normalized_timeframe = self.normalize_timeframe(timeframe)
            if normalized_timeframe is None:
                self.logger.error(f'不支持的时间框架: {timeframe}')
                return None
            
            # 确保symbol包含交易所前缀
            if ':' not in symbol:
                # 默认添加NASDAQ前缀给美股
                symbol = f"NASDAQ:{symbol}"
            
            # 构建Layout Chart API请求
            payload = {
                "symbol": symbol,
                "interval": normalized_timeframe,
                "width": 1920,
                "height": 1080,
                "format": "png",
                "delay": 8000  # 等待8秒让技术指标完全加载
            }
            
            headers = {
                "X-API-Key": self.config.chart_img_api_key,
                "Content-Type": "application/json"
            }
            
            # 如果有TradingView会话信息，添加到headers
            if self.config.tradingview_session_id and self.config.tradingview_session_id_sign:
                headers["X-TradingView-SessionId"] = self.config.tradingview_session_id
                headers["X-TradingView-SessionId-Sign"] = self.config.tradingview_session_id_sign
            
            self.logger.info(f'请求图表: {symbol} {timeframe} -> {normalized_timeframe}')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'image' in content_type:
                            # 直接返回图片数据
                            image_data = await response.read()
                            self.logger.info(f'成功获取图表: {symbol} {timeframe}, 大小: {len(image_data)} bytes')
                            return image_data
                        else:
                            # 可能是JSON响应包含base64图片
                            response_data = await response.json()
                            if 'image' in response_data:
                                # 如果是base64编码的图片
                                if response_data['image'].startswith('data:image'):
                                    base64_data = response_data['image'].split(',')[1]
                                    image_data = base64.b64decode(base64_data)
                                    self.logger.info(f'成功获取图表(base64): {symbol} {timeframe}')
                                    return image_data
                    else:
                        error_text = await response.text()
                        self.logger.error(f'API请求失败: {response.status} - {error_text}')
                        
        except asyncio.TimeoutError:
            self.logger.error(f'API请求超时: {symbol} {timeframe}')
        except Exception as e:
            self.logger.error(f'获取图表失败: {symbol} {timeframe} - {e}')
        
        return None
    
    def format_success_message(self, symbol: str, timeframe: str) -> str:
        """格式化成功消息"""
        return f"📊 {symbol} {timeframe} 图表已生成并发送到您的私信中"
    
    def format_error_message(self, symbol: str, timeframe: str, error: str = "未知错误") -> str:
        """格式化错误消息"""
        return f"❌ 无法获取 {symbol} {timeframe} 图表: {error}"
    
    def format_chart_dm_content(self, symbol: str, timeframe: str) -> str:
        """格式化私信内容"""
        return f"📈 {symbol} {timeframe} 技术分析图表"