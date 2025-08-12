#!/usr/bin/env python3
"""
测试多监控频道配置功能
"""

import os
import sys
from config import Config

def test_multiple_monitor_channels():
    """测试多个监控频道配置"""
    print("=== 测试多个监控频道配置 ===")
    
    # 测试1: 多个频道ID配置
    print("\n--- 测试1: 多个频道ID配置 ---")
    os.environ['MONITOR_CHANNEL_IDS'] = '1404532905916760125,1234567890123456789,9876543210987654321'
    
    config = Config()
    print(f"配置的监控频道IDs: {config.monitor_channel_ids}")
    print(f"频道数量: {len(config.monitor_channel_ids)}")
    
    # 验证频道ID格式
    for channel_id in config.monitor_channel_ids:
        if channel_id.isdigit():
            print(f"✅ 频道ID {channel_id} 格式正确")
        else:
            print(f"❌ 频道ID {channel_id} 格式错误")
    
    # 测试2: 单个频道ID配置（向后兼容）
    print("\n--- 测试2: 单个频道ID配置（向后兼容） ---")
    if 'MONITOR_CHANNEL_IDS' in os.environ:
        del os.environ['MONITOR_CHANNEL_IDS']
    os.environ['MONITOR_CHANNEL_ID'] = '1404532905916760125'
    
    config2 = Config()
    print(f"单个频道配置: {config2.monitor_channel_ids}")
    print(f"频道数量: {len(config2.monitor_channel_ids)}")
    
    # 测试3: 带空格的配置处理
    print("\n--- 测试3: 带空格的配置处理 ---")
    os.environ['MONITOR_CHANNEL_IDS'] = ' 1404532905916760125 , 1234567890123456789 , 9876543210987654321 '
    
    config3 = Config()
    print(f"处理空格后的配置: {config3.monitor_channel_ids}")
    
    # 验证所有频道ID都被正确处理
    for channel_id in config3.monitor_channel_ids:
        if ' ' in channel_id:
            print(f"❌ 频道ID '{channel_id}' 仍包含空格")
        else:
            print(f"✅ 频道ID '{channel_id}' 空格处理正确")
    
    # 测试4: 空配置处理
    print("\n--- 测试4: 空配置处理 ---")
    if 'MONITOR_CHANNEL_IDS' in os.environ:
        del os.environ['MONITOR_CHANNEL_IDS']
    if 'MONITOR_CHANNEL_ID' in os.environ:
        del os.environ['MONITOR_CHANNEL_ID']
    
    try:
        config4 = Config()
        print(f"空配置结果: {config4.monitor_channel_ids}")
    except Exception as e:
        print(f"空配置验证捕获到预期错误: {e}")
    
    print("\n=== 测试完成 ===")

def test_channel_checking_logic():
    """测试频道检查逻辑"""
    print("\n=== 测试频道检查逻辑 ===")
    
    # 设置测试配置
    os.environ['MONITOR_CHANNEL_IDS'] = '1404532905916760125,1234567890123456789'
    config = Config()
    
    # 模拟频道检查
    test_channels = [
        '1404532905916760125',  # 应该匹配
        '1234567890123456789',  # 应该匹配  
        '9999999999999999999',  # 不应该匹配
        '1404532905916760126',  # 不应该匹配（相似但不同）
    ]
    
    for channel_id in test_channels:
        is_monitored = channel_id in config.monitor_channel_ids
        status = "✅ 匹配" if is_monitored else "❌ 不匹配"
        print(f"频道 {channel_id}: {status}")
    
    print("\n=== 频道检查逻辑测试完成 ===")

if __name__ == "__main__":
    try:
        test_multiple_monitor_channels()
        test_channel_checking_logic()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()