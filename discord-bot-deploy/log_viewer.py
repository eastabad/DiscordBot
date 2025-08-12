#!/usr/bin/env python3
"""
日志查看器
提供简单的命令行界面查看用户请求日志
"""

import argparse
import json
from datetime import datetime, timedelta
from daily_logger import DailyRequestLogger

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="查看用户请求日志")
    parser.add_argument("--today", action="store_true", help="显示今天的详细统计")
    parser.add_argument("--days", type=int, default=7, help="显示最近几天的总结 (默认7天)")
    parser.add_argument("--user", type=str, help="显示特定用户的请求")
    parser.add_argument("--type", type=str, choices=["chart", "prediction", "analysis"], help="按请求类型过滤")
    parser.add_argument("--watch", action="store_true", help="实时监控模式")
    
    args = parser.parse_args()
    
    logger = DailyRequestLogger()
    
    if args.watch:
        print("🔍 实时监控模式 - 按 Ctrl+C 退出")
        import time
        try:
            while True:
                print(f"\r📊 {datetime.now().strftime('%H:%M:%S')} - 监控中...", end="", flush=True)
                time.sleep(10)
                # 每10秒显示一次今天的总结
                summary = logger.get_today_summary()
                if summary['total_requests'] > 0:
                    print(f"\r总请求: {summary['total_requests']} | 用户: {len(summary['users'])} | 成功率: {summary['success_rate']}%", end="", flush=True)
        except KeyboardInterrupt:
            print("\n监控结束")
            return
    
    if args.today:
        logger.print_today_summary()
    else:
        # 显示最近几天的总结
        summaries = logger.get_recent_days_summary(args.days)
        
        print(f"\n📈 最近 {args.days} 天请求统计")
        print("="*70)
        print(f"{'日期':<12} {'请求数':<8} {'用户数':<8} {'成功率':<10} {'成功/失败'}")
        print("-"*70)
        
        for summary in reversed(summaries):  # 从最新的开始显示
            success = summary.get('success_count', 0)
            failed = summary.get('failed_count', 0)
            print(f"{summary['date']:<12} {summary['total_requests']:<8} {summary['users_count']:<8} "
                  f"{summary['success_rate']:<9}% {success}/{failed}")
        
        print("="*70)
        
        # 总计
        total_requests = sum(s['total_requests'] for s in summaries)
        print(f"总计: {total_requests} 请求")

if __name__ == "__main__":
    main()