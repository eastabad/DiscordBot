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
            return self._generate_fallback_report(trading_data, raw_data)
    
    def _build_analysis_prompt(self, trading_data: TradingViewData, raw_data: Dict, user_request: str) -> str:
        """构建分析提示词"""
        
        # 格式化时间戳
        data_time = trading_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""作为一名专业的股票技术分析师，请基于以下TradingView数据为股票 {trading_data.symbol} 生成详细的技术分析报告：

📊 **基础信息**
- 股票代码: {trading_data.symbol}
- 时间框架: {trading_data.timeframe}
- 数据时间: {data_time}

📈 **技术指标分析**
"""

        # 添加技术指标信息
        if raw_data:
            prompt += self._format_technical_indicators(raw_data)
        
        prompt += f"""

🎯 **分析要求**
请提供以下分析内容：

1. **当前趋势分析** - 基于多个时间框架的趋势判断
2. **技术指标解读** - 分析各项技术指标的含义和信号
3. **支撑阻力位** - 识别关键价位
4. **交易建议** - 给出具体的交易策略建议
5. **风险提示** - 分析潜在风险和注意事项

用户具体要求: {user_request if user_request else "无特殊要求"}

请用专业但易懂的语言撰写报告，适合中级投资者阅读。报告应该客观、准确，并包含适当的风险提示。
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
    
    def _generate_fallback_report(self, trading_data: TradingViewData, raw_data: Dict) -> str:
        """生成备用报告（当AI生成失败时）"""
        
        fallback_report = f"""
📊 **{trading_data.symbol} 技术分析报告**
🕐 数据时间: {trading_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
⏱️ 时间框架: {trading_data.timeframe}

**基础技术指标摘要:**
"""
        
        # 添加原始技术指标信息
        if raw_data:
            for key, value in raw_data.items():
                if value and key != 'symbol':
                    fallback_report += f"- {key}: {value}\n"
        
        fallback_report += """
⚠️ **注意**: AI报告生成服务暂时不可用，以上为基础数据摘要。
⚠️ **免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""
        
        return fallback_report