"""
Gemini AI报告生成器
使用Google Gemini API生成股票分析报告
"""
import json
import logging
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
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
                    max_output_tokens=4096  # 增加token限制以避免截断
                )
            )
            
            # 调试：打印完整响应
            self.logger.info(f"Gemini API完整响应: {response}")
            
            if response and hasattr(response, 'text') and response.text:
                self.logger.info(f"✅ 成功生成{trading_data.symbol}分析报告，长度: {len(response.text)}")
                return self._format_report(response.text, trading_data)
            elif response and hasattr(response, 'candidates') and response.candidates:
                # 尝试从candidates中提取文本
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'text') and part.text:
                                    self.logger.info(f"✅ 从candidates提取报告，长度: {len(part.text)}")
                                    return self._format_report(part.text, trading_data)
                        
                        # 检查是否因为MAX_TOKENS被截断
                        if hasattr(candidate, 'finish_reason') and str(candidate.finish_reason) == 'MAX_TOKENS':
                            self.logger.warning("Gemini响应被截断，使用备用报告")
                            return self._generate_fallback_report(trading_data, raw_data)
                
                self.logger.error("Gemini API candidates中未找到有效文本")
                return self._generate_fallback_report(trading_data, raw_data)
            else:
                self.logger.error("Gemini API返回空响应或格式异常")
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
        
        # 获取增强评级信息
        bullish_osc = raw_data.get('BullishOscRating', '未知')
        bullish_trend = raw_data.get('BullishTrendRating', '未知')
        bearish_osc = raw_data.get('BearishOscRating', '未知')
        bearish_trend = raw_data.get('BearishTrendRating', '未知')
        
        # 计算综合评级
        def safe_float_calc(value):
            try:
                return float(value) if value != '未知' else 0
            except:
                return 0
        
        bullish_rating = safe_float_calc(bullish_osc) + safe_float_calc(bullish_trend)
        bearish_rating = safe_float_calc(bearish_osc) + safe_float_calc(bearish_trend)
        
        # 构建信号列表字符串
        signals_text = ','.join(signals_list) if signals_list else '暂无可用信号'
        
        # 使用正确的报告模板格式
        prompt = f"""
请严格按照以下模板格式生成一份针对{trading_data.symbol}的中文交易报告，必须包含所有指定的字段和内容：

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
给出基于上述分析的交易建议，并结合趋势改变点，结合对比bullishrating和bearishrating的值，分析总结：
- 趋势改变止损点：{trend_stop}
- bullishrating：{bullish_rating} (看涨震荡评级: {bullish_osc} + 看涨趋势评级: {bullish_trend})
- bearishrating：{bearish_rating} (看跌震荡评级: {bearish_osc} + 看跌趋势评级: {bearish_trend})

基于以上评级对比分析，结合止损止盈策略：
- 止损：{stop_loss}  
- 止盈：{take_profit}

## ⚠️ 风险提示
根据关键交易信号，结合趋势总结，提醒潜在风险因素。重点关注：
- 风险等级：{risk_level}
- 多空力量对比：bullishrating ({bullish_rating}) vs bearishrating ({bearish_rating})
- 震荡与趋势评级差异分析
- 其他技术指标背离风险

请严格按照上述格式输出，确保所有字段都包含在内，特别是投资建议和风险提示部分的具体数值。
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
        """从原始数据中提取解析的信号列表，完全匹配JavaScript解析逻辑"""
        signals = []
        
        def safe_str(value):
            """安全字符串转换"""
            return str(value) if value is not None else ''
        
        def safe_int(value):
            """安全整数转换"""
            try:
                return int(float(value)) if value is not None else None
            except:
                return None
        
        def safe_float(value):
            """安全浮点数转换"""
            try:
                return float(value) if value is not None else None
            except:
                return None
        
        # PMA 信号
        pma_text = safe_str(raw_data.get('pmaText', ''))
        if pma_text == 'PMA Strong Bullish':
            signals.append('PMA 强烈看涨')
        elif pma_text == 'PMA Bullish':
            signals.append('PMA 看涨')
        elif pma_text == 'PMA Trendless':
            signals.append('PMA 无明确趋势')
        elif pma_text == 'PMA Strong Bearish':
            signals.append('PMA 强烈看跌')
        elif pma_text == 'PMA Bearish':
            signals.append('PMA 看跌')
        else:
            signals.append('PMA 状态未知')
        
        # CVD 信号
        cvd_signal = safe_str(raw_data.get('CVDsignal', ''))
        if cvd_signal == 'cvdAboveMA':
            signals.append('CVD 高于移动平均线 (买压增加，资金流入)')
        elif cvd_signal == 'cvdBelowMA':
            signals.append('CVD 低于移动平均线 (卖压增加，资金流出)')
        else:
            signals.append('CVD 状态未知')
        
        # RSIHAsignal 信号
        rsi_ha_signal = safe_str(raw_data.get('RSIHAsignal', ''))
        if rsi_ha_signal == 'BullishHA':
            signals.append('Heikin Ashi RSI 看涨')
        elif rsi_ha_signal == 'BearishHA':
            signals.append('Heikin Ashi RSI 看跌')
        else:
            signals.append('Heikin Ashi RSI 状态未知')
        
        # BBPsignal 信号
        bbp_signal = safe_str(raw_data.get('BBPsignal', '')).strip()
        if bbp_signal == 'bullpower':
            signals.append('多头主导控场')
        elif bbp_signal == 'bearpower':
            signals.append('空头主导控场')
        else:
            signals.append('市场控场状态未知')
        
        # Choppiness 信号
        choppiness = safe_float(raw_data.get('choppiness'))
        if choppiness is not None:
            if choppiness < 38.2:
                signals.append('市场处于趋势状态')
            elif choppiness <= 61.8:
                signals.append('市场处于过渡状态')
            else:
                signals.append('市场处于震荡状态')
        else:
            signals.append('Choppiness: 数据无效')
        
        # ADX 信号
        adx_value = safe_float(raw_data.get('adxValue'))
        if adx_value is not None:
            if adx_value < 20:
                signals.append('ADX 无趋势或弱趋势')
            elif adx_value < 25:
                signals.append('ADX 趋势开始形成')
            elif adx_value < 50:
                signals.append('ADX 强趋势')
            elif adx_value < 75:
                signals.append('ADX 非常强趋势')
            else:
                signals.append('ADX 极强趋势')
        else:
            signals.append('ADX: 数据无效')
        
        # RSI 信号
        rsi_state_trend = safe_str(raw_data.get('rsi_state_trend', ''))
        if rsi_state_trend == 'Bullish':
            signals.append('RSI 看涨')
        elif rsi_state_trend == 'Bearish':
            signals.append('RSI 看跌')
        elif rsi_state_trend == 'Neutral':
            signals.append('RSI 中性')
        else:
            signals.append('RSI 趋势: 状态未知')
        
        # 获取当前时间框架 - 优先使用Current_timeframe
        current_timeframe = raw_data.get('Current_timeframe')
        if not current_timeframe:
            # 回退到使用timeframe字段
            current_timeframe = raw_data.get('timeframe', '15')
            if current_timeframe.endswith('m'):
                current_timeframe = current_timeframe[:-1]
            elif current_timeframe.endswith('h'):
                current_timeframe = str(int(current_timeframe[:-1]) * 60)
        
        # MAtrend 信号（对应Current_timeframe的MA趋势）
        ma_trend = safe_int(raw_data.get('MAtrend'))
        if ma_trend == 1:
            signals.append(f'{current_timeframe} 分钟当前MA趋势: 上涨')
        elif ma_trend == 0:
            signals.append(f'{current_timeframe} 分钟当前MA趋势: 短线回调但未跌破 200 周期均线，观望')
        elif ma_trend == -1:
            signals.append(f'{current_timeframe} 分钟当前MA趋势: 下跌')
        else:
            signals.append(f'{current_timeframe} 分钟当前MA趋势: 状态未知')
        
        # MAtrend_timeframe1 信号
        tf1 = safe_str(raw_data.get('adaptive_timeframe_1', '15'))
        ma_trend1 = safe_int(raw_data.get('MAtrend_timeframe1'))
        if ma_trend1 == 1:
            signals.append(f'{tf1} 分钟 MA 趋势: 上涨')
        elif ma_trend1 == 0:
            signals.append(f'{tf1} 分钟 MA 趋势: 短线回调但未跌破 200 周期均线，观望')
        elif ma_trend1 == -1:
            signals.append(f'{tf1} 分钟 MA 趋势: 下跌')
        else:
            signals.append(f'{tf1} 分钟 MA 趋势: 状态未知')
        
        # MAtrend_timeframe2 信号
        tf2 = safe_str(raw_data.get('adaptive_timeframe_2', '60'))
        ma_trend2 = safe_int(raw_data.get('MAtrend_timeframe2'))
        if ma_trend2 == 1:
            signals.append(f'{tf2} 分钟 MA 趋势: 上涨')
        elif ma_trend2 == 0:
            signals.append(f'{tf2} 分钟 MA 趋势: 短线回调但未跌破 200 周期均线，观望')
        elif ma_trend2 == -1:
            signals.append(f'{tf2} 分钟 MA 趋势: 下跌')
        else:
            signals.append(f'{tf2} 分钟 MA 趋势: 状态未知')
        
        # Middle Smooth Trend 信号
        smooth_trend = safe_str(raw_data.get('Middle_smooth_trend', ''))
        if smooth_trend == 'Bullish +':
            signals.append('平滑趋势: 强烈看涨')
        elif smooth_trend == 'Bullish':
            signals.append('平滑趋势: 看涨')
        elif smooth_trend == 'Bearish +':
            signals.append('平滑趋势: 强烈看跌')
        elif smooth_trend == 'Bearish':
            signals.append('平滑趋势: 看跌')
        else:
            signals.append('平滑趋势: 状态未知')
        
        # MOMOsignal 信号
        momo_signal = safe_str(raw_data.get('MOMOsignal', ''))
        if momo_signal == 'bullishmomo':
            signals.append('动量指标: 看涨')
        elif momo_signal == 'bearishmomo':
            signals.append('动量指标: 看跌')
        else:
            signals.append('动量指标: 状态未知')
        
        # TrendTracersignal 信号 (对应Current_timeframe)
        trend_tracer_signal = safe_int(raw_data.get('TrendTracersignal'))
        if trend_tracer_signal == 1:
            signals.append(f'{current_timeframe} 分钟 TrendTracer 趋势: 蓝色上涨趋势')
        elif trend_tracer_signal == -1:
            signals.append(f'{current_timeframe} 分钟 TrendTracer 趋势: 粉色下跌趋势')
        else:
            signals.append(f'{current_timeframe} 分钟 TrendTracer 趋势: 状态未知')
        
        # TrendTracerHTF 信号 (对应adaptive_timeframe_1)
        trend_tracer_htf = safe_int(raw_data.get('TrendTracerHTF'))
        tf1 = safe_str(raw_data.get('adaptive_timeframe_1', '60'))
        if trend_tracer_htf == 1:
            signals.append(f'{tf1} 分钟 TrendTracer HTF 趋势: 蓝色上涨趋势')
        elif trend_tracer_htf == -1:
            signals.append(f'{tf1} 分钟 TrendTracer HTF 趋势: 粉色下跌趋势')
        else:
            signals.append(f'{tf1} 分钟 TrendTracer HTF 趋势: 状态未知')
        
        # trend_change_volatility_stop 信号
        trend_stop = raw_data.get('trend_change_volatility_stop')
        signals.append(f'趋势改变止损点: {trend_stop if trend_stop is not None else "未知"}')
        
        # AI 智能趋势带信号
        ai_band_signal = safe_str(raw_data.get('AIbandsignal', ''))
        if ai_band_signal in ['green uptrend', 'blue uptrend']:
            signals.append('AI 智能趋势带: 上升趋势')
        elif ai_band_signal in ['red downtrend', 'pink downtrend']:
            signals.append('AI 智能趋势带: 下降趋势')
        elif ai_band_signal == 'yellow neutral':
            signals.append('AI 智能趋势带: 中性趋势')
        else:
            signals.append('AI 智能趋势带: 状态未知')
        
        # Squeeze Momentum 信号
        sqz_signal = safe_str(raw_data.get('SQZsignal', ''))
        if sqz_signal == 'squeeze':
            signals.append('市场处于横盘挤压')
        elif sqz_signal == 'no squeeze':
            signals.append('市场不在横盘挤压')
        else:
            signals.append('Squeeze Momentum: 状态未知')
        
        # Chopping Range 信号
        chopping_signal = safe_str(raw_data.get('choppingrange_signal', ''))
        if chopping_signal == 'chopping':
            signals.append('Chopping Range: 市场处于震荡区间')
        elif chopping_signal in ['no chopping', 'trending']:
            signals.append('Chopping Range: 市场处于趋势状态')
        else:
            signals.append('Chopping Range: 状态未知')
        
        # Center Trend 信号
        center_trend = safe_str(raw_data.get('center_trend', ''))
        if center_trend in ['Strong Bullish']:
            signals.append('中心趋势强烈看涨')
        elif center_trend in ['Bullish', 'Weak Bullish']:
            signals.append('中心趋势看涨')
        elif center_trend in ['Bearish', 'Weak Bearish']:
            signals.append('中心趋势看跌')
        elif center_trend == 'Strong Bearish':
            signals.append('中心趋势强烈看跌')
        elif center_trend == 'Neutral':
            signals.append('中心趋势中性')
        else:
            signals.append('中心趋势: 状态未知')
        
        # WaveMatrix 状态信号
        wave_state = safe_str(raw_data.get('wavemarket_state', ''))
        if wave_state == 'Long Strong':
            signals.append('WaveMatrix 状态: 强烈上涨趋势')
        elif wave_state in ['Long Moderate', 'Long Weak']:
            signals.append('WaveMatrix 状态: 温和上涨趋势')
        elif wave_state == 'Short Strong':
            signals.append('WaveMatrix 状态: 强烈下跌趋势')
        elif wave_state in ['Short Moderate', 'Short Weak']:
            signals.append('WaveMatrix 状态: 温和下跌趋势')
        elif wave_state == 'Neutral':
            signals.append('WaveMatrix 状态: 中性')
        else:
            signals.append('WaveMatrix 状态: 状态未知')
        
        # Elliott Wave Trend 信号
        ewo_trend = safe_str(raw_data.get('ewotrend_state', ''))
        if ewo_trend == 'Strong Bullish':
            signals.append('艾略特波浪趋势: 强烈上涨趋势')
        elif ewo_trend in ['Bullish', 'Weak Bullish']:
            signals.append('艾略特波浪趋势: 上涨趋势')
        elif ewo_trend in ['Bearish', 'Weak Bearish']:
            signals.append('艾略特波浪趋势: 下跌趋势')
        elif ewo_trend == 'Strong Bearish':
            signals.append('艾略特波浪趋势: 强烈下跌趋势')
        elif ewo_trend == 'Neutral':
            signals.append('艾略特波浪趋势: 中性')
        else:
            signals.append('艾略特波浪趋势: 状态未知')
        
        # HTFwave_signal 信号
        htf_wave = safe_str(raw_data.get('HTFwave_signal', ''))
        if htf_wave == 'Bullish':
            signals.append('高时间框架波浪信号: 看涨')
        elif htf_wave == 'Bearish':
            signals.append('高时间框架波浪信号: 看跌')
        elif htf_wave == 'Neutral':
            signals.append('高时间框架波浪信号: 中性')
        else:
            signals.append('高时间框架波浪信号: 状态未知')
        
        # 增强评级系统分析 (新增5个字段)
        bullish_osc = safe_float(raw_data.get('BullishOscRating'))
        bullish_trend = safe_float(raw_data.get('BullishTrendRating'))
        bearish_osc = safe_float(raw_data.get('BearishOscRating'))
        bearish_trend = safe_float(raw_data.get('BearishTrendRating'))
        
        if all(rating is not None for rating in [bullish_osc, bullish_trend, bearish_osc, bearish_trend]):
            # 计算综合评级
            bullish_rating = bullish_osc + bullish_trend
            bearish_rating = bearish_osc + bearish_trend
            
            # 判断看涨还是看跌
            if bullish_rating > bearish_rating:
                rating_direction = "Rating看涨"
                strength_diff = bullish_rating - bearish_rating
            elif bearish_rating > bullish_rating:
                rating_direction = "Rating看跌"
                strength_diff = bearish_rating - bullish_rating
            else:
                rating_direction = "Rating中性"
                strength_diff = 0
            
            # 根据差额确定趋势强弱
            if strength_diff >= 40:
                trend_strength = "极强"
            elif strength_diff >= 30:
                trend_strength = "很强" 
            elif strength_diff >= 20:
                trend_strength = "强"
            elif strength_diff >= 10:
                trend_strength = "中等"
            elif strength_diff > 0:
                trend_strength = "弱"
            else:
                trend_strength = "平衡"
            
            # 添加综合评级分析
            signals.append(f'{rating_direction} (多方评级: {bullish_rating}, 空方评级: {bearish_rating})')
            signals.append(f'趋势强度: {trend_strength} (差额: {strength_diff})')
            
            # 详细评级细分
            signals.append(f'看涨震荡评级: {bullish_osc}/100, 看涨趋势评级: {bullish_trend}/100')
            signals.append(f'看跌震荡评级: {bearish_osc}/100, 看跌趋势评级: {bearish_trend}/100')
        
        # 传统OscRating 和 TrendRating 比较
        extras = raw_data.get('extras', {})
        osc_rating = safe_float(extras.get('oscrating'))
        trend_rating = safe_float(extras.get('trendrating'))
        
        if osc_rating is not None and trend_rating is not None:
            if osc_rating > trend_rating:
                signals.append('趋势初期，结构不稳，波动幅度较高')
            elif osc_rating < trend_rating:
                signals.append('趋势主导，方向性强，波动相对平稳')
            else:
                signals.append('趋势状态平衡，波动适中')
        else:
            signals.append('趋势评级状态: 未知')
        
        # 止损和止盈信号
        if 'stopLoss' in raw_data and isinstance(raw_data['stopLoss'], dict):
            stop_price = raw_data['stopLoss'].get('stopPrice')
            if isinstance(stop_price, (int, float)):
                signals.append(f'止损价格: {stop_price}')
        
        if 'takeProfit' in raw_data and isinstance(raw_data['takeProfit'], dict):
            take_price = raw_data['takeProfit'].get('limitPrice')
            if isinstance(take_price, (int, float)):
                signals.append(f'止盈价格: {take_price}')
        
        if 'risk' in extras:
            signals.append(f'风险等级: {extras["risk"]}')
        
        # 交易建议
        action = raw_data.get('action', 'unknown')
        big_trend_desc = '上涨' if ma_trend2 == 1 else ('下跌' if ma_trend2 == -1 else '观望')
        trade_direction = '做多' if action == 'buy' else ('做空' if action == 'sell' else '未知')
        
        if trade_direction != '未知':
            is_reverse = (action == 'buy' and ma_trend2 < 0) or (action == 'sell' and ma_trend2 > 0)
            if is_reverse:
                suggestion = f'大级别趋势为{big_trend_desc}，该交易为{trade_direction}方向的反向交易，关注{tf1}、{tf2}级别的supply、demand，以及图表中出现的反转、背离信号，及时离场。'
            else:
                signal_type = '顶部信号' if action == 'buy' else '底部信号'
                suggestion = f'大级别趋势为{big_trend_desc}趋势，关注{tf2}的supply、demand和wavematrix是否出现{signal_type}。'
        else:
            suggestion = '趋势不明朗，离场观望等待信号'
        
        signals.append(f'交易建议: {suggestion}')
        
        return signals
    
    def generate_enhanced_report(self, symbol: str, timeframe: str) -> str:
        """生成增强版报告 - 使用数据库中的最新数据"""
        try:
            # 从数据库获取最新的signal数据和trade/close数据
            signal_data = self._get_latest_signal_data(symbol, timeframe)
            trade_data = self._get_latest_trade_data(symbol)
            
            if not signal_data:
                return f"❌ 未找到 {symbol} 的最新信号数据，无法生成报告"
            
            # 从数据库解析信号
            signals = self._parse_signals_from_database(signal_data)
            
            # 提取趋势改变止损点
            trend_stop = self._extract_trend_stop_from_data(signal_data)
            
            # 构建报告提示词
            prompt = self._build_enhanced_report_prompt(symbol, signals, trend_stop, trade_data)
            
            self.logger.info(f"开始生成{symbol}增强版分析报告...")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                self.logger.info(f"✅ 成功生成{symbol}增强版分析报告，长度: {len(response.text)}")
                return response.text
            elif response and hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'text') and part.text:
                                    self.logger.info(f"✅ 从candidates提取增强版报告，长度: {len(part.text)}")
                                    return part.text
                
                self.logger.error("Gemini API candidates中未找到有效文本")
                return f"❌ 报告生成失败：AI服务未返回有效内容"
            else:
                self.logger.error("Gemini返回空响应")
                return f"❌ 报告生成失败：AI服务返回空响应"
                
        except Exception as e:
            self.logger.error(f"生成增强版分析报告失败: {e}")
            return f"❌ 报告生成失败：{str(e)}"
    
    def _get_latest_signal_data(self, symbol: str, timeframe: str):
        """获取最新的signal数据"""
        try:
            from models import get_db_session, TradingViewData
            session = get_db_session()
            
            latest_signal = session.query(TradingViewData).filter(
                TradingViewData.symbol == symbol.upper(),
                TradingViewData.timeframe == timeframe,
                TradingViewData.data_type == 'signal'
            ).order_by(TradingViewData.received_at.desc()).first()
            
            session.close()
            return latest_signal
            
        except Exception as e:
            self.logger.error(f"获取signal数据失败: {e}")
            return None
    
    def _get_latest_trade_data(self, symbol: str):
        """获取最新的trade或close数据"""
        try:
            from models import get_db_session, TradingViewData
            session = get_db_session()
            
            latest_trade = session.query(TradingViewData).filter(
                TradingViewData.symbol == symbol.upper(),
                TradingViewData.data_type.in_(['trade', 'close']),
                TradingViewData.action.isnot(None)
            ).order_by(TradingViewData.received_at.desc()).first()
            
            session.close()
            return latest_trade
            
        except Exception as e:
            self.logger.error(f"获取trade数据失败: {e}")
            return None
    
    def _parse_signals_from_database(self, signal_data):
        """从数据库记录中解析信号"""
        try:
            import json
            raw_data = json.loads(signal_data.raw_data)
            
            # 重用现有的信号解析逻辑
            return self._extract_signals_from_data(raw_data)
            
        except Exception as e:
            self.logger.error(f"解析信号数据失败: {e}")
            return ["信号解析失败"]
    
    def _extract_trend_stop_from_data(self, signal_data):
        """提取趋势改变止损点"""
        try:
            import json
            raw_data = json.loads(signal_data.raw_data)
            return raw_data.get('trend_change_volatility_stop', 'N/A')
        except:
            return 'N/A'
    
    def _extract_rating_data(self, signal_data):
        """提取评级数据"""
        try:
            import json
            raw_data = json.loads(signal_data.raw_data)
            
            def safe_float_calc(value):
                try:
                    return float(value) if value and value != '未知' else 0
                except:
                    return 0
            
            bullish_osc = raw_data.get('BullishOscRating', '未知')
            bullish_trend = raw_data.get('BullishTrendRating', '未知')
            bearish_osc = raw_data.get('BearishOscRating', '未知')
            bearish_trend = raw_data.get('BearishTrendRating', '未知')
            
            bullish_rating = safe_float_calc(bullish_osc) + safe_float_calc(bullish_trend)
            bearish_rating = safe_float_calc(bearish_osc) + safe_float_calc(bearish_trend)
            
            return bullish_rating, bearish_rating, bullish_osc, bullish_trend, bearish_osc, bearish_trend
            
        except Exception as e:
            self.logger.error(f"提取评级数据失败: {e}")
            return 0, 0, '未知', '未知', '未知', '未知'
    
    def _build_enhanced_report_prompt(self, symbol: str, signals: list, trend_stop: str, trade_data):
        """构建增强版报告生成提示词"""
        
        # 从最新的signal数据中提取评级信息
        signal_data = self._get_latest_signal_data(symbol, '15m')  # 使用15m作为默认
        bullish_rating, bearish_rating, bullish_osc, bullish_trend, bearish_osc, bearish_trend = self._extract_rating_data(signal_data)
        
        # 格式化信号列表
        signals_text = '\n'.join(f'• {signal}' for signal in signals)
        
        # 基础报告模板
        base_prompt = f"""
