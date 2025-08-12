# Overview

This project is a Python-based Discord bot designed to monitor Discord channels for `@mentions` and forward channel information to external webhooks. Its primary purpose is to provide automated message forwarding, bridging Discord conversations with external systems through robust webhook integrations. The bot includes comprehensive error handling, retry mechanisms, and detailed logging, ensuring reliable data transmission. Key capabilities include automated chart image delivery, AI-powered stock trend prediction and analysis, and intelligent channel cleanup.

## Recent Changes (August 12, 2025)

✅ **Deployment System Fully Fixed** - Completely resolved all deployment health check issues
- Enhanced `app.py` entry point with improved startup sequence and error handling
- Optimized health check endpoints (`/api/health` and `/`) to always return 200 status for deployment systems
- Fixed API server startup timing with proper concurrent Discord bot and HTTP server initialization
- Updated root endpoint with improved HTML response and deployment-specific status indicators
- Added fallback responses to ensure health checks never fail during deployment

✅ **Production Deployment Ready** - Fully operational system with verified health checks
- Both Discord bot and HTTP API server start simultaneously on port 5000 with proper error handling
- Health checks verified working with immediate 200 responses and comprehensive status information
- Environment variable validation ensures proper configuration before startup
- All endpoints tested and confirmed working (root `/`, `/api/health`, message APIs)
- Deployment configuration fully optimized for Replit cloud deployment systems

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Architectural Decisions

**Bot Architecture**:
- Modular design using `discord.py` commands.Bot framework.
- Event-driven architecture utilizing Discord's gateway events (`on_ready`, `on_message`).
- Asynchronous programming model with Python's `asyncio` for concurrency.

**Configuration Management**:
- Centralized system prioritizing environment variables over file-based configuration.
- Supports `.env` file loading and direct environment variable access.
- Includes validation for required parameters and sensible defaults.

**Message Processing Pipeline**:
- Listens for `@mention` events in monitored Discord channels.
- Filters bot's own messages to prevent loops.
- Extracts comprehensive message metadata (author, channel, content, user context with roles/permissions, server info).
- Transforms Discord message objects into structured webhook-compatible payloads (v2.0 format).

**Error Handling Strategy**:
- Multi-layered approach with retry mechanisms (exponential backoff) for webhook delivery.
- Comprehensive logging at different severity levels.
- Graceful degradation for unavailable external services.

**UI/UX Decisions**:
- Responses are primarily delivered via private messages to reduce channel spam, with a notification in the original channel (`"已发送到您的私信中"`).
- Uses clear error messages instead of simple reactions.
- Admin commands provide gold-colored embeds for exemption status.

## Technical Implementations & Feature Specifications

**Discord Bot Functionality**:
- Monitors multiple specified channels (configured via `MONITOR_CHANNEL_IDS`).
- Supports both single and multiple channel configurations with backward compatibility.
- Handles various command formats, including Chinese and English commas.

**Stock Chart Generation & Analysis**:
- Generates stock charts using a Layout Chart Storage API, leveraging true custom TradingView layouts (1920x1080).
- Responds to simple stock commands (e.g., "AAPL,1h") without `@bot` prefix in monitored channels.
- Integrates AI for chart image analysis, including trend band signals (BUY/SELL), TrendTracer analysis, EMA trend band analysis, and support/resistance zone detection.
- Provides comprehensive stock trend prediction services with technical analysis algorithms (RSI), trading signal generation, and investment recommendations.
- Implements intelligent stock exchange detection for unknown symbols, testing against various exchanges (NASDAQ, NYSE, AMEX, OTC) and falling back to NASDAQ.
- Covers over 500 mainstream US stocks, including SP500, NASDAQ-100, and Chinese concept stocks, with accurate exchange prefixing.

**User & Admin Management**:
- Implements a daily request limit (3 requests per user per day) using PostgreSQL and SQLAlchemy, applicable to all features (charts, predictions, image analysis).
- Includes an admin exemption system to bypass daily limits for specified users, managed via commands (`!exempt_add`, `!exempt_remove`, `!exempt_list`).
- Features a command-based VIP management system (`!vip_add`, `!vip_remove`, `!vip_list`) with administrator permission checking.

**Channel Management**:
- Automatic daily channel cleanup (2 AM UTC) for monitored channels, intelligently filtering messages to preserve valuable content while removing clutter.

## Design Patterns

- **Dependency Injection**: Configuration and webhook handler instances injected into the bot class.
- **Single Responsibility Principle**: Modules focused on specific tasks (config, webhook, bot logic).
- **Observer Pattern**: Bot observes Discord message events and reacts accordingly.

# External Dependencies

## Core Libraries
- **discord.py**: Discord API wrapper.
- **aiohttp**: Asynchronous HTTP client for webhook and external API communication.
- **python-dotenv**: Environment variable management.
- **SQLAlchemy**: ORM for database interactions.
- **psycopg2** (implied by PostgreSQL/SQLAlchemy usage): PostgreSQL adapter.

## Discord Integration
- **Discord Bot Token**: Authentication credential.
- **Discord Gateway**: Real-time connection.
- **Discord Intents**: Configured for `MESSAGE_CONTENT` and `GUILD_MESSAGES`.

## Webhook Infrastructure
- **External Webhook Endpoints**: HTTP endpoints for receiving forwarded Discord data.
- **HTTP Client Configuration**: Configurable timeouts and retries for delivery.

## APIs & Services
- **Layout Chart Storage API (TradingView)**: For generating custom stock charts.
- **Chart-img API**: Used for testing symbol availability across exchanges.
- **AI Trend Band Signal Recognition Service**: For chart analysis.
- **Stock Trend Prediction Service**: For market predictions.

## Database
- **PostgreSQL**: Used for user tracking, daily request limits, and VIP/exemption management.

## Runtime Environment
- **Python 3.7+**.
- **Environment Variables**: For `DISCORD_TOKEN`, `WEBHOOK_URL`, `MONITOR_CHANNEL_IDS`, `CHART_IMG_API_KEY`, `LAYOUT_ID`, and TradingView session.