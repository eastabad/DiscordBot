# Overview

This project is a simplified Python-based Discord bot designed to handle three core user requests: stock chart generation, stock analysis, and image analysis. The bot focuses on providing high-quality trading insights while maintaining user request limits and automated channel cleanup. The system has been streamlined by removing the API server component to focus purely on Discord bot functionality.

## Recent Changes (August 12, 2025)

✅ **VPS无限制用户功能** - VPS部署用户自动获得无限制使用权限
- 新增环境变量 `VPS_DEPLOYMENT=true` 启用所有用户无限制模式
- 修改 `rate_limiter.py` 检查VPS部署状态，自动豁免所有用户
- 更新Docker配置支持VPS_DEPLOYMENT环境变量
- 创建VPS部署状态查看命令 `!vps_status` (管理员专用)
- 生成专用部署脚本 `vps-unlimited-deploy.sh` 一键启用无限制模式
- 完整文档：VPS_UNLIMITED_DEPLOYMENT_GUIDE.md
- VPS用户无需手动添加豁免，系统自动识别并提供无限制服务

✅ **VPS Docker部署完整方案** - 创建完整的自主部署解决方案
- 创建完整Docker容器化配置：Dockerfile, docker-compose.yml, docker-requirements.txt  
- 开发一键部署脚本 `vps-deploy.sh` 支持Ubuntu/Debian/CentOS自动安装Docker
- 生成部署包 `discord-bot-deploy.tar.gz` (76KB) 包含所有必需文件
- 创建管理脚本：start.sh, stop.sh, restart.sh, logs.sh, backup.sh
- 配置健康检查端点，自动重启策略，数据持久化
- 完整文档：VPS_DEPLOYMENT_GUIDE.md, DEPLOYMENT_FINAL.md
- 支持$3-5/月VPS部署，实现完全自主控制的24/7运行

✅ **部署完整解决方案** - 彻底解决Replit云部署问题  
- 重写 `main.py` 作为统一部署入口点，包含健康检查功能
- 集成Discord机器人和HTTP服务器（端口5000）于单一进程
- 实现异步启动：先启动健康检查服务器，再启动Discord机器人
- 状态追踪：全局bot_status变量实时监控机器人运行状态
- 完整的环境变量验证和错误处理
- 符合Replit部署要求：main.py自动检测，HTTP健康检查通过

✅ **部署问题修复** - 解决Replit云部署健康检查失败问题
- 创建专用部署入口点 `deploy_main.py` 和 `main_deploy.py`
- 修复 `simple_bot.py` 中的类型安全问题（Discord token验证）
- 创建 `deploy_with_health.py` 包含HTTP健康检查服务器（端口5000）
- 确保部署系统可以找到正确的主入口点并通过健康检查
- 维持纯Discord机器人架构，无需复杂的API服务器

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

✅ **实时日志系统集成** - 完整的用户请求追踪和统计
- 创建 `daily_logger.py` 实时记录所有用户请求
- 集成到三大核心功能：图表、预测、分析请求
- JSON格式日志文件，按日期存储在 `daily_logs/` 目录
- 记录成功/失败状态、用户信息、请求内容、频道信息
- 创建 `log_viewer.py` 命令行工具查看历史统计
- 新增管理员命令 `!logs` 在Discord中查看今日统计
- 支持实时监控模式和多日趋势分析

✅ **专用日志查看网页** - 替代Discord命令的完整解决方案 
- 创建 `simple_log_viewer.py` Web应用，提供详细的日志查看界面
- 实时服务状态监控：Discord机器人、数据库、系统资源监控
- 按用户分组显示所有请求详情，包括具体股票代码和时间戳
- 支持多日期查看，每30秒自动刷新最新数据
- 修复JSON数组格式兼容性，正确显示所有历史记录
- 图片分析功能改进：强制要求用户提供股票代码（@机器人 AAPL + 图片）
- 网页端口5000，包含实时状态API接口

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