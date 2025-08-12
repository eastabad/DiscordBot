#!/usr/bin/env python3
"""
简化版Discord机器人
专注于核心功能：图表获取、股票分析、图片分析、用户限制、历史清理
去掉API服务器，纯Discord机器人模式
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # 减少discord.py的调试输出
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

async def main():
    """主函数 - 纯Discord机器人模式"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 启动简化版TDbot-tradingview...")
        
        # 验证必需的环境变量
        required_vars = ['DISCORD_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
            sys.exit(1)
        
        logger.info("✅ 环境变量验证通过")
        
        # 导入并创建机器人
        from bot import DiscordBot
        from config import Config
        
        # 加载配置
        config = Config()
        logger.info("✅ 配置加载完成")
        
        # 创建机器人实例
        bot = DiscordBot(config)
        logger.info("✅ Discord机器人初始化完成")
        
        logger.info("🤖 连接Discord机器人...")
        
        # 确保discord_token存在
        if not config.discord_token:
            logger.error("❌ Discord token 为空")
            sys.exit(1)
        
        # 直接启动Discord机器人，不启动API服务器
        await bot.start(config.discord_token)
        
    except KeyboardInterrupt:
        logger.info("⏹️ 收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"❌ 启动错误: {e}")
        raise
    finally:
        logger.info("🔚 机器人已关闭")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 机器人已停止")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        sys.exit(1)