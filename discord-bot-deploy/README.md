# Discord机器人VPS部署包

## 快速开始

1. **上传到VPS**:
   ```bash
   scp -r discord-bot-deploy/ user@your-vps-ip:~/
   ```

2. **连接VPS并部署**:
   ```bash
   ssh user@your-vps-ip
   cd discord-bot-deploy
   chmod +x vps-deploy.sh
   ./vps-deploy.sh
   ```

3. **配置环境变量**:
   ```bash
   nano .env
   # 至少设置 DISCORD_TOKEN
   ```

4. **启动机器人**:
   ```bash
   docker-compose up -d
   ```

## 文件说明

- `main.py` - 主程序入口 (包含健康检查)
- `Dockerfile` - Docker镜像定义
- `docker-compose.yml` - 服务编排
- `vps-deploy.sh` - 一键部署脚本
- `VPS_DEPLOYMENT_GUIDE.md` - 详细部署指南

## 健康检查

部署成功后访问: `http://your-vps-ip:5000/health`

## 支持系统

- Ubuntu 20.04+
- Debian 11+
- CentOS 8+
- Rocky Linux 8+
