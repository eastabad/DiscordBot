#!/usr/bin/env python3
"""
Replit部署主入口点
简化版本 - 专为解决部署健康检查问题
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 设置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    try:
        logger.info("启动Discord机器人...")
        
        # 检查必需的环境变量
        if not os.getenv('DISCORD_TOKEN'):
            logger.error("缺少DISCORD_TOKEN环境变量")
            sys.exit(1)
        
        # 导入并启动机器人
        from simple_bot import main as bot_main
        await bot_main()
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())