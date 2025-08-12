#!/usr/bin/env python3
"""
Discord Bot Entry Point
运行Discord机器人的主入口文件
"""

import asyncio
import logging
import sys
from bot import DiscordBot
from config import Config
from api_server import DiscordAPIServer

def setup_logging():
    """设置日志配置"""
    # 设置日志级别为INFO减少部署时的噪音
    log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('discord_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 减少discord.py的调试输出
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)

async def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 加载配置
        config = Config()
        
        # 验证必要的配置
        if not config.discord_token:
            logger.error("Discord token未配置，请检查环境变量DISCORD_TOKEN")
            return
            
        if not config.webhook_url:
            logger.error("Webhook URL未配置，请检查环境变量WEBHOOK_URL")
            return
        
        # 创建机器人
        bot = DiscordBot(config)
        
        # 启动机器人和API服务器
        logger.info("🚀 启动Discord机器人和API服务器...")
        logger.info("🌐 API服务器将在 http://0.0.0.0:5000 启动")
        logger.info("🤖 Discord机器人正在连接...")
        
        await bot.start_with_api(config.discord_token, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"启动服务时发生错误: {e}")
        raise
    finally:
        logger.info("服务已关闭")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n机器人已停止")
    except Exception as e:
        print(f"运行时发生错误: {e}")
        sys.exit(1)
