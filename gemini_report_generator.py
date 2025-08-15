"""
Gemini AI报告生成器
使用Google Gemini API生成股票分析报告
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from models import TradingViewData

class GeminiReportGenerator:
    """Gemini AI报告生成器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY环境变量未设置")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.logger.info("✅ Gemini客户端初始化成功")
        except Exception as e:
            self.logger.error(f"❌ Gemini客户端初始化失败: {e}")
            raise
    
    def generate_stock_report(self, trading_data: TradingViewData, user_request: str = "") -> str:
        """基于TradingView数据生成股票分析报告"""
        try:
            # 解析原始数据
            raw_data = json.loads(trading_data.raw_data) if trading_data.raw_data else {}
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(trading_data, raw_data, user_request)
            
            # 调用Gemini API
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2048
                )
            )
            
            if response.text:
                self.logger.info(f"✅ 成功生成{trading_data.symbol}分析报告")
                return self._format_report(response.text, trading_data)
            else:
                self.logger.error("Gemini API返回空响应")
                return self._generate_fallback_report(trading_data, raw_data)
                
        except Exception as e:
            self.logger.error(f"生成Gemini报告失败: {e}")
            signals_list = self._extract_signals_from_data(raw_data)
            return self._generate_fallback_report(trading_data, raw_data, signals_list)
    
    def _build_analysis_prompt(self, trading_data: TradingViewData, raw_data: Dict, user_request: str) -> str:
        """构建分析提示词"""
        
        # 获取解析后的信号列表
        signals_list = self._extract_signals_from_data(raw_data)
        signals_text = '\n'.join([f"- {signal}" for signal in signals_list])
        
        # 获取止损止盈信息
        stop_loss = raw_data.get('stopLoss', {}).get('stopPrice', '未设置')
        take_profit = raw_data.get('takeProfit', {}).get('limitPrice', '未设置')
        trend_stop = raw_data.get('trend_change_volatility_stop', '未知')
        risk_level = raw_data.get('risk', '未知')
        osc_rating = raw_data.get('extras', {}).get('oscrating', '未知')
        trend_rating = raw_data.get('extras', {}).get('trendrating', '未知')
        
        # 使用新的报告模板
        prompt = f"""
生成一份针对 {trading_data.symbol} 的中文交易报告，格式为 Markdown，包含以下部分：

## 📈 市场概况
简要说明市场整体状态和当前交易环境。

## 🔑 关键交易信号
逐条列出以下原始信号，不做删改：
{signals_text}

## 📉 趋势分析
1. **趋势总结**：基于 3 个级别的 MA 趋势、TrendTracer 两个级别，以及 AI 智能趋势带，总结市场的总体趋势方向。
2. **当前波动分析**：结合 Heikin Ashi RSI 看涨、动量指标、中心趋势、WaveMatrix 状态、艾略特波浪趋势、RSI，对当前波动特征进行分析。
3. **Squeeze 与 Chopping 分析**：判断市场是否处于横盘挤压或震荡区间，并结合 PMA 与 ADX 状态分析趋势强弱。
4. **买卖压力分析**：基于 CVD 的状态评估资金流向及买卖力量对比。

## 💡 投资建议
给出基于上述分析的交易建议，并结合止损、止盈、趋势改变止损点：
- 止损：{stop_loss}
- 止盈：{take_profit}
- 趋势改变止损点：{trend_stop}

## ⚠️ 风险提示
结合风险等级{risk_level}、OscRating{osc_rating}与 TrendRating{trend_rating}，提醒潜在风险因素。

请生成专业且详细的分析报告，确保涵盖所有技术指标的综合分析。
        """
        
        return prompt
    
    def _format_technical_indicators(self, raw_data: Dict) -> str:
        """格式化技术指标信息"""
        indicators_text = ""
        
        # 趋势相关指标
        if raw_data.get('center_trend'):
            indicators_text += f"- 中心趋势: {raw_data['center_trend']}\n"
        
        if raw_data.get('rsi_state_trend'):
            indicators_text += f"- RSI状态趋势: {raw_data['rsi_state_trend']}\n"
        
        if raw_data.get('AIbandsignal'):
            indicators_text += f"- AI波段信号: {raw_data['AIbandsignal']}\n"
        
        if raw_data.get('TrendTracersignal'):
            indicators_text += f"- 趋势追踪信号: {raw_data['TrendTracersignal']}\n"
        
        # 动量指标
        if raw_data.get('MOMOsignal'):
            indicators_text += f"- 动量信号: {raw_data['MOMOsignal']}\n"
        
        if raw_data.get('RSIHAsignal'):
            indicators_text += f"- RSI-HA信号: {raw_data['RSIHAsignal']}\n"
        
        # 波动性指标
        if raw_data.get('choppiness'):
            indicators_text += f"- 震荡指数: {raw_data['choppiness']}\n"
        
        if raw_data.get('SQZsignal'):
            indicators_text += f"- 挤压信号: {raw_data['SQZsignal']}\n"
        
        # 其他重要指标
        if raw_data.get('adxValue'):
            indicators_text += f"- ADX值: {raw_data['adxValue']}\n"
        
        if raw_data.get('trend_change_volatility_stop'):
            indicators_text += f"- 趋势变化波动止损: {raw_data['trend_change_volatility_stop']}\n"
        
        return indicators_text
    
    def _extract_signals_from_data(self, raw_data: Dict) -> list:
        """从原始数据中提取解析的信号列表"""
        signals = []
        
        # 基础信号解析（简化版）
        if raw_data.get('pmaText'):
            pma_mapping = {
                'PMA Strong Bullish': 'PMA 强烈看涨',
                'PMA Bullish': 'PMA 看涨',
                'PMA Trendless': 'PMA 无明确趋势',
                'PMA Strong Bearish': 'PMA 强烈看跌',
                'PMA Bearish': 'PMA 看跌'
            }
            signals.append(pma_mapping.get(raw_data['pmaText'], 'PMA 状态未知'))
        
        if raw_data.get('CVDsignal'):
            cvd_mapping = {
                'cvdAboveMA': 'CVD 高于移动平均线 (买压增加，资金流入)',
                'cvdBelowMA': 'CVD 低于移动平均线 (卖压增加，资金流出)'
            }
            signals.append(cvd_mapping.get(raw_data['CVDsignal'], 'CVD 状态未知'))
        
        if raw_data.get('RSIHAsignal'):
            rsi_ha_mapping = {
                'BullishHA': 'Heikin Ashi RSI 看涨',
                'BearishHA': 'Heikin Ashi RSI 看跌'
            }
            signals.append(rsi_ha_mapping.get(raw_data['RSIHAsignal'], 'Heikin Ashi RSI 状态未知'))
        
        if raw_data.get('center_trend'):
            center_mapping = {
                'Strong Bullish': '中心趋势强烈看涨',
                'Weak Bullish': '中心趋势弱看涨',
                'Weak Bearish': '中心趋势弱看跌',
                'Strong Bearish': '中心趋势强烈看跌'
            }
            signals.append(center_mapping.get(raw_data['center_trend'], '中心趋势: 状态未知'))
        
        if raw_data.get('rsi_state_trend'):
            rsi_mapping = {
                'Bullish': 'RSI 看涨',
                'Bearish': 'RSI 看跌',
                'Neutral': 'RSI 中性'
            }
            signals.append(rsi_mapping.get(raw_data['rsi_state_trend'], 'RSI 趋势: 状态未知'))
        
        # 如果没有信号，返回基础数据
        if not signals:
            for key, value in raw_data.items():
                if key not in ['symbol', 'timestamp'] and value is not None:
                    signals.append(f"{key}: {value}")
        
        return signals
    
    def _format_report(self, report_text: str, trading_data: TradingViewData) -> str:
        """格式化最终报告"""
        
        header = f"""
📊 **{trading_data.symbol} 技术分析报告**
🕐 数据时间: {trading_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
⏱️ 时间框架: {trading_data.timeframe}
🤖 分析引擎: Gemini-2.5-Pro

{'='*50}

{report_text}

{'='*50}
⚠️ **免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""
        return header
    
    def _generate_fallback_report(self, trading_data: TradingViewData, raw_data: Dict, signals_list: list = None) -> str:
        """生成备用报告（当AI生成失败时）"""
        
        # 如果没有提供signals_list，从raw_data中提取
        if signals_list is None:
            signals_list = self._extract_signals_from_data(raw_data)
        
        signals_text = '\n'.join([f"- {signal}" for signal in signals_list]) if signals_list else "- 暂无可用信号"
        
        fallback_report = f"""
📊 **{trading_data.symbol} 技术分析报告**
🕐 数据时间: {trading_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
⏱️ 时间框架: {trading_data.timeframe}

## 🔑 关键交易信号
{signals_text}

## 📉 基础数据摘要
- 数据接收时间: {trading_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- 分析时间框架: {trading_data.timeframe}
- 数据来源: TradingView webhook

⚠️ **注意**: AI报告生成服务暂时不可用，以上为基础数据摘要。
⚠️ **免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""
        
        return fallback_report