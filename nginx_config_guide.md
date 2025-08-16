# Nginx反向代理配置指南

## 1. 安装Nginx（如果未安装）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
# 或者
sudo dnf install nginx
```

## 2. 创建配置文件

在你的VPS上创建或编辑nginx配置：

```bash
sudo nano /etc/nginx/sites-available/tdindicator.top
```

## 3. Nginx配置内容

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name www.tdindicator.top tdindicator.top;

    # 现有网站的根目录（保持你当前的网站）
    root /var/www/html;  # 根据你的实际路径调整
    index index.html index.htm index.php;

    # 现有网站的location（保持你当前的网站功能）
    location / {
        try_files $uri $uri/ =404;
        # 如果你有PHP或其他配置，保持原有配置
    }

    # Discord Bot API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Discord Bot Webhook反向代理
    location /webhook/ {
        proxy_pass http://127.0.0.1:5000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Discord Bot健康检查和文档
    location /bot-health {
        proxy_pass http://127.0.0.1:5000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /bot-docs {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTPS配置（使用Let's Encrypt SSL证书）
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.tdindicator.top tdindicator.top;

    # SSL证书配置（需要先申请证书）
    ssl_certificate /etc/letsencrypt/live/www.tdindicator.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.tdindicator.top/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 现有网站的根目录
    root /var/www/html;  # 根据你的实际路径调整
    index index.html index.htm index.php;

    # 现有网站的location
    location / {
        try_files $uri $uri/ =404;
    }

    # Discord Bot API反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Discord Bot Webhook反向代理
    location /webhook/ {
        proxy_pass http://127.0.0.1:5000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Discord Bot健康检查和文档
    location /bot-health {
        proxy_pass http://127.0.0.1:5000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /bot-docs {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 4. 激活配置

```bash
# 创建软链接激活配置
sudo ln -s /etc/nginx/sites-available/tdindicator.top /etc/nginx/sites-enabled/

# 测试nginx配置
sudo nginx -t

# 重新加载nginx
sudo systemctl reload nginx
```

## 5. 申请SSL证书（推荐）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 申请SSL证书
sudo certbot --nginx -d www.tdindicator.top -d tdindicator.top

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 3 * * * /usr/bin/certbot renew --quiet
```

## 6. 配置完成后的Webhook地址

配置完成后，你的TradingView webhook地址将是：

**HTTPS（推荐）：**
```
https://www.tdindicator.top/webhook/tradingview
```

**HTTP：**
```
http://www.tdindicator.top/webhook/tradingview
```

## 7. 其他可用端点

- 健康检查：`https://www.tdindicator.top/bot-health`
- API文档：`https://www.tdindicator.top/bot-docs`
- 发送消息：`https://www.tdindicator.top/api/send-message`
- 发送私信：`https://www.tdindicator.top/api/send-dm`
- 发送图表：`https://www.tdindicator.top/api/send-chart`

## 8. 测试配置

配置完成后，可以使用以下命令测试：

```bash
# 测试健康检查
curl https://www.tdindicator.top/bot-health

# 测试webhook
curl -X POST https://www.tdindicator.top/webhook/tradingview \
-H "Content-Type: application/json" \
-d '{"symbol":"AAPL","action":"buy","price":150.00}'
```

## 注意事项

1. **防火墙配置**：确保80和443端口开放
2. **现有网站**：这个配置会保持你现有网站的功能
3. **SSL证书**：强烈建议配置HTTPS
4. **日志监控**：可以查看nginx日志来监控访问情况

```bash
# 查看nginx访问日志
sudo tail -f /var/log/nginx/access.log

# 查看nginx错误日志
sudo tail -f /var/log/nginx/error.log
```