"""
配置管理模块
处理环境变量和配置文件
"""

import os
from typing import Optional
import logging

class Config:
    """配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.logger = logging.getLogger(__name__)
        self._load_config()
        
    def _load_config(self):
        """加载配置"""
        try:
            # 尝试加载.env文件
            self._load_env_file()
        except Exception as e:
            self.logger.warning(f'加载.env文件失败: {e}')
            
        # 从环境变量加载配置
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        
        # Chart-img API配置
        self.chart_img_api_key = os.getenv('CHART_IMG_API_KEY')
        self.layout_id = os.getenv('LAYOUT_ID')
        self.tradingview_session_id = os.getenv('TRADINGVIEW_SESSION_ID')
        self.tradingview_session_id_sign = os.getenv('TRADINGVIEW_SESSION_ID_SIGN')
        
        # 支持多个监控频道
        monitor_channels_str = os.getenv('MONITOR_CHANNEL_IDS')
        if monitor_channels_str:
            # 支持逗号分隔的多个频道ID
            self.monitor_channel_ids = [id.strip() for id in monitor_channels_str.split(',') if id.strip()]
        else:
            # 向后兼容单个频道配置
            single_channel = os.getenv('MONITOR_CHANNEL_ID')
            self.monitor_channel_ids = [single_channel] if single_channel else []
        
        # 可选配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.webhook_timeout = int(os.getenv('WEBHOOK_TIMEOUT', '30'))
        self.command_prefix = os.getenv('COMMAND_PREFIX', '!')
        
        # 验证必需配置
        self._validate_config()
        
    def _load_env_file(self):
        """加载.env文件"""
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            self.logger.info('成功加载.env文件')
        
    def _validate_config(self):
        """验证配置"""
        errors = []
        
        if not self.discord_token:
            errors.append('DISCORD_TOKEN未设置')
            
        if not self.webhook_url:
            errors.append('WEBHOOK_URL未设置')
        elif not self.webhook_url.startswith(('http://', 'https://')):
            errors.append('WEBHOOK_URL必须是有效的HTTP(S) URL')
            
        if not self.monitor_channel_ids:
            errors.append('MONITOR_CHANNEL_IDS或MONITOR_CHANNEL_ID未设置')
            
        if self.max_retries < 1:
            errors.append('MAX_RETRIES必须大于0')
            
        if self.webhook_timeout < 1:
            errors.append('WEBHOOK_TIMEOUT必须大于0')
            
        if errors:
            error_msg = '配置验证失败:\n' + '\n'.join(f'- {error}' for error in errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        self.logger.info('配置验证通过')
        
    def get_summary(self) -> dict:
        """获取配置摘要（隐藏敏感信息）"""
        return {
            'discord_token': '***已设置***' if self.discord_token else '未设置',
            'webhook_url': self._mask_url(self.webhook_url) if self.webhook_url else '未设置',
            'log_level': self.log_level,
            'max_retries': self.max_retries,
            'webhook_timeout': self.webhook_timeout,
            'command_prefix': self.command_prefix
        }
        
    def _mask_url(self, url: str) -> str:
        """掩码URL中的敏感信息"""
        if not url:
            return url
            
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            masked_netloc = parsed.netloc
            
            # 如果有用户信息，掩码它
            if '@' in masked_netloc:
                user_info, host = masked_netloc.split('@')
                masked_netloc = '***@' + host
                
            return f"{parsed.scheme}://{masked_netloc}{parsed.path}..."
        except:
            return url[:20] + "..." if len(url) > 20 else url
