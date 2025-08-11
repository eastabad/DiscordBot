# Overview

This is a Discord bot application written in Python that monitors Discord channels for @mentions and forwards channel information to external webhooks. The bot provides automated message forwarding capabilities with comprehensive error handling, retry mechanisms, and detailed logging. It's designed to bridge Discord conversations with external systems through webhook integrations.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Issues & Solutions

**Discord Bot Message Handling Issue** (2025-08-11):
- Problem: Bot connects successfully but doesn't respond to messages or @mentions
- Root Cause: MESSAGE CONTENT INTENT not enabled in Discord Developer Portal + role mention detection logic
- Solution: User enabled MESSAGE CONTENT INTENT + Fixed role mention detection logic + Fixed command handling
- Status: ✅ RESOLVED - Bot now properly receives messages, handles commands, and processes @mentions including role mentions

**n8n Workflow Integration** (2025-08-11):
- Added HTTP API server on port 5000 for n8n workflow integration
- Created `/api/send-chart` endpoint for automated chart image delivery
- Supports direct message sending with chart images to specified Discord users
- API tested and working: Health check ✅, DM sending ✅, Chart delivery ✅
- Status: ✅ READY FOR PRODUCTION - n8n workflows can now send chart images via API

**Stock Chart Bot Final Upgrade** (2025-08-11):
- ✅ UPGRADED to use Layout Chart Storage API for true custom TradingView layouts
- ✅ REMOVED @bot requirement - bot now responds to simple stock commands in monitored channel
- ✅ IMPROVED command parsing for format: SYMBOL,TIMEFRAME (e.g. AAPL,1h or NASDAQ:GOOG,15m)
- ✅ FIXED API endpoint to use v2/tradingview/layout-chart/storage/{layout_id}
- ✅ IMPLEMENTED 5-second delay for perfect technical indicator loading
- ✅ TESTED Layout Chart Storage API successfully - 118KB charts with full indicators
- ✅ CONFIRMED technical indicators render correctly (MACD, RSI, etc.)
- ✅ FIXED timeframe validation to reject invalid formats like '15h' before API calls
- ✅ CLOUD STORAGE response provides stable image URLs with expiration dates
- ✅ DUAL MODE support: Stock charts in monitored channel + webhook forwarding in other channels
- ✅ AUTO-PREFIX for stock symbols (adds NASDAQ: if no exchange specified)
- ✅ LAYOUT CHART functionality using user's custom TradingView layout (1920x1080)
- Configuration: CHART_IMG_API_KEY, LAYOUT_ID, MONITOR_CHANNEL_ID, TradingView session
- Status: ✅ PRODUCTION READY - Perfect technical indicator loading achieved

# System Architecture

## Core Components

**Bot Architecture**: The application follows a modular design with clear separation of concerns:
- `DiscordBot` class extends the discord.py commands.Bot framework
- Event-driven architecture using Discord's gateway events (on_ready, on_message)
- Asynchronous programming model using Python's asyncio for concurrent operations

**Configuration Management**: Centralized configuration system that prioritizes environment variables over file-based configuration:
- Supports both `.env` file loading and direct environment variable access
- Includes validation for required configuration parameters
- Provides sensible defaults for optional settings like retry counts and timeouts

**Message Processing Pipeline**: 
- Bot listens for @mention events in Discord channels
- Filters out bot's own messages to prevent infinite loops
- Extracts message metadata including author, channel, and content information
- Transforms Discord message objects into webhook-compatible payloads

**Error Handling Strategy**: Multi-layered approach to handle various failure scenarios:
- Retry mechanisms with exponential backoff for webhook delivery
- Comprehensive logging at different severity levels
- Graceful degradation when external services are unavailable

## Design Patterns

**Dependency Injection**: Configuration and webhook handler instances are injected into the bot class, promoting testability and flexibility.

**Single Responsibility Principle**: Each module has a focused purpose - configuration management, webhook handling, bot logic, and application entry point are clearly separated.

**Observer Pattern**: Uses Discord's event system where the bot observes message events and reacts accordingly.

# External Dependencies

## Core Libraries
- **discord.py**: Primary Discord API wrapper for bot functionality and gateway connections
- **aiohttp**: Asynchronous HTTP client library for webhook delivery and external API communication
- **python-dotenv**: Environment variable management for configuration loading

## Discord Integration
- **Discord Bot Token**: Required authentication credential for Discord API access
- **Discord Gateway**: Real-time connection for receiving events and messages
- **Discord Intents**: Configured for message content and mention detection

## Webhook Infrastructure
- **External Webhook Endpoints**: HTTP endpoints that receive forwarded message data
- **HTTP Client Configuration**: Configurable timeout and retry settings for reliable delivery

## Runtime Environment
- **Python 3.7+**: Minimum runtime requirement for async/await syntax and modern features
- **Environment Variables**: Configuration through DISCORD_TOKEN, WEBHOOK_URL, and optional settings
- **File System**: Log file writing and optional .env file reading capabilities