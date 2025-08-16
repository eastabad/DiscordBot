# VPS数据库迁移指南 - 今日更新版本

## 📊 数据库更新内容

### 新增字段
**TradingView数据表 (tradingview_data) 新增字段：**
- `bullish_osc_rating` (FLOAT) - 看涨震荡评级
- `bullish_trend_rating` (FLOAT) - 看涨趋势评级  
- `bearish_osc_rating` (FLOAT) - 看跌震荡评级
- `bearish_trend_rating` (FLOAT) - 看跌趋势评级
- `current_timeframe` (VARCHAR) - 当前时间框架
- `data_type` (VARCHAR) - 数据类型标识 (signal/trade/close)

### 新增表
**ReportCache表 (report_cache) - 全新缓存表：**
- 智能报告缓存系统
- 基于symbol和timeframe的缓存键
- 自动过期和清理机制
- 命中次数统计

## 🚀 自动迁移 (推荐)

**使用现有的update-vps.sh脚本会自动处理所有数据库迁移：**

```bash
# 在VPS上运行
cd ~/discord-bot  # 你的项目目录
./update-vps.sh
```

**脚本会自动完成：**
1. ✅ 拉取最新代码（包含迁移脚本）
2. ✅ 执行数据库字段迁移
3. ✅ 创建ReportCache表
4. ✅ 验证迁移结果
5. ✅ 重启服务

## 🔧 手动迁移 (如需要)

如果自动迁移失败，可以手动执行：

```bash
# 1. 停止服务
docker-compose down

# 2. 执行迁移脚本
python3 migrate-database-fields.py

# 3. 启动服务
docker-compose up -d
```

## ✅ 验证迁移

### 检查数据库结构
```bash
# 连接数据库
docker-compose exec db psql -U postgres -d discord_bot

# 检查新字段
\d tradingview_data

# 检查新表
\d report_cache

# 退出
\q
```

### 检查数据统计
```bash
# 运行数据库检查脚本
python3 fix-database.py
```

**期望看到的输出：**
```
✅ tradingview_data表存在，共X条记录
✅ report_cache表存在，共0条记录
TradingView数据: 总计X (signal:X, trade:X, close:X)
报告缓存: 总计0 (有效:0)
```

## 🎯 迁移后的新功能

### 1. 智能评级系统
- 现在支持bullishrating和bearishrating计算
- 自动方向判断 (Rating看涨/看跌)
- 6级趋势强度分类

### 2. 缓存优化
- 相同symbol+timeframe的报告会被缓存
- 减少50-80%的Google API调用
- 自动缓存失效机制

### 3. 数据类型分离
- signal数据：用于报告主体章节
- trade/close数据：用于TDindicator Bot交易解读
- 提高数据查询效率

## 🔍 故障排除

### 常见问题

**1. 迁移脚本执行失败**
```bash
# 检查数据库连接
docker-compose ps
docker-compose logs db

# 手动修复
docker-compose exec db psql -U postgres -d discord_bot
```

**2. 字段添加失败**
```bash
# 检查现有字段
docker-compose exec db psql -U postgres -d discord_bot -c "\d tradingview_data"

# 手动添加缺失字段
docker-compose exec db psql -U postgres -d discord_bot -c "
ALTER TABLE tradingview_data ADD COLUMN bullish_osc_rating FLOAT;
ALTER TABLE tradingview_data ADD COLUMN bullish_trend_rating FLOAT;
..."
```

**3. 缓存表创建失败**
```bash
# 手动创建表
docker-compose exec db psql -U postgres -d discord_bot -c "
CREATE TABLE report_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    ...
);"
```

## 📊 迁移验证清单

- [ ] tradingview_data表包含5个新评级字段
- [ ] tradingview_data表包含data_type字段
- [ ] report_cache表已创建并包含所有必要字段
- [ ] 相关索引已创建
- [ ] 现有数据未丢失
- [ ] Discord机器人正常启动
- [ ] AI报告生成功能正常

## 🚨 回滚步骤

如果迁移后出现问题：

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复数据库备份 (如果有)
docker-compose exec db psql -U postgres -d discord_bot < backup_YYYYMMDD_HHMMSS.sql

# 3. 或者删除新字段 (不推荐)
docker-compose exec db psql -U postgres -d discord_bot -c "
ALTER TABLE tradingview_data DROP COLUMN bullish_osc_rating;
DROP TABLE report_cache;
"

# 4. 重启服务
docker-compose up -d
```

---

**注意：现有的update-vps.sh脚本已经包含自动迁移功能，推荐直接使用该脚本进行更新。**