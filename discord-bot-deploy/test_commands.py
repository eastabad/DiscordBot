#!/usr/bin/env python3
"""
命令测试脚本 - 验证Discord命令是否正常工作
"""

import os
import discord
from discord.ext import commands
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置机器人
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f"测试机器人已登录: {bot.user.name} (ID: {bot.user.id})")

@bot.command(name='ping')
async def ping(ctx):
    """测试ping命令"""
    await ctx.send("🏓 Pong! 命令系统正常工作")

@bot.command(name='quota')
async def quota(ctx):
    """测试配额命令"""
    user_id = str(ctx.author.id)
    username = ctx.author.display_name or ctx.author.name
    
    await ctx.send(f"📊 配额测试\n用户: {username}\nID: {user_id}")

@bot.command(name='vip_add')
@commands.has_permissions(administrator=True)
async def vip_add(ctx, user_id: str, *, reason: str = "管理员添加"):
    """测试VIP添加命令"""
    await ctx.send(f"✅ 测试VIP添加\n用户ID: {user_id}\n原因: {reason}")

@bot.command(name='vip_list')
@commands.has_permissions(administrator=True)
async def vip_list(ctx):
    """测试VIP列表命令"""
    await ctx.send("📋 测试VIP列表命令 - 功能正常")

@bot.command(name='test')
async def test(ctx):
    """基本测试命令"""
    await ctx.send("✅ 测试命令工作正常！")

if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN环境变量未设置")
        exit(1)
    
    print("🚀 启动命令测试机器人...")
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ 机器人启动失败: {e}")