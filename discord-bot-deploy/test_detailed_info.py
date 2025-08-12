#!/usr/bin/env python3
"""
测试详细频道信息收集功能
"""

import asyncio
import json
from datetime import datetime

# 模拟Discord对象进行测试
class MockChannel:
    def __init__(self):
        self.id = 1404064475614548018
        self.name = "test-channel"
        self.type = "text"
        self.created_at = datetime(2024, 8, 1, 12, 0, 0)
        self.position = 1
        self.topic = "测试频道主题"
        self.nsfw = False
        self.slowmode_delay = 5
        self.category = None  # 避免循环依赖
        self.guild = None     # 避免循环依赖

class MockCategory:
    def __init__(self):
        self.id = 123456789
        self.name = "测试分类"
        self.position = 0

class MockGuild:
    def __init__(self):
        self.id = 987654321
        self.name = "测试服务器"
        self.owner_id = 111111111
        self.member_count = 150
        self.created_at = datetime(2023, 1, 1, 0, 0, 0)
        self.verification_level = "medium"
        self.explicit_content_filter = "members_without_roles"
        self.default_message_notifications = "only_mentions"
        self.features = ["COMMUNITY", "NEWS"]
        self.premium_tier = 2
        self.premium_subscription_count = 5
        self.channels = [MockChannel() for _ in range(10)]
        self.roles = [MockRole() for _ in range(8)]
        self.emojis = []
        self.members = [MockMember() for _ in range(150)]
        self.icon = None
        self.banner = None

class MockRole:
    def __init__(self):
        self.id = 222222222
        self.name = "测试角色"
        self.color = 0x00ff00
        self.permissions = MockPermissions()
        self.position = 1

class MockMember:
    def __init__(self):
        self.id = 333333333
        self.name = "test_user"
        self.display_name = "测试用户"
        self.bot = False
        self.status = "online"
        self.joined_at = datetime(2024, 1, 1, 0, 0, 0)
        self.roles = [MockRole()]
        self.guild_permissions = MockPermissions()
        self.premium_since = None

class MockPermissions:
    def __init__(self):
        self.administrator = False
        self.manage_guild = False
        self.manage_channels = False
        self.manage_messages = True
        self.kick_members = False
        self.ban_members = False
        self.read_messages = True
        self.send_messages = True
        self.embed_links = True
        self.attach_files = True
        self.read_message_history = True
        self.add_reactions = True
        self.use_external_emojis = True
        self.value = 123456

class MockUser:
    def __init__(self):
        self.id = 444444444
        self.name = "test_author"
        self.display_name = "测试作者"
        self.discriminator = "1234"
        self.bot = False
        self.avatar = None
        self.created_at = datetime(2022, 6, 15, 10, 30, 0)
        self.public_flags = 0

class MockBot:
    """模拟机器人类，测试信息收集功能"""
    def __init__(self):
        self.user = MockUser()
        self.user.id = 999999999

async def test_detailed_info_collection():
    """测试详细信息收集功能"""
    print("=== 测试详细信息收集功能 ===")
    
    # 创建模拟对象
    bot = MockBot()
    channel = MockChannel()
    guild = MockGuild()
    user = MockUser()
    
    print("\n--- 测试频道信息收集 ---")
    
    # 模拟频道信息收集
    try:
        channel_info = {
            'id': channel.id,
            'name': channel.name,
            'type': str(channel.type),
            'created_at': channel.created_at.isoformat(),
            'category': {
                'id': channel.category.id,
                'name': channel.category.name,
                'position': channel.category.position
            } if channel.category else None,
            'position': channel.position,
            'topic': channel.topic,
            'nsfw': channel.nsfw,
            'slowmode_delay': channel.slowmode_delay,
            'guild_id': channel.guild.id
        }
        
        print("频道信息收集成功:")
        print(json.dumps(channel_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"频道信息收集失败: {e}")
    
    print("\n--- 测试服务器信息收集 ---")
    
    # 模拟服务器信息收集
    try:
        guild_info = {
            'id': guild.id,
            'name': guild.name,
            'owner_id': guild.owner_id,
            'member_count': guild.member_count,
            'created_at': guild.created_at.isoformat(),
            'verification_level': guild.verification_level,
            'explicit_content_filter': guild.explicit_content_filter,
            'default_notifications': guild.default_message_notifications,
            'features': guild.features,
            'boost_level': guild.premium_tier,
            'boost_count': guild.premium_subscription_count,
            'channels': {
                'total': len(guild.channels),
                'text': len([c for c in guild.channels if hasattr(c, 'type') and c.type == 'text']),
                'voice': len([c for c in guild.channels if hasattr(c, 'type') and c.type == 'voice']),
                'categories': len([c for c in guild.channels if hasattr(c, 'type') and c.type == 'category'])
            },
            'roles_count': len(guild.roles),
            'emojis_count': len(guild.emojis),
            'statistics': {
                'online_members': len([m for m in guild.members if hasattr(m, 'status') and m.status == 'online']),
                'bot_count': len([m for m in guild.members if m.bot]),
                'human_count': len([m for m in guild.members if not m.bot])
            }
        }
        
        print("服务器信息收集成功:")
        print(json.dumps(guild_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"服务器信息收集失败: {e}")
    
    print("\n--- 测试用户上下文信息收集 ---")
    
    # 模拟用户上下文信息收集
    try:
        member = guild.members[0]  # 获取第一个成员作为测试
        user_context = {
            'basic': {
                'id': user.id,
                'name': user.name,
                'display_name': user.display_name,
                'bot': user.bot,
                'created_at': user.created_at.isoformat()
            },
            'roles': [
                {
                    'id': role.id,
                    'name': role.name,
                    'color': role.color,
                    'position': role.position
                } for role in member.roles
            ],
            'permissions': {
                'administrator': member.guild_permissions.administrator,
                'manage_guild': member.guild_permissions.manage_guild,
                'manage_channels': member.guild_permissions.manage_channels,
                'manage_messages': member.guild_permissions.manage_messages
            },
            'server_info': {
                'joined_server_at': member.joined_at.isoformat(),
                'premium_since': member.premium_since
            }
        }
        
        print("用户上下文信息收集成功:")
        print(json.dumps(user_context, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"用户上下文信息收集失败: {e}")
    
    print("\n--- 测试Webhook负载格式 ---")
    
    # 模拟完整的webhook负载
    try:
        webhook_payload = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'discord_mention',
            'version': '2.0',
            'data': {
                'message': {
                    'id': 555555555,
                    'content': '@bot 这是一条测试消息',
                    'content_preview': '@bot 这是一条测试消息',
                    'created_at': datetime.now().isoformat()
                },
                'channel': channel_info,
                'guild': guild_info,
                'author': user_context
            },
            'metadata': {
                'collection_timestamp': datetime.now().isoformat(),
                'bot_version': '2.0',
                'data_quality': 'enhanced'
            }
        }
        
        print("Webhook负载格式:")
        print(json.dumps(webhook_payload, indent=2, ensure_ascii=False))
        
        # 计算负载大小
        payload_size = len(json.dumps(webhook_payload))
        print(f"\n负载大小: {payload_size} 字节 ({payload_size/1024:.2f} KB)")
        
    except Exception as e:
        print(f"Webhook负载生成失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_detailed_info_collection())