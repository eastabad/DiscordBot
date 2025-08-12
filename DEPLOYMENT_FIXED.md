# Discord机器人部署修复指南

## 问题描述
原始部署失败的错误：
- 应用程序在根端点(/)上健康检查失败
- 运行命令只执行Python文件但没有指定主入口点
- 机器人未配置响应HTTP健康检查请求

## 解决方案

### 1. 创建专用部署入口点

已创建三个部署相关文件：

#### `deploy_main.py` (推荐用于Replit部署)
- 最简化的部署入口点
- 直接调用 `simple_bot.py` 的主函数
- 包含基本的环境变量验证
- 适合纯Discord机器人部署

#### `main_deploy.py` (生产环境优化版)
- 包含详细的环境验证和错误处理
- 生产级别的日志配置
- 适合更复杂的部署场景

#### `deploy_with_health.py` (包含健康检查)
- 同时运行Discord机器人和HTTP健康检查服务器
- 提供 `/` 和 `/health` 端点响应健康检查
- 使用端口5000（Replit唯一不被防火墙阻挡的端口）
- 适合需要HTTP健康检查的部署环境

### 2. 修复的技术问题

#### 类型安全修复
在 `simple_bot.py` 中添加了明确的token验证：
```python
# 确保discord_token存在
if not config.discord_token:
    logger.error("❌ Discord token 为空")
    sys.exit(1)
```

#### 环境变量验证
所有部署入口点都包含必需环境变量检查：
- `DISCORD_TOKEN` (必需)
- 其他可选配置变量的验证

### 3. 部署使用方法

#### 选项1: 简单部署 (推荐)
使用 `deploy_main.py` 作为主入口点：
```bash
python deploy_main.py
```

#### 选项2: 带健康检查的部署
如果部署平台需要HTTP健康检查，使用 `deploy_with_health.py`：
```bash
python deploy_with_health.py
```

#### 选项3: 生产环境部署
使用 `main_deploy.py` 用于生产环境：
```bash
python main_deploy.py
```

### 4. 环境变量配置

确保在Replit Secrets中设置以下变量：

#### 必需变量
```
DISCORD_TOKEN=your_discord_bot_token
```

#### 可选变量
```
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2
WEBHOOK_URL=your_webhook_url
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign
```

### 5. 部署验证

部署成功后，你应该看到类似的日志输出：
```
✅ 环境变量验证通过
✅ 配置加载完成
✅ Discord机器人初始化完成
🤖 正在连接Discord...
机器人已登录: TDbot-tradingview (ID: xxxx)
机器人在 X 个服务器中
```

如果使用带健康检查的版本，还会看到：
```
✅ 健康检查服务器启动在端口5000
```

### 6. 故障排除

#### 如果部署仍然失败：
1. 确认 `DISCORD_TOKEN` 在Replit Secrets中正确设置
2. 检查机器人权限和服务器配置
3. 查看部署日志中的具体错误信息
4. 尝试使用不同的部署入口点

#### 常见错误：
- "缺少DISCORD_TOKEN" → 在Secrets中添加Discord机器人token
- "Discord token 为空" → 检查token格式和有效性
- "连接失败" → 检查网络连接和Discord服务状态

## 更新记录
- 2025-08-12: 创建部署修复解决方案
- 修复健康检查问题
- 添加多种部署选项
- 完善错误处理和日志