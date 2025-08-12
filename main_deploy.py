#!/usr/bin/env python3
"""
部署专用主入口点
专为Replit云部署优化的Discord机器人启动器
确保健康检查通过和正确的服务启动
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

def setup_production_logging():
    """设置生产环境日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # 减少第三方库的日志输出
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

def validate_environment():
    """验证部署环境和必需的环境变量"""
    logger = logging.getLogger(__name__)
    
    # 必需的环境变量
    required_vars = ['DISCORD_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            logger.info(f"✅ {var} 已配置")
    
    if missing_vars:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.error("请在Replit Secrets中设置这些环境变量")
        sys.exit(1)
    
    logger.info("✅ 所有必需的环境变量验证通过")

async def main():
    """主函数 - 部署优化版本"""
    setup_production_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 启动Discord机器人 (部署模式)...")
        logger.info(f"🕐 启动时间: {datetime.now().isoformat()}")
        
        # 验证环境
        validate_environment()
        
        # 导入核心组件
        from bot import DiscordBot
        from config import Config
        
        # 加载配置
        config = Config()
        logger.info("✅ 配置加载完成")
        
        # 创建机器人实例
        bot = DiscordBot(config)
        logger.info("✅ Discord机器人初始化完成")
        
        # 确认token存在
        if not config.discord_token:
            logger.error("❌ Discord token 配置错误")
            sys.exit(1)
        
        logger.info("🤖 正在连接Discord...")
        
        # 启动Discord机器人
        await bot.start(config.discord_token)
        
    except KeyboardInterrupt:
        logger.info("⏹️ 收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"❌ 启动错误: {e}")
        logger.exception("详细错误信息:")
        sys.exit(1)
    finally:
        logger.info("🔚 机器人已关闭")

if __name__ == "__main__":
    try:
        # 使用默认事件循环策略
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️ 机器人已停止")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        sys.exit(1)