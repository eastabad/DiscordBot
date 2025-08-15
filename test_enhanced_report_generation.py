#!/usr/bin/env python3
"""
测试增强版报告生成功能
验证数据库驱动的报告生成系统
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_report_generator import GeminiReportGenerator
from models import get_db_session, TradingViewData
from datetime import datetime

def test_enhanced_report_generation():
    """测试增强版报告生成"""
    print("🚀 开始测试增强版报告生成...")
    print("=" * 60)
    
    try:
        # 初始化报告生成器
        report_generator = GeminiReportGenerator()
        print("✅ Gemini报告生成器初始化成功")
        
        # 获取数据库连接
        session = get_db_session()
        
        # 查看当前数据库中的数据
        print("\n📊 当前数据库中的TradingView数据:")
        all_data = session.query(TradingViewData).order_by(TradingViewData.received_at.desc()).limit(5).all()
        
        for data in all_data:
            print(f"  • {data.data_type:6} | {data.symbol:4} | {data.timeframe:3} | {data.action or 'N/A':4} | {data.received_at}")
        
        if not all_data:
            print("  ❌ 数据库中没有数据，请先运行webhook测试")
            return False
        
        # 测试用例1: AAPL 15m 信号数据报告
        print("\n🧪 测试用例1: AAPL 15m 增强版报告生成")
        print("-" * 40)
        
        aapl_report = report_generator.generate_enhanced_report("AAPL", "15m")
        
        if "❌" in aapl_report:
            print(f"⚠️  AAPL报告生成有问题: {aapl_report[:100]}...")
        else:
            print("✅ AAPL 15m 报告生成成功")
            print(f"   报告长度: {len(aapl_report)} 字符")
            print(f"   包含关键字: {'📊TDindicator Bot 交易解读' in aapl_report}")
            
            # 显示报告部分内容
            if len(aapl_report) > 500:
                print("\n📋 报告预览 (前200字符):")
                print(aapl_report[:200] + "...")
        
        # 测试用例2: 检查是否包含交易解读部分
        print("\n🧪 测试用例2: 验证交易解读部分")
        print("-" * 40)
        
        # 查找最新的trade数据
        latest_trade = session.query(TradingViewData).filter(
            TradingViewData.data_type.in_(['trade', 'close']),
            TradingViewData.action.isnot(None)
        ).order_by(TradingViewData.received_at.desc()).first()
        
        if latest_trade:
            print(f"✅ 找到最新交易数据: {latest_trade.symbol} {latest_trade.data_type} {latest_trade.action}")
            
            # 生成该股票的报告
            symbol_report = report_generator.generate_enhanced_report(
                latest_trade.symbol, 
                latest_trade.timeframe or '15m'
            )
            
            has_trade_section = "📊TDindicator Bot 交易解读" in symbol_report
            print(f"   包含交易解读部分: {has_trade_section}")
            
            if has_trade_section:
                # 提取交易解读部分
                start_idx = symbol_report.find("📊TDindicator Bot 交易解读")
                if start_idx != -1:
                    trade_section = symbol_report[start_idx:start_idx+300]
                    print(f"\n📊 交易解读部分预览:")
                    print(trade_section + "...")
        else:
            print("⚠️  数据库中没有找到trade/close数据")
        
        # 测试用例3: 数据库查询功能验证
        print("\n🧪 测试用例3: 数据库查询功能验证")
        print("-" * 40)
        
        # 测试signal数据查询
        signal_data = report_generator._get_latest_signal_data("AAPL", "15m")
        if signal_data:
            print("✅ Signal数据查询成功")
            print(f"   数据ID: {signal_data.id}, 接收时间: {signal_data.received_at}")
        else:
            print("❌ Signal数据查询失败")
        
        # 测试trade数据查询
        trade_data = report_generator._get_latest_trade_data("AAPL")
        if trade_data:
            print("✅ Trade数据查询成功")
            print(f"   数据类型: {trade_data.data_type}, 动作: {trade_data.action}")
        else:
            print("⚠️  Trade数据查询无结果")
        
        session.close()
        
        print("\n" + "=" * 60)
        print("🎉 增强版报告生成测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_report_generation()
    sys.exit(0 if success else 1)