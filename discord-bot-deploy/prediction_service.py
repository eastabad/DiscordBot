"""
股票趋势预测服务模块
基于简单的技术分析提供股票趋势预测建议
"""

import aiohttp
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import math

class StockPredictionService:
    """股票趋势预测服务类"""
    
    def __init__(self, config):
        """初始化预测服务"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 简单的技术分析参数
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.volume_threshold = 1.2  # 成交量异常阈值
        
    def analyze_price_trend(self, prices: List[float]) -> Dict:
        """分析价格趋势"""
        if len(prices) < 5:
            return {"trend": "数据不足", "confidence": 0}
        
        # 计算短期和长期平均价格
        short_avg = sum(prices[-3:]) / 3  # 最近3个数据点
        long_avg = sum(prices[-5:]) / 5   # 最近5个数据点
        
        # 价格变化百分比
        price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
        
        # 判断趋势
        if short_avg > long_avg * 1.02:
            trend = "上升趋势"
            confidence = min(85, abs(price_change) * 10)
        elif short_avg < long_avg * 0.98:
            trend = "下降趋势"  
            confidence = min(85, abs(price_change) * 10)
        else:
            trend = "横盘整理"
            confidence = 60
            
        return {
            "trend": trend,
            "confidence": confidence,
            "price_change": price_change,
            "short_avg": short_avg,
            "long_avg": long_avg
        }
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        if len(gains) < period:
            return None
            
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_trading_signals(self, symbol: str, trend_data: Dict, rsi: Optional[float] = None) -> Dict:
        """生成交易信号"""
        signals = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "signals": [],
            "overall_sentiment": "中性",
            "risk_level": "中等"
        }
        
        # 基于趋势的信号
        if trend_data["trend"] == "上升趋势" and trend_data["confidence"] > 70:
            signals["signals"].append({
                "type": "买入信号",
                "reason": f"价格呈现强劲上升趋势，信心度{trend_data['confidence']:.1f}%",
                "strength": "强"
            })
            signals["overall_sentiment"] = "看涨"
        elif trend_data["trend"] == "下降趋势" and trend_data["confidence"] > 70:
            signals["signals"].append({
                "type": "卖出信号", 
                "reason": f"价格呈现明显下降趋势，信心度{trend_data['confidence']:.1f}%",
                "strength": "强"
            })
            signals["overall_sentiment"] = "看跌"
            
        # 基于RSI的信号
        if rsi is not None:
            if rsi < self.rsi_oversold:
                signals["signals"].append({
                    "type": "买入信号",
                    "reason": f"RSI指标{rsi:.1f}显示超卖，可能反弹",
                    "strength": "中"
                })
            elif rsi > self.rsi_overbought:
                signals["signals"].append({
                    "type": "卖出信号",
                    "reason": f"RSI指标{rsi:.1f}显示超买，可能回调", 
                    "strength": "中"
                })
        
        # 价格变化幅度风险评估
        price_change = abs(trend_data.get("price_change", 0))
        if price_change > 10:
            signals["risk_level"] = "高"
        elif price_change > 5:
            signals["risk_level"] = "中等"
        else:
            signals["risk_level"] = "低"
            
        return signals
    
    async def get_prediction(self, symbol: str) -> Dict:
        """获取股票趋势预测"""
        try:
            # 模拟价格数据（实际应用中应从真实API获取）
            mock_prices = self.generate_mock_price_data(symbol)
            
            # 分析趋势
            trend_analysis = self.analyze_price_trend(mock_prices)
            
            # 计算RSI
            rsi = self.calculate_rsi(mock_prices)
            
            # 生成交易信号
            signals = self.generate_trading_signals(symbol, trend_analysis, rsi)
            
            # 生成预测报告
            prediction = {
                "symbol": symbol,
                "analysis_time": datetime.now().isoformat(),
                "trend_analysis": trend_analysis,
                "technical_indicators": {
                    "rsi": rsi,
                    "rsi_status": self.get_rsi_status(rsi) if rsi else "数据不足"
                },
                "trading_signals": signals,
                "recommendation": self.generate_recommendation(trend_analysis, signals),
                "disclaimer": "此预测仅供参考，投资有风险，决策需谨慎"
            }
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"生成预测失败 {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": "预测生成失败",
                "message": "无法获取足够数据进行分析"
            }
    
    def generate_mock_price_data(self, symbol: str) -> List[float]:
        """生成模拟价格数据（用于演示）"""
        # 基于symbol生成不同的模拟数据
        import hashlib
        seed = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16) % 1000
        
        base_price = 100 + seed / 10
        prices = [base_price]
        
        # 生成15个价格点模拟趋势
        for i in range(14):
            # 添加随机波动
            change = ((seed + i * 13) % 41 - 20) / 100  # -0.2 to 0.2
            trend = math.sin(i * 0.3) * 0.05  # 添加趋势成分
            new_price = prices[-1] * (1 + change + trend)
            prices.append(max(new_price, 1))  # 确保价格为正
            
        return prices
    
    def get_rsi_status(self, rsi: float) -> str:
        """获取RSI状态描述"""
        if rsi < 30:
            return "超卖区间，可能反弹"
        elif rsi > 70:
            return "超买区间，可能回调"
        elif rsi < 40:
            return "偏弱，需观察支撑"
        elif rsi > 60:
            return "偏强，需注意阻力"
        else:
            return "中性区间，震荡为主"
    
    def generate_recommendation(self, trend_data: Dict, signals: Dict) -> str:
        """生成投资建议"""
        trend = trend_data["trend"]
        confidence = trend_data["confidence"]
        sentiment = signals["overall_sentiment"]
        risk = signals["risk_level"]
        
        if sentiment == "看涨" and confidence > 75:
            return f"建议：考虑逢低买入。当前{trend}明显，但请控制仓位，风险等级：{risk}"
        elif sentiment == "看跌" and confidence > 75:
            return f"建议：考虑减仓或止损。当前{trend}明显，请注意风险管理，风险等级：{risk}"
        else:
            return f"建议：保持观望或小仓位操作。当前市场{trend}，建议等待明确方向，风险等级：{risk}"
    
    def format_prediction_message(self, prediction: Dict) -> str:
        """格式化预测消息用于Discord"""
        if "error" in prediction:
            return f"❌ {prediction['symbol']} 预测失败: {prediction['message']}"
        
        symbol = prediction["symbol"]
        trend = prediction["trend_analysis"]
        indicators = prediction["technical_indicators"]
        signals = prediction["trading_signals"]
        
        # 构建消息
        lines = [
            f"📈 **{symbol} 股票趋势预测分析**",
            f"",
            f"🔍 **趋势分析**",
            f"• 当前趋势: {trend['trend']}",
            f"• 信心度: {trend['confidence']:.1f}%",
            f"• 价格变化: {trend['price_change']:+.2f}%",
            f"",
            f"📊 **技术指标**",
        ]
        
        if indicators["rsi"]:
            lines.extend([
                f"• RSI: {indicators['rsi']:.1f}",
                f"• RSI状态: {indicators['rsi_status']}"
            ])
        else:
            lines.append("• RSI: 数据不足")
        
        lines.append(f"")
        lines.append(f"🎯 **交易信号** ({signals['overall_sentiment']})")
        
        if signals["signals"]:
            for signal in signals["signals"]:
                lines.append(f"• {signal['type']}: {signal['reason']}")
        else:
            lines.append("• 暂无明确信号")
        
        lines.extend([
            f"",
            f"💡 **投资建议**",
            f"{prediction['recommendation']}",
            f"",
            f"⚠️ {prediction['disclaimer']}"
        ])
        
        return "\n".join(lines)