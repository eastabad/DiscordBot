# VPS自动更新指南

## 🚀 一键更新工具

我为您创建了完整的VPS自动更新解决方案，让您能够轻松将本地代码更新部署到VPS上。

## 📁 工具文件

### 主要脚本
- **update-vps.sh** - VPS一键更新脚本
- **quick-deploy.sh** - 本地到VPS快速部署
- **vps-config.example.sh** - VPS配置文件示例

### 辅助工具
- **fix-database.py** - 数据库修复工具
- **test-rate-limit.py** - 用户限制功能测试
- **check-status.sh** - 服务状态检查

## ⚙️ 首次配置

### 1. 配置VPS连接信息
```bash
# 复制配置文件模板
cp vps-config.example.sh vps-config.sh

# 编辑配置文件
nano vps-config.sh
```

在 `vps-config.sh` 中填入：
```bash
VPS_HOST='your-vps-ip-address'    # 您的VPS IP地址
VPS_USER='root'                   # VPS登录用户名
VPS_PATH='~/DiscordBot'           # 项目在VPS上的路径
SSH_KEY=''                        # SSH密钥路径（可选）
```

### 2. 设置SSH密钥（推荐）
```bash
# 生成SSH密钥（如果没有）
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# 复制公钥到VPS
ssh-copy-id your-username@your-vps-ip

# 测试SSH连接
ssh your-username@your-vps-ip
```

## 🎯 使用方法

### 方法1：仅更新VPS（推荐）
适合代码已推送到GitHub，只需更新VPS的场景：
```bash
./update-vps.sh
```

**功能包括：**
- 自动SSH连接到VPS
- 拉取最新GitHub代码
- 停止Docker服务
- 重新构建镜像
- 启动服务
- 运行数据库修复
- 验证部署结果

### 方法2：本地到VPS完整部署
适合本地开发完成，需要提交并部署的场景：
```bash
./quick-deploy.sh
```

**功能包括：**
- 检查本地Git状态
- 自动提交本地更改
- 推送到GitHub
- 调用VPS更新脚本
- 完整部署流程

## 📋 更新流程详解

### 自动化步骤
1. **连接检查** - 测试SSH连接
2. **代码更新** - 从GitHub拉取最新代码
3. **服务停止** - 安全停止Docker容器
4. **配置备份** - 自动备份.env配置文件
5. **镜像重建** - 使用最新代码重新构建
6. **服务启动** - 启动所有Docker服务
7. **健康检查** - 验证应用是否正常运行
8. **数据库修复** - 自动运行数据库修复脚本
9. **状态报告** - 显示部署结果和访问地址

### 安全特性
- 自动备份配置文件
- Git stash保护本地更改
- 健康检查确保服务正常
- 一键回滚功能
- 详细的错误日志

## 🔧 高级功能

### 回滚操作
如果更新后发现问题，可以快速回滚：
```bash
# 更新脚本会询问是否回滚
# 输入 'rollback' 即可回滚到上一版本
```

### 手动回滚
```bash
ssh your-username@your-vps-ip
cd DiscordBot
git reset --hard HEAD~1
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 查看实时日志
```bash
# 通过SSH查看日志
ssh your-username@your-vps-ip
cd DiscordBot
docker-compose logs -f discord-bot
```

### 数据库维护
```bash
# 在VPS上运行数据库修复
ssh your-username@your-vps-ip
cd DiscordBot
python3 fix-database.py
python3 test-rate-limit.py
```

## 📊 更新验证

### 自动验证项目
更新脚本会自动检查：
- Docker容器运行状态
- 应用健康检查端点
- 数据库连接状态
- 用户限制功能

### 手动验证
```bash
# 检查服务状态
curl http://your-vps-ip:5000/health

# 查看日志界面
# 浏览器访问: http://your-vps-ip:5001/

# Discord测试
# 在Discord中使用: !quota, !logs 等命令
```

## 🚨 故障排除

### 常见问题

**SSH连接失败**
```bash
# 检查SSH配置
ssh -v your-username@your-vps-ip

# 检查防火墙
sudo ufw status
```

**Docker构建失败**
```bash
# 清理Docker缓存
docker system prune -a
docker-compose build --no-cache
```

**数据库连接失败**
```bash
# 检查数据库容器
docker-compose logs db

# 运行数据库修复
python3 fix-database.py
```

### 日志查看
```bash
# VPS更新日志
./update-vps.sh 2>&1 | tee update.log

# Docker服务日志
docker-compose logs discord-bot
docker-compose logs db
```

## 📈 最佳实践

### 更新频率
- **开发阶段**：每次功能完成后更新
- **稳定版本**：每周定期更新
- **紧急修复**：立即更新

### 安全建议
1. 定期备份VPS数据
2. 使用SSH密钥而非密码
3. 保持VPS系统更新
4. 监控应用日志

### 性能优化
1. 定期清理Docker缓存
2. 监控VPS资源使用
3. 优化数据库查询
4. 使用CDN加速（如需要）

## 🎉 示例使用场景

### 场景1：修复Bug后快速部署
```bash
# 本地修复代码
git add .
git commit -m "修复用户限制bug"
git push origin main

# 一键更新VPS
./update-vps.sh
```

### 场景2：新功能开发完成
```bash
# 使用快速部署（包含提交和推送）
./quick-deploy.sh
```

### 场景3：定期维护更新
```bash
# 更新并运行完整检查
./update-vps.sh
ssh your-username@your-vps-ip
cd DiscordBot
./check-status.sh
```

---

**通过这套自动化工具，您可以在几分钟内完成从本地开发到VPS生产环境的部署！**