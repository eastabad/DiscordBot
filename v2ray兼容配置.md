# V2Ray兼容的Discord Bot部署方案

## 问题分析
- 端口443已被v2ray占用
- 需要在不影响v2ray的情况下添加Discord Bot功能
- 保持翻墙功能正常运行

## 解决方案：基于路径的反向代理

### 方案1：修改现有v2ray nginx配置（推荐）
在你现有的v2ray nginx配置中添加Discord Bot路径：

```nginx
# 在你现有的443端口配置中添加以下location块

# Discord Bot Webhook - TradingView数据接收
location /webhook/ {
    proxy_pass http://127.0.0.1:5000/webhook/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    client_max_body_size 10M;
}

# Discord Bot API - 消息发送等功能
location /api/ {
    proxy_pass http://127.0.0.1:5000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    client_max_body_size 10M;
}

# Discord Bot状态监控
location /bot-status {
    proxy_pass http://127.0.0.1:5000/api/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Discord Bot API文档
location /bot-api {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 方案2：使用不同端口（备选）
如果不想修改v2ray配置，可以使用其他端口：

```nginx
server {
    listen 8443 ssl http2;  # 使用8443端口
    server_name www.tdindicator.top tdindicator.top;
    
    # 使用相同的SSL证书
    ssl_certificate /etc/letsencrypt/live/www.tdindicator.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.tdindicator.top/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Discord Bot配置...
}
```

## 路径规划

### V2Ray路径（保持不变）
- `/` - 你的主网站
- `/your-v2ray-path` - v2ray WebSocket路径
- 其他现有路径

### Discord Bot路径（新增）
- `/webhook/` - TradingView webhook
- `/api/` - Discord Bot API
- `/bot-status` - 健康检查
- `/bot-api` - API文档

## 安全考虑

1. **路径隔离**: Discord Bot使用独立路径，不影响v2ray
2. **端口复用**: 共享443端口，节省资源
3. **SSL共享**: 使用相同的SSL证书
4. **访问控制**: 可以为Discord Bot路径添加额外的访问限制