# Discord转发机器人

一个Python Discord机器人，用于监听@提及并将频道信息转发到webhook。

## 功能特性

- 🤖 监听Discord中的@提及消息
- 📤 将消息和频道信息转发到指定的webhook
- 🔄 支持多种消息类型（文本、附件、嵌入内容等）
- 🛡️ 完善的错误处理和重试机制
- 📝 详细的日志记录
- ⚙️ 灵活的配置选项

## 安装要求

### Python依赖

```bash
pip install discord.py aiohttp python-dotenv
