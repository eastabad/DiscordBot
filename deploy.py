#!/usr/bin/env python3
"""
Production deployment entry point
Optimized for Replit deployments with health checks
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

def setup_production_logging():
    """设置生产环境日志配置"""
    log_level = logging.INFO
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 文件处理器（可选，部署时通常使用外部日志收集）
    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 减少第三方库的日志输出
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

async def main():
    """生产环境主函数"""
    setup_production_logging()
    logger = logging.getLogger('deploy')
    
    print(f"🚀 启动时间: {datetime.now().isoformat()}")
    print("📋 检查部署环境...")
    
    # 验证必要的环境变量
    required_vars = ['DISCORD_TOKEN', 'WEBHOOK_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("✅ 环境变量检查通过")
    print("🤖 启动Discord Bot API服务...")
    
    try:
        # 导入并运行主应用
        from main import main as app_main
        await app_main()
        
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 部署失败: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 应用已停止")
    except Exception as e:
        print(f"❌ 部署错误: {e}")
        sys.exit(1)