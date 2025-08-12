# Overview

This project is a simplified Python-based Discord bot designed to handle three core user requests: stock chart generation, stock analysis, and image analysis. The bot focuses on providing high-quality trading insights while maintaining user request limits and automated channel cleanup. The system has been streamlined by removing the API server component to focus purely on Discord bot functionality.

## Recent Changes (August 12, 2025)

✅ **系统架构简化** - 移除API服务器，专注核心Discord机器人功能
- 创建简化版入口点 `simple_bot.py`，去掉API服务器组件
- 移除 `start_with_api` 方法，使用纯Discord机器人模式
- 保留三大核心功能：图表获取、股票分析、图片分析
- 保留用户限制系统和频道清理功能
- 简化部署配置，使用console输出模式

✅ **Discord机器人核心功能保留** - 专注用户核心需求
- 股票图表生成与TradingView集成 
- AI驱动的股票分析和预测
- 图表图像分析功能
- 用户每日请求限制（3次/天）
- VIP/豁免用户管理系统
- 自动频道清理（每日凌晨2点UTC）

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Architectural Decisions

**Bot Architecture**:
- Simplified design using `discord.py` commands.Bot framework.
- Event-driven architecture utilizing Discord's gateway events (`on_ready`, `on_message`).
- Asynchronous programming model with Python's `asyncio` for concurrency.
- Pure Discord bot mode - API server component removed for simplicity.

**Configuration Management**:
- Centralized system prioritizing environment variables over file-based configuration.
- Supports `.env` file loading and direct environment variable access.
- Includes validation for required parameters and sensible defaults.

**Message Processing Pipeline**:
- Listens for `@mention` events and stock commands in monitored Discord channels.
- Filters bot's own messages to prevent loops.
- Processes three core request types: stock charts, stock analysis, and image analysis.
- Maintains user request limits and provides admin management capabilities.

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