生成一份针对 {symbol} 的中文交易报告，格式为 Markdown，包含以下部分：

## 📈 市场概况
简要说明市场整体状态和当前交易环境。

## 🔑 关键交易信号
逐条列出以下原始信号，不做删改：
{signals_text}

## 📉 趋势分析
1. **趋势总结**：基于 3 个级别的 MA 趋势、TrendTracer 两个级别，以及 AI 智能趋势带，总结市场的总体趋势方向。
2. **当前波动分析**：结合 Heikin Ashi RSI 看涨、动量指标、中心趋势、WaveMatrix 状态、艾略特波浪趋势、RSI，进行分析总结当前波动特征进行分析。
3. **Squeeze 与 Chopping 分析**：判断市场是否处于横盘挤压或震荡区间，并结合 PMA 与 ADX 状态，分析总结趋势强弱。
4. **买卖压力分析**：基于 CVD 的状态评估资金流向及买卖力量对比。给出分析总结

## 💡 投资建议
给出基于上述分析的交易建议，并结合趋势改变点，结合对比bullishrating和bearishrating的值，分析总结：
- 趋势改变止损点：{trend_stop}
- bullishrating：{bullish_rating} (看涨震荡评级: {bullish_osc} + 看涨趋势评级: {bullish_trend})
- bearishrating：{bearish_rating} (看跌震荡评级: {bearish_osc} + 看跌趋势评级: {bearish_trend})

