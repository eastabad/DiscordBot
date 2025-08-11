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
        
        # 常见股票交易所映射
        self.stock_exchange_map = {
            # NYSE 股票
            'PFE': 'NYSE:PFE',  # 辉瑞
            'JPM': 'NYSE:JPM',  # 摩根大通
            'JNJ': 'NYSE:JNJ',  # 强生
            'BAC': 'NYSE:BAC',  # 美国银行
            'WMT': 'NYSE:WMT',  # 沃尔玛
            'XOM': 'NYSE:XOM',  # 埃克森美孚
            'CVX': 'NYSE:CVX',  # 雪佛龙
            'KO': 'NYSE:KO',   # 可口可乐
            'MCD': 'NYSE:MCD', # 麦当劳
            'DIS': 'NYSE:DIS', # 迪士尼
            'HD': 'NYSE:HD',   # 家得宝
            'VZ': 'NYSE:VZ',   # 威瑞森
            'PG': 'NYSE:PG',   # 宝洁
            'IBM': 'NYSE:IBM', # IBM
            'GE': 'NYSE:GE',   # 通用电气
            'T': 'NYSE:T',     # AT&T
            'F': 'NYSE:F',     # 福特
            'GM': 'NYSE:GM',   # 通用汽车
            'C': 'NYSE:C',     # 花旗
            'WFC': 'NYSE:WFC', # 富国银行
            'GS': 'NYSE:GS',   # 高盛
            'MS': 'NYSE:MS',   # 摩根士丹利
            'UNH': 'NYSE:UNH', # 联合健康
            'V': 'NYSE:V',     # Visa
            'MA': 'NYSE:MA',   # 万事达
            'LLY': 'NYSE:LLY', # 礼来
            'ABT': 'NYSE:ABT', # 雅培
            'NKE': 'NYSE:NKE', # 耐克
            'COP': 'NYSE:COP', # 康菲石油
            'ACN': 'NYSE:ACN', # 埃森哲
            'UPS': 'NYSE:UPS', # 联合包裹
            'LOW': 'NYSE:LOW', # 劳氏
            'BMY': 'NYSE:BMY', # 百时美施贵宝
            'MDT': 'NYSE:MDT', # 美敦力
            'BA': 'NYSE:BA',   # 波音
            'CAT': 'NYSE:CAT', # 卡特彼勒
            'DE': 'NYSE:DE',   # 迪尔
            'MMM': 'NYSE:MMM', # 3M
            'SPGI': 'NYSE:SPGI', # 标普全球
            'BLK': 'NYSE:BLK', # 贝莱德
            'AXP': 'NYSE:AXP', # 美国运通
            'TRV': 'NYSE:TRV', # 旅行者
            'NOW': 'NYSE:NOW', # ServiceNow
            'BABA': 'NYSE:BABA', # 阿里巴巴
            'NIO': 'NYSE:NIO',   # 蔚来
            'XPEV': 'NYSE:XPEV', # 小鹏
            'TME': 'NYSE:TME',   # 腾讯音乐
            'DIDI': 'NYSE:DIDI', # 滴滴
            'UBER': 'NYSE:UBER', # Uber
            
            # NASDAQ 股票
            'AAPL': 'NASDAQ:AAPL', # 苹果
            'MSFT': 'NASDAQ:MSFT', # 微软
            'GOOGL': 'NASDAQ:GOOGL', # 谷歌A
            'GOOG': 'NASDAQ:GOOG', # 谷歌C
            'AMZN': 'NASDAQ:AMZN', # 亚马逊
            'TSLA': 'NASDAQ:TSLA', # 特斯拉
            'META': 'NASDAQ:META', # Meta
            'NVDA': 'NASDAQ:NVDA', # 英伟达
            'AMD': 'NASDAQ:AMD',   # AMD
            'INTC': 'NASDAQ:INTC', # 英特尔
            'COST': 'NASDAQ:COST', # 好市多
            'ADBE': 'NASDAQ:ADBE', # Adobe
            'NFLX': 'NASDAQ:NFLX', # Netflix
            'PYPL': 'NASDAQ:PYPL', # PayPal
            'CMCSA': 'NASDAQ:CMCSA', # 康卡斯特
            'PEP': 'NASDAQ:PEP', # 百事可乐
            'TXN': 'NASDAQ:TXN', # 德州仪器
            'QCOM': 'NASDAQ:QCOM', # 高通
            'HON': 'NASDAQ:HON', # 霍尼韦尔
            'SBUX': 'NASDAQ:SBUX', # 星巴克
            'AMGN': 'NASDAQ:AMGN', # 安进
            'GILD': 'NASDAQ:GILD', # 吉利德
            'JD': 'NASDAQ:JD',     # 京东
            'PDD': 'NASDAQ:PDD',   # 拼多多
            'NTES': 'NASDAQ:NTES', # 网易
            'BIDU': 'NASDAQ:BIDU', # 百度
            'LI': 'NASDAQ:LI',     # 理想
            'BILI': 'NASDAQ:BILI', # 哔哩哔哩
            'IQ': 'NASDAQ:IQ',     # 爱奇艺
            'LYFT': 'NASDAQ:LYFT', # Lyft
        }
        
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
        
        # 匹配模式: 股票符号,时间框架 (支持中英文逗号)
        patterns = [
            r'([A-Z][A-Z:]*[A-Z])[,，]\s*(\d+[smhdwMy])',  # AAPL,15h 或 AAPL，15m (中英文逗号)
            r'([A-Z][A-Z:]*[A-Z])\s+(\d+[smhdwMy])',        # AAPL 15h (空格分隔)
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
    
    def normalize_timeframe(self, timeframe: str) -> Optional[str]:
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
                # 检查股票交易所映射
                if symbol in self.stock_exchange_map:
                    symbol = self.stock_exchange_map[symbol]
                    self.logger.info(f'使用交易所映射: {symbol}')
                else:
                    # 默认添加NASDAQ前缀给未知美股
                    symbol = f"NASDAQ:{symbol}"
                    self.logger.info(f'使用默认NASDAQ前缀: {symbol}')
            
            # 构建Shared Layout API请求（参数有限）
            payload = {
                "symbol": symbol,
                "interval": normalized_timeframe,
                "width": 1920,
                "height": 1080
            }
            
            headers = {
                "x-api-key": self.config.chart_img_api_key,
                "content-type": "application/json"
            }
            
            # 如果有TradingView会话信息，添加到headers（用于私有布局访问）
            if self.config.tradingview_session_id and self.config.tradingview_session_id_sign:
                headers["tradingview-session-id"] = self.config.tradingview_session_id
                headers["tradingview-session-id-sign"] = self.config.tradingview_session_id_sign
            
            self.logger.info(f'请求图表: {symbol} {timeframe} -> {normalized_timeframe}')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=180)  # 180秒超时（Layout Chart Storage需要更长时间）
                ) as response:
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'image' in content_type:
                            # 直接返回图片数据
                            image_data = await response.read()
                            self.logger.info(f'成功获取图表: {symbol} {timeframe}, 大小: {len(image_data)} bytes')
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