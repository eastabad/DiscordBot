# VPS代码更新指南

## 🔄 快速更新步骤

### 1. 连接到VPS
```bash
ssh your-username@your-vps-ip
```

### 2. 进入项目目录
```bash
cd DiscordBot
```

### 3. 停止当前服务
```bash
docker-compose down
```

### 4. 更新代码
```bash
# 拉取最新代码
git pull origin main

# 检查更新内容
git log --oneline -5
```

### 5. 重新构建和启动
```bash
# 重新构建镜像（确保使用最新代码）
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

### 6. 验证更新
```bash
# 检查容器状态
docker-compose ps

# 查看启动日志
docker-compose logs discord-bot

# 检查机器人是否正常工作
curl http://localhost:5000/health
```

## 📋 详细更新步骤

### 方法1：标准更新（推荐）
```bash
# 进入项目目录
cd DiscordBot

# 停止服务
docker-compose down

# 备份当前配置（可选）
cp .env .env.backup

# 更新代码
git fetch origin
git reset --hard origin/main

# 检查是否需要更新环境配置
diff .env.example .env || echo "检查环境变量是否需要更新"

# 重新构建并启动
docker-compose build --no-cache
docker-compose up -d

# 验证服务状态
docker-compose logs -f discord-bot
```

### 方法2：保守更新（有重要数据时）
```bash
# 备份数据
docker-compose exec db pg_dump -U postgres discord_bot > backup_$(date +%Y%m%d).sql
tar -czf logs_backup_$(date +%Y%m%d).tar.gz daily_logs/

# 然后按方法1更新
```

### 方法3：完全重新部署
```bash
# 完全清理（注意：会丢失数据）
docker-compose down -v
docker system prune -a

# 重新克隆项目
cd ..
rm -rf DiscordBot
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot

# 恢复配置文件
cp ../DiscordBot.backup/.env .env  # 如果有备份的话

# 启动服务
docker-compose up -d
```

## ⚡ 一键更新脚本

创建更新脚本：
```bash
nano update.sh
```

脚本内容：
```bash
#!/bin/bash
set -e

echo "🔄 开始更新Discord机器人..."

# 停止服务
echo "停止当前服务..."
docker-compose down

# 备份配置
echo "备份配置文件..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 更新代码
echo "更新代码..."
git pull origin main

# 重新构建
echo "重新构建镜像..."
docker-compose build --no-cache

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待启动
echo "等待服务启动..."
sleep 10

# 检查状态
echo "检查服务状态..."
docker-compose ps
docker-compose logs discord-bot | tail -20

echo "✅ 更新完成！"
```

使用脚本：
```bash
chmod +x update.sh
./update.sh
```

## 🔍 验证更新成功

### 1. 检查容器状态
```bash
docker-compose ps
```
应该显示所有容器都在运行状态。

### 2. 检查机器人日志
```bash
docker-compose logs discord-bot | tail -20
```
应该看到机器人登录成功的消息。

### 3. 测试Discord命令
在Discord中测试：
- `!quota` - 查看配额状态
- `!exempt_list` - 查看豁免用户（管理员）
- `@机器人 AAPL,1h` - 测试股票查询

### 4. 检查Web界面
访问 `http://your-vps-ip:5001/` 查看日志界面是否正常。

## 📊 更新内容检查

此次更新主要变更：
- ✅ 恢复手动豁免系统
- ❌ 移除VPS自动无限制模式
- ✅ 保持原有的豁免用户管理命令
- ✅ 清理了自动豁免相关代码

## 🔧 故障排除

### 问题1：git pull失败
```bash
# 如果有本地修改冲突
git stash
git pull origin main
git stash pop
```

### 问题2：Docker构建失败
```bash
# 清理Docker缓存
docker system prune -a
docker-compose build --no-cache
```

### 问题3：服务启动失败
```bash
# 查看详细错误日志
docker-compose logs discord-bot
docker-compose logs db

# 检查配置文件
cat .env
```

### 问题4：端口冲突
```bash
# 检查端口占用
sudo netstat -tulpn | grep 5000
sudo netstat -tulpn | grep 5001

# 如果有冲突，停止占用端口的进程
sudo kill -9 <进程ID>
```

## 💡 更新最佳实践

1. **定期更新**：建议每周检查一次代码更新
2. **备份重要数据**：更新前备份数据库和日志
3. **测试验证**：更新后测试主要功能
4. **监控日志**：更新后监控日志确保稳定运行
5. **配置检查**：对比.env.example检查是否需要新的配置项

## 📞 获取帮助

如果更新过程中遇到问题：
1. 查看详细日志：`docker-compose logs discord-bot`
2. 检查GitHub最新提交：`git log --oneline -10`
3. 验证配置文件：`cat .env`
4. 重启服务：`docker-compose restart`

---

**现在您的VPS上的机器人已经更新为手动豁免系统模式！**