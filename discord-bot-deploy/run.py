#!/usr/bin/env python3
"""
Alternative entry point for deployment
Ensures proper startup with minimal logging
"""

import asyncio
import os
import sys
from main import main

if __name__ == "__main__":
    # Ensure proper environment for deployment
    if not os.getenv('DISCORD_TOKEN'):
        print("❌ Error: DISCORD_TOKEN environment variable not set")
        sys.exit(1)
    
    if not os.getenv('WEBHOOK_URL'):
        print("❌ Error: WEBHOOK_URL environment variable not set")
        sys.exit(1)
    
    print("✅ Starting Discord Bot with API Server...")
    print("🔧 Environment configured properly")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)