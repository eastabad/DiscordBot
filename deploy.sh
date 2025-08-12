#!/bin/bash
set -e

echo "=== 更新系统 ==="
sudo apt update -y && sudo apt upgrade -y

echo "=== 安装 Python、pip、pm2、PostgreSQL 客户端 ==="
sudo apt install -y python3 python3-pip python3-venv postgresql-client
sudo npm install -g pm2

echo "=== 克隆项目 ==="
if [ ! -d "DiscordBot" ]; then
    git clone https://github.com/abad315/DiscordBot.git
fi
cd DiscordBot

echo "=== 创建虚拟环境 ==="
python3 -m venv venv
source venv/bin/activate

echo "=== 安装依赖 ==="
pip install --upgrade pip
pip install -r requirements.txt
pip install psycopg2-binary  # PostgreSQL 驱动

echo "=== 创建 .env 文件（请修改为你的真实值） ==="
cat > .env <<EOL
SESSION_SECRET=t5aZuv2Sb6qs8dKTQc6H0Tu5DSHU6N+r/m8X10KVyQ4oA0Jp3hJUCGr+/XG1aC25kfjrLEUkHdKUoQqDuoRgdQ==
DISCORD_TOKEN=MTQwNDE3MzUxMDA3NDU2NDcwOQ.Gov3pA.-FXpD4ZZRIIXslF8f4QY7s3ZLfnD18CH7g7RDU
WEBHOOK_URL=https://tv.tdindicator.top/webhook-test/discord
CHART_IMG_API_KEY=ZOZZS7E4MtOJBBQ0f3uO3g2GY4YkDrO4vuif7Ooc
LAYOUT_ID=Gc320R2h
TRADINGVIEW_SESSION_ID=m4gyrgsdj56tl9o26sybtldqhk6n5fjq
TRADINGVIEW_SESSION_ID_SIGN=v3:5S95PPfuVubh64QLxCR/KEJt6liAY6br/OuHbCyeOo0=
DATABASE_URL=postgresql://neondb_owner:npg_3SIY6kbdycji@ep-cold-sea-adl4vpy0.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
PGDATABASE=neondb
PGHOST=ep-cold-sea-adl4vpy0.c-2.us-east-1.aws.neon.tech
PGPORT=5432
PGUSER=neondb_owner
PGPASSWORD=npg_3SIY6kbdycji
MONITOR_CHANNEL_ID=1404532905916760125,1404064475614548018
EOL

echo "=== 初始化数据库表 ==="
python db_models.py

echo "=== 使用 pm2 后台启动 Bot ==="
pm2 delete discord-bot || true
pm2 start "venv/bin/python main.py" --name discord-bot
pm2 save
pm2 startup systemd -u $USER --hp $HOME

echo "=== 部署完成，Bot 已后台运行 ==="
pm2 status
