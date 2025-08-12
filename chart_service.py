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
        
        # SP500 + 纳指100 完整股票交易所映射
        self.stock_exchange_map = {
            # === NYSE 交易所股票 (SP500主要成分) ===
            
            # 金融服务
            'JPM': 'NYSE:JPM',   # 摩根大通
            'BAC': 'NYSE:BAC',   # 美国银行
            'WFC': 'NYSE:WFC',   # 富国银行
            'GS': 'NYSE:GS',     # 高盛集团
            'MS': 'NYSE:MS',     # 摩根士丹利
            'C': 'NYSE:C',       # 花旗集团
            'AXP': 'NYSE:AXP',   # 美国运通
            'BLK': 'NYSE:BLK',   # 贝莱德
            'SPGI': 'NYSE:SPGI', # 标普全球
            'ICE': 'NYSE:ICE',   # 洲际交易所
            'CME': 'NASDAQ:CME', # 芝加哥商品交易所
            'TRV': 'NYSE:TRV',   # 旅行者公司
            'ALL': 'NYSE:ALL',   # 好事达保险
            'USB': 'NYSE:USB',   # 美国合众银行
            'PNC': 'NYSE:PNC',   # PNC金融服务
            'COF': 'NYSE:COF',   # 第一资本金融
            'MMC': 'NYSE:MMC',   # 威达信集团
            'AON': 'NYSE:AON',   # 怡安集团
            'AIG': 'NYSE:AIG',   # 美国国际集团
            'PRU': 'NYSE:PRU',   # 保德信金融
            'MET': 'NYSE:MET',   # 大都会人寿
            'AFL': 'NYSE:AFL',   # Aflac保险
            'TFC': 'NYSE:TFC',   # Truist金融
            'STT': 'NYSE:STT',   # 道富银行
            'BK': 'NYSE:BK',     # 纽约梅隆银行
            'SCHW': 'NYSE:SCHW', # 嘉信理财
            
            # 医疗保健
            'UNH': 'NYSE:UNH',   # 联合健康集团
            'JNJ': 'NYSE:JNJ',   # 强生公司
            'PFE': 'NYSE:PFE',   # 辉瑞制药
            'ABT': 'NYSE:ABT',   # 雅培实验室
            'TMO': 'NYSE:TMO',   # 赛默飞世尔科技
            'DHR': 'NYSE:DHR',   # 丹纳赫公司
            'BMY': 'NYSE:BMY',   # 百时美施贵宝
            'LLY': 'NYSE:LLY',   # 礼来公司
            'MDT': 'NYSE:MDT',   # 美敦力公司
            'SYK': 'NYSE:SYK',   # 史赛克公司
            'BSX': 'NYSE:BSX',   # 波士顿科学
            'ELV': 'NYSE:ELV',   # Elevance Health
            'CVS': 'NYSE:CVS',   # CVS Health
            'CI': 'NYSE:CI',     # Cigna集团
            'HUM': 'NYSE:HUM',   # Humana
            'ZTS': 'NYSE:ZTS',   # 硕腾公司
            'DXCM': 'NASDAQ:DXCM', # 德康医疗
            'BDX': 'NYSE:BDX',   # 贝克顿·迪金森
            'BAX': 'NYSE:BAX',   # 百特国际
            'WAT': 'NYSE:WAT',   # 沃特世公司
            'A': 'NYSE:A',       # 安捷伦科技
            'IQV': 'NYSE:IQV',   # IQVIA控股
            'RMD': 'NYSE:RMD',   # 瑞思迈
            'MTD': 'NYSE:MTD',   # 墨提斯公司
            'IDXX': 'NASDAQ:IDXX', # IDEXX实验室
            'DGX': 'NYSE:DGX',   # Quest Diagnostics
            'LH': 'NYSE:LH',     # LabCorp
            'SOLV': 'NASDAQ:SOLV', # Solventum
            
            # 工业
            'BA': 'NYSE:BA',     # 波音公司
            'CAT': 'NYSE:CAT',   # 卡特彼勒
            'RTX': 'NYSE:RTX',   # 雷神技术
            'DE': 'NYSE:DE',     # 迪尔公司
            'UPS': 'NYSE:UPS',   # 联合包裹服务
            'LMT': 'NYSE:LMT',   # 洛克希德·马丁
            'NOC': 'NYSE:NOC',   # 诺斯罗普·格鲁曼
            'GD': 'NYSE:GD',     # 通用动力
            'MMM': 'NYSE:MMM',   # 3M公司
            'GE': 'NYSE:GE',     # 通用电气
            'HON': 'NASDAQ:HON', # 霍尼韦尔国际
            'ITW': 'NYSE:ITW',   # 伊利诺伊工具
            'EMR': 'NYSE:EMR',   # 艾默生电气
            'ETN': 'NYSE:ETN',   # 伊顿公司
            'PH': 'NYSE:PH',     # 派克汉尼汾
            'CMI': 'NYSE:CMI',   # 康明斯
            'FDX': 'NYSE:FDX',   # 联邦快递
            'CSX': 'NASDAQ:CSX', # CSX运输
            'NSC': 'NYSE:NSC',   # 诺福克南方铁路
            'UNP': 'NYSE:UNP',   # 联合太平洋
            'LUV': 'NYSE:LUV',   # 西南航空
            'AAL': 'NASDAQ:AAL', # 美国航空
            'DAL': 'NYSE:DAL',   # 达美航空
            'UAL': 'NASDAQ:UAL', # 联合大陆航空
            'UBER': 'NYSE:UBER', # 优步
            'WM': 'NYSE:WM',     # 废物管理公司
            'RSG': 'NYSE:RSG',   # 共和废品处理
            'CARR': 'NYSE:CARR', # 开利公司
            'OTIS': 'NYSE:OTIS', # 奥的斯电梯
            'PWR': 'NYSE:PWR',   # Quanta Services
            'VRSK': 'NASDAQ:VRSK', # Verisk Analytics
            'ROL': 'NYSE:ROL',   # Rollins公司
            'J': 'NYSE:J',       # 雅各布斯工程
            'FAST': 'NASDAQ:FAST', # Fastenal公司
            'PAYX': 'NASDAQ:PAYX', # Paychex
            'ODFL': 'NASDAQ:ODFL', # Old Dominion货运
            'PCAR': 'NASDAQ:PCAR', # PACCAR公司
            
            # 消费必需品
            'WMT': 'NYSE:WMT',   # 沃尔玛
            'PG': 'NYSE:PG',     # 宝洁公司
            'KO': 'NYSE:KO',     # 可口可乐
            'PEP': 'NASDAQ:PEP', # 百事可乐
            'COST': 'NASDAQ:COST', # 好市多
            'MCD': 'NYSE:MCD',   # 麦当劳
            'TGT': 'NYSE:TGT',   # 塔吉特
            'SBUX': 'NASDAQ:SBUX', # 星巴克
            'KMB': 'NYSE:KMB',   # 金佰利
            'CL': 'NYSE:CL',     # 高露洁棕榄
            'GIS': 'NYSE:GIS',   # 通用磨坊
            'K': 'NYSE:K',       # 家乐氏
            'HSY': 'NYSE:HSY',   # 好时公司
            'SYY': 'NYSE:SYY',   # Sysco公司
            'MKC': 'NYSE:MKC',   # 味好美
            'CPB': 'NASDAQ:CPB', # 金宝汤公司
            'CAG': 'NYSE:CAG',   # 康尼格拉品牌
            'TSN': 'NYSE:TSN',   # 泰森食品
            'HRL': 'NYSE:HRL',   # 荷美尔食品
            'SJM': 'NYSE:SJM',   # J.M.史摩克
            'KR': 'NYSE:KR',     # 克罗格
            'WBA': 'NASDAQ:WBA', # 沃尔格林
            'MNST': 'NASDAQ:MNST', # Monster Beverage
            'KDP': 'NASDAQ:KDP', # Keurig Dr Pepper
            'STZ': 'NYSE:STZ',   # 星座品牌
            'TAP': 'NYSE:TAP',   # 摩森康胜
            'BF.B': 'NYSE:BF.B', # Brown-Forman
            'MDLZ': 'NASDAQ:MDLZ', # 亿滋国际
            'EL': 'NYSE:EL',     # 雅诗兰黛
            'CLX': 'NYSE:CLX',   # 高乐氏
            'CHD': 'NYSE:CHD',   # Church & Dwight
            'ADM': 'NYSE:ADM',   # 阿彻丹尼尔斯米德兰
            'CTVA': 'NYSE:CTVA', # Corteva
            
            # 消费可选
            'AMZN': 'NASDAQ:AMZN', # 亚马逊
            'TSLA': 'NASDAQ:TSLA', # 特斯拉
            'HD': 'NYSE:HD',     # 家得宝
            'NKE': 'NYSE:NKE',   # 耐克
            'DIS': 'NYSE:DIS',   # 迪士尼
            'LOW': 'NYSE:LOW',   # 劳氏
            'F': 'NYSE:F',       # 福特汽车
            'GM': 'NYSE:GM',     # 通用汽车
            'TJX': 'NYSE:TJX',   # TJX公司
            'BKNG': 'NASDAQ:BKNG', # Booking Holdings
            'ABNB': 'NASDAQ:ABNB', # Airbnb
            'MAR': 'NASDAQ:MAR', # 万豪国际
            'HLT': 'NYSE:HLT',   # 希尔顿全球
            'MGM': 'NYSE:MGM',   # 美高梅度假村
            'CCL': 'NYSE:CCL',   # 嘉年华游轮
            'RCL': 'NYSE:RCL',   # 皇家加勒比游轮
            'NCLH': 'NYSE:NCLH', # 挪威游轮
            'YUM': 'NYSE:YUM',   # 百胜餐饮集团
            'CMG': 'NYSE:CMG',   # Chipotle Mexican Grill
            'ORLY': 'NASDAQ:ORLY', # O'Reilly汽车配件
            'AZO': 'NYSE:AZO',   # AutoZone
            'AAP': 'NYSE:AAP',   # Advance Auto Parts
            'BBY': 'NYSE:BBY',   # 百思买
            'EBAY': 'NASDAQ:EBAY', # eBay
            'ETSY': 'NASDAQ:ETSY', # Etsy
            'EXPE': 'NASDAQ:EXPE', # Expedia集团
            'LULU': 'NASDAQ:LULU', # Lululemon运动服装
            'ROST': 'NASDAQ:ROST', # Ross Stores
            'DG': 'NYSE:DG',     # Dollar General
            'DLTR': 'NASDAQ:DLTR', # Dollar Tree
            'GPS': 'NYSE:GPS',   # Gap公司
            'RL': 'NYSE:RL',     # 拉夫劳伦
            'TPG': 'NYSE:TPG',   # TPG公司
            'LVS': 'NYSE:LVS',   # 拉斯维加斯金沙
            'WYNN': 'NASDAQ:WYNN', # 永利度假村
            'GPC': 'NYSE:GPC',   # Genuine Parts公司
            'PHM': 'NYSE:PHM',   # PulteGroup
            'NVR': 'NYSE:NVR',   # NVR公司
            'DHI': 'NYSE:DHI',   # D.R. Horton
            'LEN': 'NYSE:LEN',   # Lennar公司
            'WHR': 'NYSE:WHR',   # 惠而浦
            'HAS': 'NASDAQ:HAS', # 孩之宝
            'MAT': 'NASDAQ:MAT', # 美泰
            'POOL': 'NASDAQ:POOL', # Pool公司
            'LKQ': 'NASDAQ:LKQ', # LKQ公司
            
            # 能源
            'XOM': 'NYSE:XOM',   # 埃克森美孚
            'CVX': 'NYSE:CVX',   # 雪佛龙
            'COP': 'NYSE:COP',   # 康菲石油
            'EOG': 'NYSE:EOG',   # EOG Resources
            'SLB': 'NYSE:SLB',   # 斯伦贝谢
            'PXD': 'NASDAQ:PXD', # Pioneer Natural Resources
            'KMI': 'NYSE:KMI',   # Kinder Morgan
            'OKE': 'NYSE:OKE',   # ONEOK
            'WMB': 'NYSE:WMB',   # Williams Companies
            'MPC': 'NYSE:MPC',   # Marathon Petroleum
            'VLO': 'NYSE:VLO',   # Valero Energy
            'PSX': 'NYSE:PSX',   # Phillips 66
            'BKR': 'NASDAQ:BKR', # Baker Hughes
            'HAL': 'NYSE:HAL',   # 哈里伯顿
            'DVN': 'NYSE:DVN',   # Devon Energy
            'FANG': 'NASDAQ:FANG', # Diamondback Energy
            'EQT': 'NYSE:EQT',   # EQT公司
            'APA': 'NASDAQ:APA', # APA公司
            'OXY': 'NYSE:OXY',   # 西方石油
            'HES': 'NYSE:HES',   # 赫斯公司
            'CTRA': 'NYSE:CTRA', # Coterra Energy
            'MRO': 'NYSE:MRO',   # Marathon Oil
            'TPG': 'NYSE:TPG',   # Texas Pacific Group
            'CVE': 'NYSE:CVE',   # Cenovus Energy
            'CNQ': 'NYSE:CNQ',   # Canadian Natural Resources
            'SU': 'NYSE:SU',     # Suncor Energy
            'TTE': 'NYSE:TTE',   # TotalEnergies
            'ENB': 'NYSE:ENB',   # Enbridge
            'TRP': 'NYSE:TRP',   # TC Energy
            'EPD': 'NYSE:EPD',   # Enterprise Products Partners
            'ET': 'NYSE:ET',     # Energy Transfer
            'KMX': 'NYSE:KMX',   # CarMax
            'TRGP': 'NYSE:TRGP', # Targa Resources
            
            # 公用事业
            'NEE': 'NYSE:NEE',   # NextEra Energy
            'SO': 'NYSE:SO',     # Southern Company
            'DUK': 'NYSE:DUK',   # 杜克能源
            'AEP': 'NASDAQ:AEP', # American Electric Power
            'EXC': 'NASDAQ:EXC', # Exelon公司
            'XEL': 'NASDAQ:XEL', # Xcel Energy
            'SRE': 'NYSE:SRE',   # Sempra Energy
            'D': 'NYSE:D',       # Dominion Energy
            'PCG': 'NYSE:PCG',   # 太平洋天然气电力
            'PEG': 'NYSE:PEG',   # Public Service Enterprise Group
            'EIX': 'NYSE:EIX',   # Edison International
            'WEC': 'NYSE:WEC',   # WEC Energy Group
            'AWK': 'NYSE:AWK',   # American Water Works
            'PPL': 'NYSE:PPL',   # PPL公司
            'CMS': 'NYSE:CMS',   # CMS Energy
            'DTE': 'NYSE:DTE',   # DTE Energy
            'ATO': 'NYSE:ATO',   # Atmos Energy
            'ES': 'NYSE:ES',     # Eversource Energy
            'FE': 'NYSE:FE',     # FirstEnergy
            'AES': 'NYSE:AES',   # AES公司
            'NI': 'NYSE:NI',     # NiSource
            'CNP': 'NYSE:CNP',   # CenterPoint Energy
            'ETR': 'NYSE:ETR',   # Entergy公司
            'EVRG': 'NYSE:EVRG', # Evergy公司
            'PNW': 'NYSE:PNW',   # Pinnacle West Capital
            'LNT': 'NASDAQ:LNT', # Alliant Energy
            'AEE': 'NYSE:AEE',   # Ameren公司
            'VST': 'NYSE:VST',   # Vistra Corp
            'CEG': 'NASDAQ:CEG', # Constellation Energy
            
            # 房地产
            'AMT': 'NYSE:AMT',   # American Tower
            'PLD': 'NYSE:PLD',   # Prologis
            'CCI': 'NYSE:CCI',   # Crown Castle
            'EQIX': 'NASDAQ:EQIX', # Equinix
            'WELL': 'NYSE:WELL', # Welltower
            'DLR': 'NYSE:DLR',   # Digital Realty Trust
            'O': 'NYSE:O',       # Realty Income
            'SBAC': 'NASDAQ:SBAC', # SBA Communications
            'PSA': 'NYSE:PSA',   # Public Storage
            'EXR': 'NYSE:EXR',   # Extended Stay America
            'AVB': 'NYSE:AVB',   # AvalonBay Communities
            'EQR': 'NYSE:EQR',   # Equity Residential
            'INVH': 'NYSE:INVH', # Invitation Homes
            'MAA': 'NYSE:MAA',   # Mid-America Apartment Communities
            'ESS': 'NYSE:ESS',   # Essex Property Trust
            'UDR': 'NYSE:UDR',   # UDR公司
            'CPT': 'NYSE:CPT',   # Camden Property Trust
            'SPG': 'NYSE:SPG',   # Simon Property Group
            'KIM': 'NYSE:KIM',   # Kimco Realty
            'REG': 'NASDAQ:REG', # Regency Centers
            'BXP': 'NYSE:BXP',   # Boston Properties
            'VTR': 'NYSE:VTR',   # Ventas
            'HCP': 'NYSE:HCP',   # Healthpeak Properties
            'HST': 'NYSE:HST',   # Host Hotels & Resorts
            'RHP': 'NYSE:RHP',   # Ryman Hospitality Properties
            'PEAK': 'NYSE:PEAK', # Healthpeak Properties
            'DOC': 'NYSE:DOC',   # Physicians Realty Trust
            'WPC': 'NYSE:WPC',   # W. P. Carey
            'STAG': 'NYSE:STAG', # Stag Industrial
            'ELS': 'NYSE:ELS',   # Equity Lifestyle Properties
            'SUI': 'NYSE:SUI',   # Sun Communities
            'AMH': 'NYSE:AMH',   # American Homes 4 Rent
            'CUBE': 'NYSE:CUBE', # CubeSmart
            'LSI': 'NYSE:LSI',   # Life Storage
            'FRT': 'NYSE:FRT',   # Federal Realty Investment Trust
            'KRC': 'NYSE:KRC',   # Kilroy Realty
            'VNO': 'NYSE:VNO',   # Vornado Realty Trust
            'SLG': 'NYSE:SLG',   # SL Green Realty
            'BRX': 'NYSE:BRX',   # Brixmor Property Group
            'FR': 'NYSE:FR',     # First Industrial Realty Trust
            'PLD': 'NYSE:PLD',   # Prologis (重复检查)
            
            # 材料
            'LIN': 'NYSE:LIN',   # 林德集团
            'SHW': 'NYSE:SHW',   # 宣伟公司
            'APD': 'NYSE:APD',   # Air Products and Chemicals
            'FCX': 'NYSE:FCX',   # 自由港迈克墨伦铜金公司
            'NUE': 'NYSE:NUE',   # 纽柯钢铁
            'ECL': 'NYSE:ECL',   # 艺康集团
            'NEM': 'NYSE:NEM',   # 纽蒙特公司
            'DOW': 'NYSE:DOW',   # 陶氏公司
            'DD': 'NYSE:DD',     # 杜邦公司
            'LYB': 'NYSE:LYB',   # LyondellBasell Industries
            'MLM': 'NYSE:MLM',   # Martin Marietta Materials
            'VMC': 'NYSE:VMC',   # Vulcan Materials
            'PPG': 'NYSE:PPG',   # PPG工业公司
            'IFF': 'NYSE:IFF',   # 国际香料香精
            'EMN': 'NYSE:EMN',   # 伊士曼化工
            'RPM': 'NYSE:RPM',   # RPM International
            'CF': 'NYSE:CF',     # CF Industries Holdings
            'MOS': 'NYSE:MOS',   # Mosaic公司
            'FMC': 'NYSE:FMC',   # FMC公司
            'ALB': 'NYSE:ALB',   # Albemarle公司
            'CE': 'NYSE:CE',     # Celanese公司
            'AVY': 'NYSE:AVY',   # Avery Dennison
            'BALL': 'NYSE:BALL', # Ball公司
            'PKG': 'NYSE:PKG',   # Packaging Corporation of America
            'IP': 'NYSE:IP',     # International Paper
            'WRK': 'NYSE:WRK',   # WestRock公司
            'SON': 'NYSE:SON',   # Sonoco Products
            'SEE': 'NYSE:SEE',   # Sealed Air
            'AMCR': 'NYSE:AMCR', # Amcor公司
            'CCK': 'NYSE:CCK',   # Crown Holdings
            'SWK': 'NYSE:SWK',   # Stanley Black & Decker
            'MHK': 'NYSE:MHK',   # Mohawk Industries
            'X': 'NYSE:X',       # 美国钢铁公司
            'STLD': 'NASDAQ:STLD', # Steel Dynamics
            'RS': 'NYSE:RS',     # Reliance Steel & Aluminum
            'AA': 'NYSE:AA',     # Alcoa公司
            
            # 通信服务
            'META': 'NASDAQ:META', # Meta Platforms
            'GOOGL': 'NASDAQ:GOOGL', # Alphabet A类
            'GOOG': 'NASDAQ:GOOG', # Alphabet C类
            'NFLX': 'NASDAQ:NFLX', # Netflix
            'DIS': 'NYSE:DIS',   # 迪士尼 (重复检查)
            'VZ': 'NYSE:VZ',     # 威瑞森通信
            'T': 'NYSE:T',       # AT&T (重复检查)
            'CMCSA': 'NASDAQ:CMCSA', # 康卡斯特 (重复检查)
            'CHTR': 'NASDAQ:CHTR', # Charter Communications
            'TMUS': 'NASDAQ:TMUS', # T-Mobile US
            'EA': 'NASDAQ:EA',   # 艺电
            'TTWO': 'NASDAQ:TTWO', # Take-Two Interactive
            'ATVI': 'NASDAQ:ATVI', # 动视暴雪
            'WBD': 'NASDAQ:WBD', # Warner Bros. Discovery
            'PARA': 'NASDAQ:PARA', # Paramount Global
            'FOX': 'NASDAQ:FOX', # Fox Corporation
            'FOXA': 'NASDAQ:FOXA', # Fox Corporation A类
            'NWSA': 'NASDAQ:NWSA', # News Corporation A类
            'NWS': 'NASDAQ:NWS', # News Corporation B类
            'IPG': 'NYSE:IPG',   # Interpublic Group
            'OMC': 'NYSE:OMC',   # Omnicom Group
            'DISH': 'NASDAQ:DISH', # Dish Network
            'SIRI': 'NASDAQ:SIRI', # Sirius XM Holdings
            'MTCH': 'NASDAQ:MTCH', # Match Group
            'PINS': 'NYSE:PINS', # Pinterest
            'SNAP': 'NYSE:SNAP', # Snap公司
            'TWTR': 'NYSE:TWTR', # Twitter (已私有化)
            'LUMN': 'NYSE:LUMN', # Lumen Technologies
            'ROKU': 'NASDAQ:ROKU', # Roku公司
            'FUBO': 'NYSE:FUBO', # fuboTV
            'PTON': 'NASDAQ:PTON', # Peloton Interactive
            'ZM': 'NASDAQ:ZM',   # Zoom Video Communications
            'DOCU': 'NASDAQ:DOCU', # DocuSign
            'DBX': 'NASDAQ:DBX', # Dropbox
            'BOX': 'NYSE:BOX',   # Box公司
            'WORK': 'NYSE:WORK', # Slack Technologies (已被Salesforce收购)
            'TWLO': 'NYSE:TWLO', # Twilio
            'ZEN': 'NYSE:ZEN',   # Zendesk (已私有化)
            'CRM': 'NYSE:CRM',   # Salesforce (重复检查)
            
            # === NASDAQ 交易所股票 (纳指100 + 其他科技股) ===
            
            # 科技巨头
            'AAPL': 'NASDAQ:AAPL', # 苹果公司
            'MSFT': 'NASDAQ:MSFT', # 微软公司
            'NVDA': 'NASDAQ:NVDA', # 英伟达
            'AMZN': 'NASDAQ:AMZN', # 亚马逊 (重复检查)
            'TSLA': 'NASDAQ:TSLA', # 特斯拉 (重复检查)
            'META': 'NASDAQ:META', # Meta Platforms (重复检查)
            
            # 半导体
            'NVDA': 'NASDAQ:NVDA', # 英伟达 (重复检查)
            'AMD': 'NASDAQ:AMD',   # 超威半导体
            'INTC': 'NASDAQ:INTC', # 英特尔
            'AVGO': 'NASDAQ:AVGO', # 博通
            'TXN': 'NASDAQ:TXN',   # 德州仪器
            'QCOM': 'NASDAQ:QCOM', # 高通
            'ADI': 'NASDAQ:ADI',   # 亚德诺半导体
            'AMAT': 'NASDAQ:AMAT', # 应用材料
            'LRCX': 'NASDAQ:LRCX', # 拉姆研究
            'KLAC': 'NASDAQ:KLAC', # 科磊半导体
            'ASML': 'NASDAQ:ASML', # ASML控股
            'SNPS': 'NASDAQ:SNPS', # 新思科技
            'CDNS': 'NASDAQ:CDNS', # 铿腾电子
            'MRVL': 'NASDAQ:MRVL', # 迈威尔科技
            'MCHP': 'NASDAQ:MCHP', # 微芯科技
            'NXPI': 'NASDAQ:NXPI', # 恩智浦半导体
            'SWKS': 'NASDAQ:SWKS', # Skyworks Solutions
            'QRVO': 'NASDAQ:QRVO', # Qorvo公司
            'MPWR': 'NASDAQ:MPWR', # Monolithic Power Systems
            'ENPH': 'NASDAQ:ENPH', # Enphase Energy
            'ON': 'NASDAQ:ON',     # 安森美半导体
            'STM': 'NYSE:STM',     # 意法半导体
            'TSM': 'NYSE:TSM',     # 台积电
            'UMC': 'NYSE:UMC',     # 联华电子
            'ASX': 'NYSE:ASX',     # ASE集团
            'MKSI': 'NASDAQ:MKSI', # MKS Instruments
            'ENTG': 'NASDAQ:ENTG', # Entegris
            'UCTT': 'NASDAQ:UCTT', # Ultra Clean Holdings
            'COHU': 'NASDAQ:COHU', # Cohu公司
            'FORM': 'NASDAQ:FORM', # FormFactor
            'ACLS': 'NASDAQ:ACLS', # Axcelis Technologies
            'PLAB': 'NASDAQ:PLAB', # Photronics
            'ONTO': 'NYSE:ONTO',   # Onto Innovation
            'ICHR': 'NASDAQ:ICHR', # Ichor Holdings
            'CRUS': 'NASDAQ:CRUS', # Cirrus Logic
            'SIMO': 'NASDAQ:SIMO', # Silicon Motion Technology
            'DIOD': 'NASDAQ:DIOD', # Diodes Incorporated
            'RMBS': 'NASDAQ:RMBS', # Rambus
            'SITM': 'NASDAQ:SITM', # SiTime Corporation
            'MLGO': 'NASDAQ:MLGO', # MicroAlgo
            'SMCI': 'NASDAQ:SMCI', # Super Micro Computer
            'ARM': 'NASDAQ:ARM',   # Arm Holdings
            
            # 软件与服务
            'CRM': 'NYSE:CRM',     # Salesforce (重复检查)
            'ORCL': 'NYSE:ORCL',   # 甲骨文公司
            'ADBE': 'NASDAQ:ADBE', # Adobe
            'NOW': 'NYSE:NOW',     # ServiceNow (重复检查)
            'INTU': 'NASDAQ:INTU', # Intuit
            'PLTR': 'NYSE:PLTR',   # Palantir Technologies
            'SNOW': 'NYSE:SNOW',   # Snowflake
            'CRWD': 'NASDAQ:CRWD', # CrowdStrike Holdings
            'FTNT': 'NASDAQ:FTNT', # Fortinet
            'PANW': 'NASDAQ:PANW', # Palo Alto Networks
            'WDAY': 'NASDAQ:WDAY', # Workday
            'TEAM': 'NASDAQ:TEAM', # Atlassian
            'ZS': 'NASDAQ:ZS',     # Zscaler
            'OKTA': 'NASDAQ:OKTA', # Okta
            'SPLK': 'NASDAQ:SPLK', # Splunk
            'VEEV': 'NYSE:VEEV',   # Veeva Systems
            'DDOG': 'NASDAQ:DDOG', # Datadog
            'MDB': 'NASDAQ:MDB',   # MongoDB
            'ZM': 'NASDAQ:ZM',     # Zoom Video Communications (重复检查)
            'DOCU': 'NASDAQ:DOCU', # DocuSign (重复检查)
            'TWLO': 'NYSE:TWLO',   # Twilio (重复检查)
            'NET': 'NYSE:NET',     # Cloudflare
            'FSLY': 'NYSE:FSLY',   # Fastly
            'ESTC': 'NYSE:ESTC',   # Elastic
            'PATH': 'NYSE:PATH',   # UiPath
            'APPN': 'NASDAQ:APPN', # Appian
            'PD': 'NYSE:PD',       # PagerDuty
            'S': 'NYSE:S',         # SentinelOne
            'CYBR': 'NASDAQ:CYBR', # CyberArk Software
            'TENB': 'NASDAQ:TENB', # Tenable Holdings
            'QLYS': 'NASDAQ:QLYS', # Qualys
            'RPD': 'NYSE:RPD',     # Rapid7
            'PING': 'NYSE:PING',   # Ping Identity Holdings
            'SAIL': 'NYSE:SAIL',   # SailPoint Technologies Holdings
            'MIME': 'NASDAQ:MIME', # Mimecast
            'PFPT': 'NASDAQ:PFPT', # Proofpoint
            'VRNS': 'NYSE:VRNS',   # Varonis Systems
            'EVBG': 'NASDAQ:EVBG', # Everbridge
            'GTLB': 'NASDAQ:GTLB', # GitLab
            'CFLT': 'NYSE:CFLT',   # Confluent
            'AI': 'NYSE:AI',       # C3.ai
            'BILL': 'NYSE:BILL',   # Bill.com Holdings
            'COUP': 'NASDAQ:COUP', # Coupa Software
            'PCTY': 'NASDAQ:PCTY', # Paylocity Holding
            'PAYC': 'NYSE:PAYC',   # Paycom Software
            'HUBS': 'NYSE:HUBS',   # HubSpot
            'ZUO': 'NYSE:ZUO',     # Zuora
            'SAGE': 'NASDAQ:SAGE', # Sage Therapeutics
            'WIX': 'NASDAQ:WIX',   # Wix.com
            'SHOP': 'NYSE:SHOP',   # Shopify
            'SQ': 'NYSE:SQ',       # Block (formerly Square)
            'PYPL': 'NASDAQ:PYPL', # PayPal Holdings
            'ADSK': 'NASDAQ:ADSK', # Autodesk
            'ANSS': 'NASDAQ:ANSS', # ANSYS
            'CTSH': 'NASDAQ:CTSH', # Cognizant Technology Solutions
            'EPAM': 'NYSE:EPAM',   # EPAM Systems
            'GLW': 'NYSE:GLW',     # 康宁公司
            'HPQ': 'NYSE:HPQ',     # 惠普公司
            'NTAP': 'NASDAQ:NTAP', # NetApp
            'STX': 'NASDAQ:STX',   # 希捷科技
            'WDC': 'NASDAQ:WDC',   # 西部数据
            'SMCI': 'NASDAQ:SMCI', # Super Micro Computer (重复检查)
            'DELL': 'NYSE:DELL',   # 戴尔科技
            'HPE': 'NYSE:HPE',     # 慧与科技
            'CSCO': 'NASDAQ:CSCO', # 思科系统
            'JNPR': 'NYSE:JNPR',   # 瞻博网络
            'ANET': 'NYSE:ANET',   # Arista Networks
            'FFIV': 'NASDAQ:FFIV', # F5 Networks
            'CIEN': 'NYSE:CIEN',   # Ciena
            'VIAV': 'NASDAQ:VIAV', # Viavi Solutions
            'LITE': 'NASDAQ:LITE', # Lumentum Holdings
            'AAOI': 'NASDAQ:AAOI', # Applied Optoelectronics
            'CALX': 'NASDAQ:CALX', # Calix
            'COMM': 'NASDAQ:COMM', # CommScope Holding
            'INFN': 'NASDAQ:INFN', # Infinera
            'IRDM': 'NASDAQ:IRDM', # Iridium Communications
            'SATS': 'NASDAQ:SATS', # EchoStar
            'GSAT': 'NASDAQ:GSAT', # Globalstar
            'VSAT': 'NASDAQ:VSAT', # Viasat
            'GILT': 'NASDAQ:GILT', # Gilat Satellite Networks
            
            # 生物技术
            'AMGN': 'NASDAQ:AMGN', # 安进公司 (重复检查)
            'GILD': 'NASDAQ:GILD', # 吉利德科学 (重复检查)
            'REGN': 'NASDAQ:REGN', # Regeneron Pharmaceuticals
            'VRTX': 'NASDAQ:VRTX', # Vertex Pharmaceuticals
            'BIIB': 'NASDAQ:BIIB', # 百健公司
            'ILMN': 'NASDAQ:ILMN', # Illumina
            'MRNA': 'NASDAQ:MRNA', # Moderna
            'BNTX': 'NASDAQ:BNTX', # BioNTech
            'SGEN': 'NASDAQ:SGEN', # Seagen
            'ALNY': 'NASDAQ:ALNY', # Alnylam Pharmaceuticals
            'INCY': 'NASDAQ:INCY', # Incyte
            'BMRN': 'NASDAQ:BMRN', # BioMarin Pharmaceutical
            'EXAS': 'NASDAQ:EXAS', # Exact Sciences
            'TECH': 'NASDAQ:TECH', # Bio-Techne
            'SRPT': 'NASDAQ:SRPT', # Sarepta Therapeutics
            'RARE': 'NASDAQ:RARE', # Ultragenyx Pharmaceutical
            'BLUE': 'NASDAQ:BLUE', # bluebird bio
            'FOLD': 'NASDAQ:FOLD', # Amicus Therapeutics
            'IONS': 'NASDAQ:IONS', # Ionis Pharmaceuticals
            'ARWR': 'NASDAQ:ARWR', # Arrowhead Pharmaceuticals
            'MYGN': 'NASDAQ:MYGN', # Myriad Genetics
            'VCYT': 'NASDAQ:VCYT', # Veracyte
            'NVTA': 'NASDAQ:NVTA', # Invitae
            'QGEN': 'NYSE:QGEN',   # QIAGEN
            'CDNA': 'NASDAQ:CDNA', # CareDx
            'TWST': 'NASDAQ:TWST', # Twist Bioscience
            'PACB': 'NASDAQ:PACB', # Pacific Biosciences of California
            'ONT': 'NYSE:ONT',     # Oxford Nanopore Technologies
            'FGEN': 'NASDAQ:FGEN', # FibroGen
            'JAZZ': 'NASDAQ:JAZZ', # Jazz Pharmaceuticals
            'HALO': 'NASDAQ:HALO', # Halozyme Therapeutics
            'PTCT': 'NASDAQ:PTCT', # PTC Therapeutics
            'UTHR': 'NASDAQ:UTHR', # United Therapeutics
            'ACAD': 'NASDAQ:ACAD', # ACADIA Pharmaceuticals
            'NBIX': 'NASDAQ:NBIX', # Neurocrine Biosciences
            'SAGE': 'NASDAQ:SAGE', # Sage Therapeutics (重复检查)
            'SAVA': 'NASDAQ:SAVA', # Cassava Sciences
            'AXSM': 'NASDAQ:AXSM', # Axsome Therapeutics
            'TGTX': 'NASDAQ:TGTX', # TG Therapeutics
            'CORT': 'NASDAQ:CORT', # Corcept Therapeutics
            'HZNP': 'NASDAQ:HZNP', # Horizon Therapeutics (已被Amgen收购)
            'MEDP': 'NASDAQ:MEDP', # Medpace Holdings
            'IQVIA': 'NYSE:IQV',   # IQVIA Holdings (重复检查)
            'CRL': 'NYSE:CRL',     # Charles River Laboratories International
            'LH': 'NYSE:LH',       # Laboratory Corporation of America Holdings (重复检查)
            'DGX': 'NYSE:DGX',     # Quest Diagnostics (重复检查)
            'TMO': 'NYSE:TMO',     # Thermo Fisher Scientific (重复检查)
            'DHR': 'NYSE:DHR',     # Danaher Corporation (重复检查)
            'A': 'NYSE:A',         # Agilent Technologies (重复检查)
            'WAT': 'NYSE:WAT',     # Waters Corporation (重复检查)
            'PKI': 'NYSE:PKI',     # PerkinElmer
            'MTD': 'NYSE:MTD',     # Mettler-Toledo International (重复检查)
            'LIFE': 'NASDAQ:LIFE', # aTyr Pharma
            'FLGT': 'NASDAQ:FLGT', # Fulgent Genetics
            'NTRA': 'NASDAQ:NTRA', # Natera
            'GRFS': 'NASDAQ:GRFS', # Grifols S.A.
            'ARCT': 'NASDAQ:ARCT', # Arcturus Therapeutics Holdings
            'BPMC': 'NASDAQ:BPMC', # Blueprint Medicines
            'FATE': 'NASDAQ:FATE', # Fate Therapeutics
            'CRSP': 'NASDAQ:CRSP', # CRISPR Therapeutics
            'EDIT': 'NASDAQ:EDIT', # Editas Medicine
            'NTLA': 'NASDAQ:NTLA', # Intellia Therapeutics
            'BEAM': 'NASDAQ:BEAM', # Beam Therapeutics
            'PRIME': 'NASDAQ:PRME', # Prime Medicine
            
            # 消费服务与零售
            'COST': 'NASDAQ:COST', # 好市多 (重复检查)
            'SBUX': 'NASDAQ:SBUX', # 星巴克 (重复检查)
            'MCD': 'NYSE:MCD',     # 麦当劳 (重复检查)
            'BKNG': 'NASDAQ:BKNG', # Booking Holdings (重复检查)
            'ABNB': 'NASDAQ:ABNB', # Airbnb (重复检查)
            'EBAY': 'NASDAQ:EBAY', # eBay (重复检查)
            'ETSY': 'NASDAQ:ETSY', # Etsy (重复检查)
            'EXPE': 'NASDAQ:EXPE', # Expedia Group (重复检查)
            'LULU': 'NASDAQ:LULU', # Lululemon Athletica (重复检查)
            'ROST': 'NASDAQ:ROST', # Ross Stores (重复检查)
            'DLTR': 'NASDAQ:DLTR', # Dollar Tree (重复检查)
            'ORLY': 'NASDAQ:ORLY', # O'Reilly Automotive (重复检查)
            'WYNN': 'NASDAQ:WYNN', # Wynn Resorts (重复检查)
            'MAR': 'NASDAQ:MAR',   # Marriott International (重复检查)
            'HAS': 'NASDAQ:HAS',   # Hasbro (重复检查)
            'MAT': 'NASDAQ:MAT',   # Mattel (重复检查)
            'POOL': 'NASDAQ:POOL', # Pool Corporation (重复检查)
            'LKQ': 'NASDAQ:LKQ',   # LKQ Corporation (重复检查)
            'ULTA': 'NASDAQ:ULTA', # Ulta Beauty
            'NDSN': 'NASDAQ:NDSN', # Nordson Corporation
            'FAST': 'NASDAQ:FAST', # Fastenal Company (重复检查)
            'PAYX': 'NASDAQ:PAYX', # Paychex (重复检查)
            'ODFL': 'NASDAQ:ODFL', # Old Dominion Freight Line (重复检查)
            'PCAR': 'NASDAQ:PCAR', # PACCAR (重复检查)
            'CHRW': 'NASDAQ:CHRW', # C.H. Robinson Worldwide
            'EXPD': 'NASDAQ:EXPD', # Expeditors International of Washington
            'JBHT': 'NASDAQ:JBHT', # J.B. Hunt Transport Services
            'KNX': 'NYSE:KNX',     # Knight-Swift Transportation Holdings
            'LSTR': 'NASDAQ:LSTR', # Landstar System
            'SAIA': 'NASDAQ:SAIA', # Saia
            'ARCB': 'NASDAQ:ARCB', # ArcBest
            'YELL': 'NASDAQ:YELL', # Yellow Corporation
            'CVCO': 'NASDAQ:CVCO', # Cavco Industries
            'SKX': 'NYSE:SKX',     # Skechers U.S.A.
            'CROX': 'NASDAQ:CROX', # Crocs
            'DECK': 'NYSE:DECK',   # Deckers Outdoor Corporation
            'COLM': 'NASDAQ:COLM', # Columbia Sportswear Company
            'VFC': 'NYSE:VFC',     # VF Corporation
            'TPG': 'NASDAQ:TPG',   # TPG Inc. (重复检查)
            'CPNG': 'NYSE:CPNG',   # Coupang
            'SE': 'NYSE:SE',       # Sea Limited
            'MELI': 'NASDAQ:MELI', # MercadoLibre
            'JD': 'NASDAQ:JD',     # JD.com (重复检查)
            'PDD': 'NASDAQ:PDD',   # PDD Holdings (重复检查)
            'BABA': 'NYSE:BABA',   # Alibaba Group Holding (重复检查)
            'TME': 'NYSE:TME',     # Tencent Music Entertainment Group (重复检查)
            'BILI': 'NASDAQ:BILI', # Bilibili (重复检查)
            'IQ': 'NASDAQ:IQ',     # iQIYI (重复检查)
            'NTES': 'NASDAQ:NTES', # NetEase (重复检查)
            'BIDU': 'NASDAQ:BIDU', # Baidu (重复检查)
            'NIO': 'NYSE:NIO',     # NIO (重复检查)
            'XPEV': 'NYSE:XPEV',   # XPeng (重复检查)
            'LI': 'NASDAQ:LI',     # Li Auto (重复检查)
            'DIDI': 'NYSE:DIDI',   # DiDi Global (重复检查)
            'GRAB': 'NASDAQ:GRAB', # Grab Holdings
            'UBER': 'NYSE:UBER',   # Uber Technologies (重复检查)
            'LYFT': 'NASDAQ:LYFT', # Lyft (重复检查)
            'DASH': 'NYSE:DASH',   # DoorDash
            'GDDY': 'NYSE:GDDY',   # GoDaddy
            'FTCH': 'NYSE:FTCH',   # Farfetch
            'RH': 'NYSE:RH',       # RH
            'W': 'NYSE:W',         # Wayfair
            'CHWY': 'NYSE:CHWY',   # Chewy
            'PETS': 'NASDAQ:PETS', # PetMed Express
            'WOOF': 'NASDAQ:WOOF', # Petco Health and Wellness Company
            'ZG': 'NASDAQ:ZG',     # Zillow Group A类
            'Z': 'NASDAQ:Z',       # Zillow Group C类
            'OPEN': 'NASDAQ:OPEN', # Opendoor Technologies
            'RDFN': 'NASDAQ:RDFN', # Redfin
            'COMP': 'NASDAQ:COMP', # Compass
            'OPAD': 'NASDAQ:OPAD', # Offerpad Solutions
            'BIGC': 'NASDAQ:BIGC', # BigCommerce Holdings
            'BIGC': 'NASDAQ:BIGC', # BigCommerce Holdings (重复检查)
            'OSTK': 'NASDAQ:OSTK', # Overstock.com
            'VIPS': 'NYSE:VIPS',   # Vipshop Holdings
            'VTEX': 'NYSE:VTEX',   # VTEX
            'STNE': 'NASDAQ:STNE', # StoneCo
            'PAGS': 'NYSE:PAGS',   # PagSeguro Digital
            'MOMO': 'NASDAQ:MOMO', # Hello Group
            'YY': 'NASDAQ:YY',     # JOYY
            'HUYA': 'NYSE:HUYA',   # HUYA
            'DOYU': 'NYSE:DOYU',   # DouYu International Holdings
            'WB': 'NASDAQ:WB',     # Weibo Corporation
            'SINA': 'NASDAQ:SINA', # SINA Corporation
            'SOHU': 'NASDAQ:SOHU', # Sohu.com
            'FENG': 'NASDAQ:FENG', # Phoenix New Media
            'TOUR': 'NASDAQ:TOUR', # Tuniu Corporation
            'TIGR': 'NASDAQ:TIGR', # UP Fintech Holding
            'FUTU': 'NASDAQ:FUTU', # Futu Holdings
            'NOAH': 'NYSE:NOAH',   # Noah Holdings
            'TANH': 'NYSE:TANH',   # Tantech Holdings
            'CAAS': 'NASDAQ:CAAS', # China Automotive Systems
            'CBAT': 'NASDAQ:CBAT', # CBAK Energy Technology
            'CCXT': 'NASDAQ:CCXT', # Chinacast Education Corporation
            'CNET': 'NASDAQ:CNET', # ZW Data Action Technologies
            'DQ': 'NYSE:DQ',       # Daqo New Energy
            'GSX': 'NYSE:GSX',     # Gensyn (formerly GSX Techedu)
            'LX': 'NYSE:LX',       # LexinFintech Holdings
            'QD': 'NASDAQ:QD',     # Qudian
            'RERE': 'NASDAQ:RERE', # ATRenew
            'TAL': 'NYSE:TAL',     # TAL Education Group
            'WDH': 'NASDAQ:WDH',   # Waterdrop
            'YMM': 'NASDAQ:YMM',   # Full Truck Alliance
            'ZYME': 'NASDAQ:ZYME', # Zymeworks
            
            # 其他重要股票
            'BRK.A': 'NYSE:BRK.A', # 伯克希尔·哈撒韦A类
            'BRK.B': 'NYSE:BRK.B', # 伯克希尔·哈撒韦B类
            'GOOGL': 'NASDAQ:GOOGL', # Alphabet A类 (重复检查)
            'GOOG': 'NASDAQ:GOOG', # Alphabet C类 (重复检查)
            'META': 'NASDAQ:META', # Meta Platforms (重复检查)
            'AMZN': 'NASDAQ:AMZN', # Amazon.com (重复检查)
            'TSLA': 'NASDAQ:TSLA', # Tesla (重复检查)
            'NVDA': 'NASDAQ:NVDA', # NVIDIA Corporation (重复检查)
            'MSFT': 'NASDAQ:MSFT', # Microsoft Corporation (重复检查)
            'AAPL': 'NASDAQ:AAPL', # Apple Inc. (重复检查)
        }
        
    async def detect_stock_exchange(self, symbol: str) -> str:
        """
        智能检测未知股票符号的交易所
        使用多种策略自动匹配最可能的交易所
        """
        symbol = symbol.upper()
        
        # 如果已经包含交易所前缀，直接返回
        if ':' in symbol:
            return symbol
            
        # 尝试通过Chart-img API测试不同交易所
        test_exchanges = ['NASDAQ', 'NYSE', 'AMEX', 'OTC']
        
        for exchange in test_exchanges:
            test_symbol = f"{exchange}:{symbol}"
            try:
                # 构建测试API URL
                test_url = f"https://api.chart-img.com/v1/tradingview/advanced-chart"
                test_params = {
                    'symbol': test_symbol,
                    'interval': '1h',
                    'width': 400,
                    'height': 300,
                    'key': self.config.chart_img_api_key
                }
                
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(test_url, params=test_params) as response:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            if 'image' in content_type:
                                self.logger.info(f"检测到 {symbol} 属于 {exchange} 交易所")
                                return test_symbol
                                
            except Exception as e:
                self.logger.debug(f"测试 {test_symbol} 失败: {e}")
                continue
        
        # 如果API测试失败，使用启发式规则
        nasdaq_patterns = [
            # 科技公司常见后缀
            r'.*X$',      # 如 DKNG -> NASDAQ
            r'.*G$',      # 如 GOOGL -> NASDAQ  
            r'.*T$',      # 如 MSFT -> NASDAQ
            # 生物技术/制药
            r'.*BIO$', r'.*GENE$', r'.*THER$', r'.*PHARM$',
            # 新兴公司/IPO
            r'^[A-Z]{3,4}$'  # 3-4字母的简单符号通常在NASDAQ
        ]
        
        nyse_patterns = [
            # 传统行业
            r'.*CORP$', r'.*INC$', r'.*LLC$',
            # 金融服务
            r'.*BANK$', r'.*FINANCIAL$', r'.*TRUST$',
            # 能源/材料
            r'.*OIL$', r'.*GAS$', r'.*ENERGY$', r'.*MATERIALS$',
            # 单字母股票通常在NYSE
            r'^[A-Z]$'
        ]
        
        # 检查NASDAQ模式
        for pattern in nasdaq_patterns:
            if re.match(pattern, symbol):
                self.logger.info(f"基于模式匹配，推测 {symbol} 属于 NASDAQ 交易所")
                return f"NASDAQ:{symbol}"
        
        # 检查NYSE模式  
        for pattern in nyse_patterns:
            if re.match(pattern, symbol):
                self.logger.info(f"基于模式匹配，推测 {symbol} 属于 NYSE 交易所")
                return f"NYSE:{symbol}"
        
        # 默认尝试NASDAQ（新股票更可能在NASDAQ）
        self.logger.info(f"无法确定 {symbol} 交易所，默认尝试 NASDAQ")
        return f"NASDAQ:{symbol}"
        
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
                    # 使用智能检测功能自动匹配交易所
                    symbol = await self.detect_stock_exchange(symbol)
                    self.logger.info(f'智能检测交易所: {symbol}')
            
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