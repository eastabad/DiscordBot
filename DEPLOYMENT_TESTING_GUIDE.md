# VPS部署成功验证指南

## 🧪 完整测试流程

### 1. 基础连接测试

```bash
# 检查VPS连接
ssh user@your-vps-ip

# 检查系统信息
uname -a
free -h
df -h
```

### 2. Docker环境验证

```bash
# 检查Docker版本
docker --version
docker-compose --version

# 检查Docker服务状态
sudo systemctl status docker

# 检查Docker用户组
groups $USER
```

### 3. 项目部署状态检查

```bash
# 进入项目目录
cd DiscordBot

# 检查项目文件
ls -la

# 检查环境配置
cat .env

# 检查Docker配置
cat docker-compose.yml
```

### 4. 容器运行状态验证

```bash
# 检查所有容器状态
docker-compose ps

# 预期输出示例：
#     Name                   Command               State           Ports
# ----------------------------------------------------------------
# discord-bot          python main.py               Up      0.0.0.0:5000->5000/tcp
# discord-bot-db       docker-entrypoint.sh ...     Up      0.0.0.0:5432->5432/tcp

# 检查容器详细信息
docker ps
```

### 5. 健康检查测试

```bash
# 内部健康检查
curl http://localhost:5000/health

# 预期返回：
# {
#   "status": "healthy",
#   "timestamp": "2025-08-12T13:30:00Z",
#   "bot_running": true,
#   "started_at": "2025-08-12T13:25:00Z"
# }

# 外部健康检查
curl http://your-vps-ip:5000/health

# 如果无法访问，检查防火墙：
sudo ufw status
```

### 6. 日志分析

```bash
# 查看Discord机器人日志
docker-compose logs discord-bot

# 预期看到的成功日志：
# discord-bot    | 2025-08-12 13:25:00 - INFO - 🚀 启动简化版TDbot-tradingview...
# discord-bot    | 2025-08-12 13:25:00 - INFO - ✅ 环境变量验证通过
# discord-bot    | 2025-08-12 13:25:01 - INFO - ✅ 配置加载完成
# discord-bot    | 2025-08-12 13:25:01 - INFO - ✅ Discord机器人初始化完成
# discord-bot    | 2025-08-12 13:25:02 - INFO - 机器人已登录: TDbot-tradingview (ID: xxxx)

# 查看数据库日志
docker-compose logs db

# 实时日志监控
docker-compose logs -f discord-bot
```

### 7. 数据库连接测试

```bash
# 测试数据库连接
docker-compose exec db pg_isready -U postgres

# 连接数据库检查表
docker-compose exec db psql -U postgres discord_bot -c "\dt"

# 检查数据库连接
docker-compose exec discord-bot python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://postgres:discord123@db:5432/discord_bot'))
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

### 8. Discord机器人状态验证

```bash
# 检查机器人是否在线（在Discord中验证）
# 1. 打开Discord应用
# 2. 查看服务器成员列表
# 3. 确认机器人显示为在线状态（绿色圆点）

# 发送测试消息验证功能
# 在监控频道中发送：@TDbot-tradingview AAPL,1h
```

### 9. 网络和端口测试

```bash
# 检查端口监听状态
sudo netstat -tulpn | grep 5000
sudo netstat -tulpn | grep 5432

# 检查防火墙规则
sudo ufw status verbose

# 测试外部访问
# 从本地计算机运行：
# curl http://your-vps-ip:5000/health
```

### 10. 资源使用监控

```bash
# 查看系统资源使用
htop

# 查看Docker容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

## 🚨 常见问题诊断

### 问题1: 容器无法启动

```bash
# 诊断步骤
docker-compose logs discord-bot
docker-compose logs db

# 常见原因和解决方法
# 1. 端口被占用
sudo netstat -tulpn | grep 5000
sudo kill -9 <PID>

# 2. 环境变量未设置
cat .env
# 确保DISCORD_TOKEN已设置

# 3. 权限问题
sudo chown -R $USER:$USER .
```

### 问题2: 健康检查失败

```bash
# 检查服务是否运行
docker-compose ps

# 检查端口绑定
docker port discord-bot

# 检查防火墙
sudo ufw allow 5000/tcp
sudo ufw reload

# 重启服务
docker-compose restart discord-bot
```

### 问题3: Discord机器人离线

```bash
# 检查机器人日志
docker-compose logs discord-bot | grep ERROR

# 验证Token
echo $DISCORD_TOKEN  # 应该显示有效的token

# 重新设置环境变量
nano .env
docker-compose restart discord-bot
```

### 问题4: 数据库连接问题

```bash
# 检查数据库状态
docker-compose exec db pg_isready -U postgres

# 重启数据库
docker-compose restart db

# 检查数据库日志
docker-compose logs db
```

## ✅ 成功部署的标志

部署成功时，您应该看到：

1. **容器状态正常**
```bash
docker-compose ps
# 所有服务显示 "Up" 状态
```

2. **健康检查通过**
```bash
curl http://localhost:5000/health
# 返回 {"status": "healthy", "bot_running": true}
```

3. **Discord机器人在线**
- 在Discord中显示绿色在线状态
- 能够响应@mention命令

4. **日志无错误**
```bash
docker-compose logs discord-bot
# 看到成功登录信息，无ERROR级别日志
```

5. **外部访问正常**
```bash
curl http://your-vps-ip:5000/health
# 能够从外部访问健康检查端点
```

## 🔧 自动化测试脚本

创建测试脚本：

```bash
cat > test-deployment.sh << 'EOF'
#!/bin/bash
echo "🧪 开始VPS部署测试..."

# 1. 检查Docker
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker未安装或未启动"
    exit 1
fi
echo "✅ Docker运行正常"

# 2. 检查容器状态
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ 容器未正常运行"
    docker-compose ps
    exit 1
fi
echo "✅ 容器运行正常"

# 3. 健康检查
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "❌ 健康检查失败"
    exit 1
fi
echo "✅ 健康检查通过"

# 4. 检查日志中是否有错误
if docker-compose logs discord-bot | grep -q "ERROR"; then
    echo "⚠️  发现错误日志"
    docker-compose logs discord-bot | grep "ERROR"
else
    echo "✅ 日志检查通过"
fi

echo "🎉 VPS部署测试完成！"
EOF

chmod +x test-deployment.sh
./test-deployment.sh
```

## 📊 性能基准测试

```bash
# CPU和内存使用测试
docker stats --no-stream

# 响应时间测试
time curl http://localhost:5000/health

# 并发测试（可选）
for i in {1..10}; do
    curl http://localhost:5000/health &
done
wait
```

## 📞 获取帮助

如果测试失败：

1. **检查完整日志**：`docker-compose logs`
2. **验证环境配置**：`cat .env`
3. **重启服务**：`docker-compose restart`
4. **查看系统资源**：`htop`, `df -h`
5. **检查网络连接**：`ping discord.com`

---

**测试完成后，您的Discord机器人应该已经在VPS上24/7稳定运行！**