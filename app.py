#!/usr/bin/env python3
"""
Optimized deployment entry point for Replit deployments
Ensures immediate health check response and proper bot startup
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

def setup_deployment_logging():
    """Setup minimal logging for deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Reduce discord.py noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

async def main():
    """Main deployment entry point"""
    setup_deployment_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Starting TDbot-tradingview deployment...")
        
        # Validate critical environment variables
        required_vars = ['DISCORD_TOKEN', 'WEBHOOK_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
        
        logger.info("✅ Environment variables validated")
        
        # Import and run the main application
        from bot import DiscordBot
        from config import Config
        
        # Load configuration
        config = Config()
        logger.info("✅ Configuration loaded")
        
        # Create and start bot with API server
        bot = DiscordBot(config)
        logger.info("✅ Discord bot initialized")
        
        logger.info("🌐 Starting API server on port 5000...")
        logger.info("🤖 Connecting Discord bot...")
        
        # Start both services concurrently
        await bot.start_with_api(config.discord_token, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        raise
    finally:
        logger.info("🔚 Deployment shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)