## ⚠️ 风险提示
根据关键交易信号，结合趋势总结，提醒潜在风险因素。"""
        
        # 如果有交易数据，添加交易解读部分
        if trade_data:
            trade_section = self._build_trade_section(trade_data)
            base_prompt += f"\n{trade_section}"
        
        return base_prompt
    
    def _build_trade_section(self, trade_data):
        """构建交易解读部分"""
        try:
            action_desc = {
                'buy': '做多',
                'sell': '做空'
            }
            
            action_text = action_desc.get(trade_data.action, trade_data.action)
            
            section = f"""

## 📊TDindicator Bot 交易解读：
**交易方向：{action_text}**
- **止损：{trade_data.stop_loss_price or 'N/A'}**
- **止盈：{trade_data.take_profit_price or 'N/A'}**
结合风险等级{trade_data.risk_level or 'N/A'}、OscRating{trade_data.osc_rating or 'N/A'}与 TrendRating{trade_data.trend_rating or 'N/A'}；
说明：这是bot交易的最后一笔，结合总体趋势，对该交易用3-4句话做出简短的分析和评价。"""
            
            return section
            
        except Exception as e:
            self.logger.error(f"构建交易部分失败: {e}")
            return "\n## 📊TDindicator Bot 交易解读：\n交易数据解析失败"
    
    def _format_report(self, report_text: str, trading_data: TradingViewData) -> str:
        """按照Discord格式要求格式化报告输出"""
        try:
            # 获取美东时间
            eastern_date = self._get_eastern_date()
            
            # 从Markdown中提取并替换标题日期
            title = self._extract_and_update_title(report_text, eastern_date)
            
            # 解析Markdown成结构化对象
            sections = self._parse_markdown_sections(report_text)
            
            # 高亮关键价格
            for section_name in sections:
                sections[section_name] = self._highlight_prices(sections[section_name])
            
            # 构建Discord格式的最终报告
            discord_report = f"📊 **{title}**\n\n"
            
            # 按顺序添加各个部分
            section_order = [
                "市场概况", "关键信号分析", "趋势分析", "技术指标详解", 
                "风险评估", "交易建议", "投资建议", "风险提示"
            ]
            
            for section_name in section_order:
                if section_name in sections and sections[section_name].strip():
                    discord_report += f"**{section_name}**\n{sections[section_name]}\n\n"
            
            # 添加其他未列出的部分
            for section_name, content in sections.items():
                if section_name not in section_order and content.strip():
                    discord_report += f"**{section_name}**\n{content}\n\n"
            
            # 添加报告尾部
            discord_report += f"⏰ **时间框架:** {trading_data.timeframe}\n"
            discord_report += f"📅 **分析时间:** {eastern_date}\n"
            discord_report += "=" * 40
            
            return discord_report.strip()
            
        except Exception as e:
            self.logger.error(f"Discord格式化失败: {e}")
            return self._format_simple_report(report_text, trading_data)
    
    def _get_eastern_date(self) -> str:
        """获取美东时间日期"""
        try:
            import pytz
            # 获取美东时区
            eastern = pytz.timezone('America/New_York')
            # 转换为美东时间
            eastern_time = datetime.now(eastern)
            return eastern_time.strftime('%Y-%m-%d %H:%M (美国东部时间)')
        except:
            # 回退到UTC时间
            return datetime.now().strftime('%Y-%m-%d %H:%M (UTC时间)')
    
    def _extract_and_update_title(self, markdown_text: str, eastern_date: str) -> str:
        """提取标题并替换日期为当前美东时间"""
        match = re.search(r'^#\s+(.*)', markdown_text, re.MULTILINE)
        title = match.group(1).strip() if match else "交易分析报告"
        
        # 替换日期部分为当前美东时间
        title = re.sub(r'\(\d{4}年\d{1,2}月\d{1,2}日.*?\)', f'({eastern_date})', title)
        title = re.sub(r'\(\d{4}-\d{1,2}-\d{1,2}.*?\)', f'({eastern_date})', title)
        return title
    
    def _highlight_prices(self, text: str) -> str:
        """高亮关键价格信息"""
        # 高亮止损、止盈价格
        text = re.sub(r'(止损[^\d]*)(\d+(?:\.\d+)?)', r'🎯 **\1\2**', text)
        text = re.sub(r'(止盈[^\d]*)(\d+(?:\.\d+)?)', r'🎯 **\1\2**', text)
        text = re.sub(r'(趋势改变止损点[^\d]*)(\d+(?:\.\d+)?)', r'🎯 **\1\2**', text)
        return text
    
    def _parse_markdown_sections(self, markdown_text: str) -> Dict[str, str]:
        """解析Markdown成结构化对象"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = markdown_text.split('\n')
        
        for line in lines:
            # 检查二级标题 (##)
            section_match = re.match(r'^##\s+(.*)', line)
            # 检查三级标题 (###)
            sub_match = re.match(r'^###\s+(.*)', line)
            
            if section_match:
                # 保存上一个部分
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # 开始新部分
                current_section = section_match.group(1).strip()
                current_content = []
            elif sub_match and current_section:
                # 添加子标题
                current_content.append(f"\n**{sub_match.group(1)}**\n")
            elif current_section:
                # 添加内容行
                current_content.append(line)
        
        # 保存最后一个部分
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _format_simple_report(self, report_text: str, trading_data: TradingViewData) -> str:
        """简单格式化（备用方案）"""
        eastern_date = self._get_eastern_date()
        header = f"📊 **{trading_data.symbol} 技术分析报告**\n"
        header += f"⏰ 时间框架: {trading_data.timeframe}\n"
        header += f"📅 分析时间: {eastern_date}\n"
        header += "=" * 40 + "\n\n"
        
        return header + report_text.strip()
    
    def _generate_fallback_report(self, trading_data: TradingViewData, raw_data: Dict, signals_list: list = None) -> str:
        """生成备用报告（当AI生成失败时）"""
        
        # 如果没有提供signals_list，从raw_data中提取
        if signals_list is None:
            signals_list = self._extract_signals_from_data(raw_data)
        
        signals_text = '\n'.join([f"- {signal}" for signal in signals_list]) if signals_list else "- 暂无可用信号"
        
        eastern_date = self._get_eastern_date()
        fallback_report = f"""
📊 **{trading_data.symbol} 技术分析报告**
🕐 数据时间: {eastern_date}
⏱️ 时间框架: {trading_data.timeframe}

## 🔑 关键交易信号
{signals_text}

## 📉 基础数据摘要
- 数据接收时间: {eastern_date}
- 分析时间框架: {trading_data.timeframe}
- 数据来源: TradingView webhook

⚠️ **注意**: AI报告生成服务暂时不可用，以上为基础数据摘要。
⚠️ **免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""
        
        return fallback_report