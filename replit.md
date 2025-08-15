# Overview

This project is an advanced Python-based Discord bot with integrated API server capabilities, designed to provide high-quality trading insights. It handles four core user requests: stock chart generation, stock analysis, image analysis, and AI-powered report generation. The system ensures user request limits and automated channel cleanup, while also supporting enhanced data storage for various TradingView signal types (signal, trade, close). It features a comprehensive database-driven report generation system that queries stored historical data rather than relying on real-time webhook inputs. The project includes robust report channel monitoring for AI analysis and offers comprehensive AI-driven report generation with detailed technical indicator analysis, investment recommendations, and integrated trading insights. The system aims for fully autonomous operation with robust deployment solutions and dedicated logging systems.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Architectural Decisions

**Bot Architecture**:
- Advanced design using `discord.py` commands.Bot framework with an integrated API server for TradingView webhook integration.
- Event-driven architecture utilizing Discord's gateway events and asynchronous programming with Python's `asyncio`.
- Hybrid mode supporting both Discord bot functionality and API server capabilities.

**Configuration Management**:
- Centralized system prioritizing environment variables over file-based configuration, supporting `.env` file loading and direct access.

**Message Processing Pipeline**:
- Listens for `@mention` events and stock commands in monitored Discord channels, including dedicated "report" channels for AI analysis requests.
- Processes four core request types: stock charts, stock analysis, image analysis, and AI reports.
- Integrates with TradingView webhook data for real-time technical analysis and maintains user request limits.

**Error Handling Strategy**:
- Multi-layered approach with retry mechanisms (exponential backoff), comprehensive logging, and graceful degradation for external services.

**UI/UX Decisions**:
- Responses are primarily delivered via private messages to reduce channel spam, with a notification in the original channel.
- Uses clear error messages. Admin commands provide gold-colored embeds for exemption status.

## Technical Implementations & Feature Specifications

**Discord Bot Functionality**:
- Monitors multiple specified channels and handles various command formats.
- Differentiates channel behavior, prioritizing AI report processing in "report" channels.

**Stock Chart Generation & Analysis**:
- Generates stock charts using a Layout Chart Storage API, leveraging custom TradingView layouts.
- Responds to stock commands (e.g., "AAPL,1h") and integrates AI for chart image analysis (trend band signals, TrendTracer, EMA, support/resistance).
- Provides comprehensive stock trend prediction services with technical analysis algorithms and investment recommendations.
- Implements intelligent stock exchange detection for unknown symbols, covering over 500 mainstream US stocks.

**TradingView Webhook Integration**:
- Receives and parses TradingView webhook data, storing enhanced data types (signal, trade, close) with detailed trading fields.
- Supports 22+ technical indicator intelligent parsing and multi-timeframe trend analysis.
- Features database-driven report generation using stored historical data for comprehensive analysis.
- Generates structured AI reports with market overview, key signals, trend analysis, investment advice, risk warnings, and integrated trading insights including stop loss, take profit, and risk ratings.
- Implements intelligent data type detection for proper categorization of signals, trades, and position closures.

**User & Admin Management**:
- Implements a daily request limit (3 requests per user per day) using PostgreSQL.
- Includes an admin exemption system (`!exempt_add`, `!exempt_remove`, `!exempt_list`) and a VIP management system (`!vip_add`, `!vip_remove`, `!vip_list`).

**Channel Management**:
- Automatic daily channel cleanup (2 AM UTC) for monitored channels, intelligently filtering messages.

**Deployment & Logging**:
- Provides a comprehensive Docker deployment solution for VPS environments, including automated updates and self-recovery.
- Features a real-time logging system (`daily_logger.py`) for all user requests, storing JSON logs by date.
- Offers a dedicated web-based log viewer (`simple_log_viewer.py`) for detailed request tracking and real-time service status monitoring.

## Design Patterns

- **Dependency Injection**: Configuration and webhook handler instances injected.
- **Single Responsibility Principle**: Modules focused on specific tasks.
- **Observer Pattern**: Bot observes Discord message events.

# External Dependencies

## Core Libraries
- **discord.py**: Discord API wrapper.
- **aiohttp**: Asynchronous HTTP client.
- **python-dotenv**: Environment variable management.
- **SQLAlchemy**: ORM for database interactions.
- **psycopg2**: PostgreSQL adapter.

## Discord Integration
- **Discord Bot Token**: Authentication credential.
- **Discord Gateway**: Real-time connection.
- **Discord Intents**: Configured for `MESSAGE_CONTENT` and `GUILD_MESSAGES`.

## Webhook Infrastructure
- **External Webhook Endpoints**: HTTP endpoints for receiving forwarded Discord data.

## APIs & Services
- **Layout Chart Storage API (TradingView)**: For generating custom stock charts.
- **Chart-img API**: Used for testing symbol availability across exchanges.
- **AI Trend Band Signal Recognition Service**: For chart analysis.
- **Stock Trend Prediction Service**: For market predictions.
- **Google Gemini-2.5-pro**: For AI analysis report generation with enhanced database-driven prompts.

## Database
- **PostgreSQL**: Used for user tracking, daily request limits, VIP/exemption management, and enhanced TradingView data storage with intelligent data type categorization. Features database-driven report generation querying the latest signal and trade data for comprehensive analysis.

## Runtime Environment
- **Python 3.7+**.
- **Environment Variables**: For `DISCORD_TOKEN`, `WEBHOOK_URL`, `MONITOR_CHANNEL_IDS`, `CHART_IMG_API_KEY`, `LAYOUT_ID`, `REPORT_CHANNEL_ID`, and TradingView session.