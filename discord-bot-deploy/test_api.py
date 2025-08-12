#!/usr/bin/env python3
"""
API测试脚本
用于测试Discord Bot API功能
"""

import asyncio
import aiohttp
import json
import base64

async def test_health():
    """测试健康检查端点"""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:5000/api/health') as resp:
            print(f"健康检查: {resp.status}")
            result = await resp.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return resp.status == 200

async def test_send_chart():
    """测试发送图表API"""
    # 模拟n8n工作流数据
    test_data = [
        {
            "chartImgRequest": {
                "symbol": "NASDAQ:GOOG",
                "interval": "1h",
                "width": 1920,
                "height": 1080,
                "format": "png"
            },
            "discordPayload": {
                "content": "📊 您的GOOG 1小时图表:",
                "attachments": [
                    {
                        "id": "0",
                        "filename": "GOOG_1h.png",
                        "description": "Stock chart for GOOG (1h)",
                        "url": ""  # 空URL，模拟没有图片的情况
                    }
                ]
            },
            "authorId": 1145170623354638418,  # 您的用户ID
            "symbol": "GOOG",
            "timeframe": "1h",
            "currentCount": 1,
            "channelId": "",
            "messageId": "",
            "guildId": ""
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:5000/api/send-chart',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        ) as resp:
            print(f"发送图表: {resp.status}")
            result = await resp.text()
            print(f"响应: {result}")
            return resp.status == 200

async def test_send_dm():
    """测试发送私信API"""
    test_data = {
        "userId": 1145170623354638418,  # 您的用户ID
        "content": "🤖 API测试消息：Discord Bot API正常工作！"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:5000/api/send-dm',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        ) as resp:
            print(f"发送私信: {resp.status}")
            result = await resp.text()
            print(f"响应: {result}")
            return resp.status == 200

async def main():
    """主测试函数"""
    print("开始API测试...")
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    try:
        # 测试健康检查
        print("\n=== 测试健康检查 ===")
        await test_health()
        
        # 测试发送私信
        print("\n=== 测试发送私信 ===")
        await test_send_dm()
        
        # 测试发送图表
        print("\n=== 测试发送图表 ===")
        await test_send_chart()
        
        print("\n✅ API测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())