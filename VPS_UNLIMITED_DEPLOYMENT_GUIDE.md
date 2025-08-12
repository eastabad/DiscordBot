# VPS部署无限制用户使用指南

## 🚀 VPS部署自动豁免功能

当您在VPS上部署Discord机器人时，所有用户将自动获得无限制使用权限，无需手动添加豁免用户。

## ✨ 功能特点

### 自动豁免系统
- 🔓 **所有用户无限制**：VPS部署模式下，所有用户都可以无限次使用股票图表、分析、预测功能
- 📊 **仍然记录使用**：系统依然会记录用户使用情况，便于统计分析
- 🎯 **零配置启用**：只需设置一个环境变量即可激活

### 与标准部署的区别

| 功能对比 | 标准部署 | VPS部署 |
|---------|---------|---------|
| 用户限制 | 每日3次 | ❌ 无限制 |
| 豁免管理 | 需手动添加 | ✅ 自动豁免 |
| 使用记录 | ✅ 完整记录 | ✅ 完整记录 |
| 管理命令 | ✅ 支持 | ✅ 支持 |

## 🛠️ 部署配置

### 1. 环境变量设置

在`.env`文件中添加：
```env
# VPS部署配置 - 启用无限制模式
VPS_DEPLOYMENT=true

# Discord配置 (必需)
DISCORD_TOKEN=your_discord_bot_token_here

# 其他可选配置...
CHART_IMG_API_KEY=your_chart_img_api_key
LAYOUT_ID=your_layout_id
MONITOR_CHANNEL_IDS=1234567890,0987654321
```

### 2. Docker部署
```bash
# 克隆项目
git clone https://github.com/eastabad/DiscordBot.git
cd DiscordBot

# 配置环境变量
cp .env.example .env
nano .env  # 设置 VPS_DEPLOYMENT=true 和 DISCORD_TOKEN

# 启动服务
docker-compose up -d

# 验证部署
docker-compose logs discord-bot
```

### 3. 验证无限制模式

部署完成后，查看日志确认VPS模式已启用：
```bash
docker-compose logs discord-bot | grep "VPS部署模式"
```

预期看到：
```
INFO - VPS部署模式：用户 用户名 (用户ID) 无限制使用
```

## 📋 管理命令

### 查看部署状态
在Discord中使用管理员命令：
```
!vps_status
```

显示当前部署模式和用户限制状态。

### 其他管理命令
```bash
!logs          # 查看今日使用统计
!exempt_list   # 查看手动豁免用户列表（VPS模式下可能为空）
!quota         # 个人用户查看配额状态（VPS模式显示无限制）
```

## 🔄 模式切换

### 启用VPS无限制模式
```bash
# 设置环境变量
echo "VPS_DEPLOYMENT=true" >> .env

# 重启服务
docker-compose restart discord-bot
```

### 切换回标准限制模式
```bash
# 修改环境变量
sed -i 's/VPS_DEPLOYMENT=true/VPS_DEPLOYMENT=false/' .env

# 重启服务
docker-compose restart discord-bot
```

## 📊 监控和日志

### 使用统计查看
VPS部署后可通过以下方式监控使用情况：

1. **Web界面**：访问 `http://your-vps-ip:5001/`
2. **Discord命令**：`!logs` 查看当日统计
3. **日志文件**：`daily_logs/requests_YYYY-MM-DD.json`

### 日志示例
```json
{
  "timestamp": "2025-08-12T14:30:00Z",
  "user_id": "123456789",
  "username": "TestUser",
  "request_type": "chart",
  "content": "AAPL,1h",
  "success": true,
  "channel_info": "股票交流群",
  "vps_mode": true
}
```

## ⚙️ 技术实现

### 代码逻辑
系统通过检查 `VPS_DEPLOYMENT` 环境变量来决定是否启用无限制模式：

```python
# rate_limiter.py 中的实现
import os
if os.getenv('VPS_DEPLOYMENT', '').lower() in ['true', '1', 'yes']:
    self.logger.info(f"VPS部署模式：用户 {username} 无限制使用")
    return True, 0, 999  # 返回999表示无限制
```

### 数据库记录
即使在无限制模式下，系统仍然会：
- 记录每次请求到数据库
- 更新用户使用统计
- 生成日志文件
- 支持历史数据查询

## 🔧 故障排除

### 常见问题

**Q: VPS模式未生效？**
A: 检查环境变量设置和容器重启：
```bash
# 检查环境变量
docker-compose exec discord-bot printenv | grep VPS_DEPLOYMENT

# 查看日志确认模式
docker-compose logs discord-bot | grep VPS
```

**Q: 用户仍受限制？**  
A: 确认环境变量格式正确：
```bash
# 正确格式
VPS_DEPLOYMENT=true

# 错误格式
VPS_DEPLOYMENT=True    # 注意大小写
VPS_DEPLOYMENT="true"  # 不要使用引号
```

**Q: 如何验证无限制功能？**
A: 
1. 使用测试用户连续发送多个请求（超过3次）
2. 查看 `!quota` 命令显示是否为无限制
3. 检查日志是否显示 "VPS部署模式" 字样

## 📈 使用建议

### 适用场景
- 私人或小团队使用
- VPS自主部署
- 需要频繁股票查询的场景
- 不想管理用户豁免列表

### 不适用场景
- 公共Discord服务器
- 需要控制API调用成本
- 希望限制用户使用频率

## 🎯 最佳实践

1. **监控API使用**：虽然用户无限制，但要注意外部API的调用限制和费用
2. **定期检查日志**：通过Web界面监控使用情况
3. **备份数据**：定期备份数据库和日志文件
4. **资源监控**：关注VPS资源使用情况

## 📞 支持

如果遇到问题：
1. 查看 `docker-compose logs discord-bot`
2. 检查 `!vps_status` 命令输出
3. 验证环境变量配置
4. 确认网络连接正常

---

**部署成功后，您的Discord机器人将为所有用户提供无限制的股票分析服务！** 🎉