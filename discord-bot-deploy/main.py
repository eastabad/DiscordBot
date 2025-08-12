#!/usr/bin/env python3
"""
Discord Bot Deployment Entry Point
专为Replit部署优化的主入口文件，包含健康检查功能
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from aiohttp import web

def setup_deployment_logging():
    """设置部署环境日志配置"""
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

# 全局变量追踪服务状态
bot_status = {"running": False, "started_at": None}

async def health_check(request):
    """健康检查端点"""
    status = {
        "status": "healthy" if bot_status["running"] else "starting",
        "timestamp": datetime.now().isoformat(),
        "bot_running": bot_status["running"],
        "started_at": bot_status["started_at"]
    }
    return web.json_response(status)

async def root_endpoint(request):
    """根端点 - 部署健康检查"""
    if bot_status["running"]:
        return web.json_response({
            "message": "Discord Bot is running",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    else:
        return web.json_response({
            "message": "Discord Bot is starting",
            "status": "starting", 
            "timestamp": datetime.now().isoformat()
        }, status=503)

async def create_health_server():
    """创建健康检查HTTP服务器"""
    app = web.Application()
    app.router.add_get('/', root_endpoint)
    app.router.add_get('/health', health_check)
    
    # 使用端口5000，这是唯一不被防火墙阻挡的端口
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    
    logger = logging.getLogger(__name__)
    logger.info("✅ 健康检查服务器启动在端口5000")
    
    return runner

async def start_discord_bot():
    """启动Discord机器人"""
    logger = logging.getLogger(__name__)
    
    try:
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
        
        # 更新状态
        bot_status["running"] = True
        bot_status["started_at"] = datetime.now().isoformat()
        
        # 启动Discord机器人
        await bot.start(config.discord_token)
        
    except Exception as e:
        logger.error(f"❌ Discord机器人启动错误: {e}")
        logger.exception("详细错误信息:")
        bot_status["running"] = False
        raise

async def main():
    """主函数 - 同时运行Discord机器人和健康检查服务器"""
    setup_deployment_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 启动Discord机器人服务 (部署模式)...")
        logger.info(f"🕐 启动时间: {datetime.now().isoformat()}")
        
        # 验证环境
        validate_environment()
        
        # 创建健康检查服务器
        health_runner = await create_health_server()
        
        logger.info("🤖 启动Discord机器人...")
        
        # 启动Discord机器人 (这会阻塞)
        await start_discord_bot()
        
    except KeyboardInterrupt:
        logger.info("⏹️ 收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"❌ 启动错误: {e}")
        logger.exception("详细错误信息:")
        sys.exit(1)
    finally:
        logger.info("🔚 服务已关闭")
        bot_status["running"] = False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 服务已停止")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        sys.exit(1)
