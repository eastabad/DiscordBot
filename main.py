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
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('discord_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

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
        
        # 创建API服务器
        api_server = DiscordAPIServer(bot)
        
        # 启动API服务器
        logger.info("正在启动API服务器...")
        runner = await api_server.start_server(host='0.0.0.0', port=5000)
        
        # 启动机器人
        logger.info("正在启动Discord机器人...")
        
        # 并行运行机器人和API服务器
        bot_task = asyncio.create_task(bot.start(config.discord_token))
        
        # 等待机器人任务完成
        await bot_task
        
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
