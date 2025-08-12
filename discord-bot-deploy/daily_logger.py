#!/usr/bin/env python3
"""
每日用户请求日志记录器
记录用户请求的详细信息，提供实时查看功能
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import asyncio
from pathlib import Path

class DailyRequestLogger:
    """每日请求日志记录器"""
    
    def __init__(self):
        """初始化日志记录器"""
        self.logger = logging.getLogger(__name__)
        self.log_dir = Path("daily_logs")
        self.log_dir.mkdir(exist_ok=True)
        
    def get_today_log_file(self) -> Path:
        """获取今天的日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"requests_{today}.json"
    
    def log_request(self, user_id: str, username: str, request_type: str, 
                   content: str, success: bool = True, error: str = None, 
                   channel_name: str = None, guild_name: str = None):
        """记录用户请求"""
        timestamp = datetime.now().isoformat()
        
        request_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "username": username,
            "request_type": request_type,  # "chart", "prediction", "analysis"
            "content": content,
            "success": success,
            "error": error,
            "channel": channel_name,
            "guild": guild_name
        }
        
        # 写入今天的日志文件
        log_file = self.get_today_log_file()
        requests = []
        
        # 读取现有日志
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
            except Exception as e:
                self.logger.error(f"读取日志文件失败: {e}")
                requests = []
        
        # 添加新请求
        requests.append(request_data)
        
        # 写回文件
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(requests, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"写入日志文件失败: {e}")
        
        # 同时输出到控制台
        status = "✅" if success else "❌"
        self.logger.info(f"📊 用户请求日志 {status} | {username}({user_id}) | {request_type.upper()} | {content[:50]}...")
    
    def get_today_summary(self) -> Dict[str, Any]:
        """获取今天的请求总结"""
        log_file = self.get_today_log_file()
        if not log_file.exists():
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_requests": 0,
                "users": {},
                "request_types": {},
                "success_rate": 100.0,
                "requests": []
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                requests = json.load(f)
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
            return {"error": str(e)}
        
        # 统计数据
        total_requests = len(requests)
        success_count = sum(1 for r in requests if r.get('success', True))
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 100.0
        
        # 按用户统计
        users = {}
        for request in requests:
            user = request['username']
            if user not in users:
                users[user] = {
                    "user_id": request['user_id'],
                    "total": 0,
                    "chart": 0,
                    "prediction": 0,
                    "analysis": 0,
                    "success": 0,
                    "failed": 0
                }
            
            users[user]["total"] += 1
            users[user][request['request_type']] += 1
            
            if request.get('success', True):
                users[user]["success"] += 1
            else:
                users[user]["failed"] += 1
        
        # 按请求类型统计
        request_types = {"chart": 0, "prediction": 0, "analysis": 0}
        for request in requests:
            req_type = request['request_type']
            if req_type in request_types:
                request_types[req_type] += 1
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_requests": total_requests,
            "users": users,
            "request_types": request_types,
            "success_rate": round(success_rate, 2),
            "success_count": success_count,
            "failed_count": total_requests - success_count,
            "requests": requests[-20:]  # 最近20条请求
        }
    
    def get_recent_days_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近几天的请求总结"""
        summaries = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            log_file = self.log_dir / f"requests_{date_str}.json"
            
            if not log_file.exists():
                summaries.append({
                    "date": date_str,
                    "total_requests": 0,
                    "users_count": 0,
                    "success_rate": 100.0
                })
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
                
                total = len(requests)
                success = sum(1 for r in requests if r.get('success', True))
                success_rate = (success / total * 100) if total > 0 else 100.0
                users_count = len(set(r['username'] for r in requests))
                
                summaries.append({
                    "date": date_str,
                    "total_requests": total,
                    "users_count": users_count,
                    "success_rate": round(success_rate, 2),
                    "success_count": success,
                    "failed_count": total - success
                })
                
            except Exception as e:
                self.logger.error(f"读取日志文件 {log_file} 失败: {e}")
                summaries.append({
                    "date": date_str,
                    "total_requests": 0,
                    "users_count": 0,
                    "success_rate": 100.0,
                    "error": str(e)
                })
        
        return summaries
    
    def print_today_summary(self):
        """打印今天的请求总结到控制台"""
        summary = self.get_today_summary()
        
        print("\n" + "="*60)
        print(f"📊 每日请求统计 - {summary['date']}")
        print("="*60)
        print(f"总请求数: {summary['total_requests']}")
        print(f"成功率: {summary['success_rate']}% ({summary.get('success_count', 0)}/{summary['total_requests']})")
        
        if summary['users']:
            print(f"\n👥 活跃用户 ({len(summary['users'])} 人):")
            for username, stats in summary['users'].items():
                print(f"  • {username}: {stats['total']}次 "
                      f"(📊{stats['chart']} 📈{stats['prediction']} 🖼️{stats['analysis']})")
        
        print(f"\n📈 请求类型分布:")
        for req_type, count in summary['request_types'].items():
            type_emoji = {"chart": "📊", "prediction": "📈", "analysis": "🖼️"}
            print(f"  • {type_emoji.get(req_type, '📋')} {req_type}: {count}")
        
        if summary['requests']:
            print(f"\n🕒 最近请求:")
            for request in summary['requests'][-5:]:  # 显示最后5条
                time = request['timestamp'].split('T')[1][:8]
                status = "✅" if request.get('success', True) else "❌"
                print(f"  {time} {status} {request['username']} - {request['request_type']} - {request['content'][:40]}...")
        
        print("="*60)

# 全局日志记录器实例
daily_logger = DailyRequestLogger()