# Docker容器化部署指南

## 为什么使用Docker
- ✅ 跨平台一致性
- ✅ 可部署到任何支持Docker的平台
- ✅ 环境隔离和版本控制
- ✅ 容易扩展和维护

## Docker文件配置

### 1. 创建Dockerfile
```dockerfile
# 使用Python 3.11官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/daily_logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口 (健康检查)
EXPOSE 5000

# 设置用户 (安全最佳实践)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 启动命令
CMD ["python", "main.py"]
```

### 2. 创建.dockerignore
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# 开发文件
*.md
!DEPLOYMENT_*.md
.gitignore
.replit
replit.nix

# 测试文件  
test_*
*_test.py

# 临时文件
daily_logs/*
discord_bot.log
app.log
attached_assets/*
```

### 3. 创建requirements.txt
```txt
discord.py>=2.5.2
aiohttp>=3.12.15
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.43
anthropic>=0.62.0
psutil>=7.0.0
flask>=3.1.1
```

### 4. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  discord-bot:
    build: .
    container_name: discord-bot
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - CHART_IMG_API_KEY=${CHART_IMG_API_KEY}
      - LAYOUT_ID=${LAYOUT_ID}
      - TRADINGVIEW_SESSION_ID=${TRADINGVIEW_SESSION_ID}
      - TRADINGVIEW_SESSION_ID_SIGN=${TRADINGVIEW_SESSION_ID_SIGN}
      - MONITOR_CHANNEL_IDS=${MONITOR_CHANNEL_IDS}
      - WEBHOOK_URL=${WEBHOOK_URL}
      - DATABASE_URL=postgresql://postgres:password@db:5432/discord_bot
    volumes:
      - ./daily_logs:/app/daily_logs
      - ./attached_assets:/app/attached_assets
    depends_on:
      - db
    networks:
      - discord-net

  db:
    image: postgres:16
    container_name: discord-bot-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=discord_bot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - discord-net

volumes:
  postgres_data:

networks:
  discord-net:
    driver: bridge
```

### 5. 创建环境变量文件 (.env)
```bash
# Discord配置
DISCORD_TOKEN=your_discord_bot_token

# TradingView配置
CHART_IMG_API_KEY=your_chart_api_key
LAYOUT_ID=your_layout_id
TRADINGVIEW_SESSION_ID=your_session_id
TRADINGVIEW_SESSION_ID_SIGN=your_session_sign

# 频道配置
MONITOR_CHANNEL_IDS=channel_id_1,channel_id_2

# 可选配置
WEBHOOK_URL=your_webhook_url
```

## 部署到不同平台

### 1. 本地开发部署
```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f discord-bot

# 停止服务
docker-compose down
```

### 2. 部署到DigitalOcean App Platform
创建 `.do/app.yaml`:
```yaml
name: discord-bot
services:
- name: discord-bot
  source_dir: /
  github:
    repo: yourusername/discord-bot
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 5000
  envs:
  - key: DISCORD_TOKEN
    scope: RUN_TIME
    type: SECRET
  - key: DATABASE_URL
    scope: RUN_TIME
    type: SECRET

databases:
- name: discord-bot-db
  engine: PG
  size: db-s-dev-database
```

### 3. 部署到Google Cloud Run
```bash
# 构建镜像
docker build -t gcr.io/YOUR_PROJECT_ID/discord-bot .

# 推送到Container Registry
docker push gcr.io/YOUR_PROJECT_ID/discord-bot

# 部署到Cloud Run
gcloud run deploy discord-bot \
  --image gcr.io/YOUR_PROJECT_ID/discord-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DISCORD_TOKEN=your_token
```

### 4. 部署到AWS ECS
创建任务定义 `task-definition.json`:
```json
{
  "family": "discord-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "discord-bot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/discord-bot:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DISCORD_TOKEN",
          "value": "your_token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/discord-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 监控和维护

### 1. 健康检查
```bash
# 检查容器状态
docker ps

# 查看日志
docker logs discord-bot

# 检查健康端点
curl http://localhost:5000/health
```

### 2. 资源监控
```bash
# 查看资源使用
docker stats discord-bot

# 容器信息
docker inspect discord-bot
```

### 3. 更新部署
```bash
# 重新构建
docker-compose build discord-bot

# 重启服务
docker-compose restart discord-bot

# 滚动更新
docker-compose up -d --no-deps discord-bot
```

## 安全最佳实践

### 1. 镜像安全
- 使用官方基础镜像
- 定期更新依赖
- 扫描安全漏洞
- 使用非root用户

### 2. 环境变量安全
- 使用Docker secrets
- 加密敏感信息
- 定期轮换密钥
- 限制环境变量暴露

### 3. 网络安全
```yaml
# 在docker-compose.yml中
networks:
  discord-net:
    driver: bridge
    internal: true  # 内部网络
```

## 成本优化

### 1. 镜像优化
- 使用多阶段构建
- 最小化镜像层
- 清理不必要文件
- 使用.dockerignore

### 2. 资源配置
```yaml
# 在docker-compose.yml中添加资源限制
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

## 总结

Docker部署的优势：
- 环境一致性
- 易于迁移
- 版本控制
- 自动化部署

适合场景：
- 需要自定义环境
- 多平台部署
- 企业级应用
- DevOps工作流

下一步可以选择具体的云平台进行部署，推荐优先级：
1. DigitalOcean App Platform (简单)
2. Google Cloud Run (弹性)  
3. AWS ECS (企业级)
4. Azure Container Instances (混合云)