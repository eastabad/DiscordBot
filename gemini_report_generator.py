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
        
        # 构建信号列表字符串
        signals_text = ','.join(signals_list) if signals_list else '暂无可用信号'
        
        # 使用正确的报告模板格式
        prompt = f"""
生成一份针对{trading_data.symbol}的中文交易报告，格式为 Markdown，包含以下部分：

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
        """从原始数据中提取解析的信号列表，使用正确的中文描述，基于实际TradingView数据结构"""
        signals = []
        
        # PMA信号 (基于pmaText字段)
        if 'pmaText' in raw_data:
            pma_text = str(raw_data['pmaText'])
            if 'Bullish' in pma_text:
                signals.append('PMA 看涨')
            elif 'Bearish' in pma_text:
                signals.append('PMA 看跌')
            else:
                signals.append(f'PMA {pma_text}')
        
        # CVD信号 (基于CVDsignal字段)
        if 'CVDsignal' in raw_data:
            cvd_signal = str(raw_data['CVDsignal'])
            if 'cvdAboveMA' in cvd_signal:
                signals.append('CVD 高于移动平均线 (买压增加，资金流入)')
            elif 'cvdBelowMA' in cvd_signal:
                signals.append('CVD 低于移动平均线 (卖压增加，资金流出)')
            else:
                signals.append(f'CVD {cvd_signal}')
        
        # RSI-HA信号 (基于RSIHAsignal字段)
        if 'RSIHAsignal' in raw_data:
            rsi_ha_signal = str(raw_data['RSIHAsignal'])
            if 'BullishHA' in rsi_ha_signal:
                signals.append('Heikin Ashi RSI 看涨')
            elif 'BearishHA' in rsi_ha_signal:
                signals.append('Heikin Ashi RSI 看跌')
            else:
                signals.append(f'Heikin Ashi RSI {rsi_ha_signal}')
        
        # BBP信号 (基于BBPsignal字段)
        if 'BBPsignal' in raw_data:
            bbp_signal = str(raw_data['BBPsignal']).strip()
            if 'bullpower' in bbp_signal:
                signals.append('多头主导控场')
            elif 'bearpower' in bbp_signal:
                signals.append('空头主导控场')
            else:
                signals.append('市场处于过渡状态')
        
        # Choppiness相关信号
        if 'SQZsignal' in raw_data:
            sqz_signal = str(raw_data['SQZsignal'])
            if 'no squeeze' in sqz_signal:
                signals.append('市场不在横盘挤压')
            else:
                signals.append('市场处于横盘挤压')
        
        if 'choppingrange_signal' in raw_data:
            chop_signal = str(raw_data['choppingrange_signal'])
            if 'no chopping' in chop_signal:
                signals.append('市场处于非震荡区间')
            else:
                signals.append('市场处于震荡区间')
        
        # ADX信号 (基于adxValue字段)
        if 'adxValue' in raw_data:
            try:
                adx_value = float(raw_data['adxValue'])
                if adx_value > 25:
                    signals.append('ADX 强趋势')
                else:
                    signals.append('ADX 弱趋势')
            except:
                signals.append(f'ADX {raw_data["adxValue"]}')
        
        # RSI状态趋势
        if 'rsi_state_trend' in raw_data:
            rsi_trend = str(raw_data['rsi_state_trend'])
            if 'Bullish' in rsi_trend:
                signals.append('RSI 看涨')
            elif 'Bearish' in rsi_trend:
                signals.append('RSI 看跌')
            else:
                signals.append('RSI 中性')
        
        # MA趋势信号 (基于不同时间框架)
        timeframe = raw_data.get('timeframe', '15m')
        if 'MAtrend' in raw_data:
            ma_trend = str(raw_data['MAtrend'])
            if ma_trend == '1':
                signals.append(f'{timeframe} 分钟当前趋势: 上涨')
            elif ma_trend == '-1':
                signals.append(f'{timeframe} 分钟当前趋势: 下跌')
            else:
                signals.append(f'{timeframe} 分钟当前趋势: 横盘')
        
        # 多时间框架MA趋势
        if 'adaptive_timeframe_1' in raw_data and 'MAtrend_timeframe1' in raw_data:
            tf1 = raw_data['adaptive_timeframe_1']
            ma1 = str(raw_data['MAtrend_timeframe1'])
            if ma1 == '1':
                signals.append(f'{tf1} 分钟 MA 趋势: 上涨')
            elif ma1 == '-1':
                signals.append(f'{tf1} 分钟 MA 趋势: 下跌')
        
        if 'adaptive_timeframe_2' in raw_data and 'MAtrend_timeframe2' in raw_data:
            tf2 = raw_data['adaptive_timeframe_2']
            ma2 = str(raw_data['MAtrend_timeframe2'])
            if ma2 == '1':
                signals.append(f'{tf2} 分钟 MA 趋势: 上涨')
            elif ma2 == '-1':
                signals.append(f'{tf2} 分钟 MA 趋势: 下跌')
        
        # 平滑趋势 (基于Middle_smooth_trend字段)
        if 'Middle_smooth_trend' in raw_data:
            smooth_trend = str(raw_data['Middle_smooth_trend'])
            if 'Bullish' in smooth_trend:
                signals.append('平滑趋势: 强烈看涨')
            elif 'Bearish' in smooth_trend:
                signals.append('平滑趋势: 强烈看跌')
        
        # 动量指标 (基于MOMOsignal字段)
        if 'MOMOsignal' in raw_data:
            momo_signal = str(raw_data['MOMOsignal'])
            if 'bullish' in momo_signal.lower():
                signals.append('动量指标: 看涨')
            elif 'bearish' in momo_signal.lower():
                signals.append('动量指标: 看跌')
        
        # TrendTracer信号
        if 'TrendTracersignal' in raw_data:
            tt_signal = str(raw_data['TrendTracersignal'])
            timeframe = raw_data.get('timeframe', '15m')
            if tt_signal == '1':
                signals.append(f'{timeframe} 分钟 TrendTracer 趋势: 绿色上涨趋势')
            elif tt_signal == '-1':
                signals.append(f'{timeframe} 分钟 TrendTracer 趋势: 粉色下跌趋势')
        
        if 'TrendTracerHTF' in raw_data and 'adaptive_timeframe_2' in raw_data:
            tt_htf = str(raw_data['TrendTracerHTF'])
            tf2 = raw_data['adaptive_timeframe_2']
            if tt_htf == '1':
                signals.append(f'{tf2} 分钟 TrendTracer 趋势: 绿色上涨趋势')
            elif tt_htf == '-1':
                signals.append(f'{tf2} 分钟 TrendTracer 趋势: 粉色下跌趋势')
        
        # 趋势改变止损点
        if 'trend_change_volatility_stop' in raw_data:
            trend_stop = raw_data['trend_change_volatility_stop']
            signals.append(f'趋势改变止损点: {trend_stop}')
        
        # AI智能趋势带 (基于AIbandsignal字段)
        if 'AIbandsignal' in raw_data:
            ai_signal = str(raw_data['AIbandsignal'])
            if 'green' in ai_signal.lower() or 'uptrend' in ai_signal.lower():
                signals.append('AI 智能趋势带: 上升趋势')
            elif 'red' in ai_signal.lower() or 'downtrend' in ai_signal.lower():
                signals.append('AI 智能趋势带: 下降趋势')
        
        # 中心趋势 (基于center_trend字段)
        if 'center_trend' in raw_data:
            center_trend = str(raw_data['center_trend'])
            if 'Strong Bullish' in center_trend:
                signals.append('中心趋势强烈看涨')
            elif 'Strong Bearish' in center_trend:
                signals.append('中心趋势强烈看跌')
            elif 'Bullish' in center_trend:
                signals.append('中心趋势看涨')
            elif 'Bearish' in center_trend:
                signals.append('中心趋势看跌')
        
        # WaveMatrix状态 (基于wavemarket_state字段)
        if 'wavemarket_state' in raw_data:
            wave_state = str(raw_data['wavemarket_state'])
            if 'Long Strong' in wave_state:
                signals.append('WaveMatrix 状态: 强烈上涨趋势')
            elif 'Short Strong' in wave_state:
                signals.append('WaveMatrix 状态: 强烈下跌趋势')
            elif 'Long' in wave_state:
                signals.append('WaveMatrix 状态: 上涨趋势')
            elif 'Short' in wave_state:
                signals.append('WaveMatrix 状态: 下跌趋势')
        
        # 艾略特波浪趋势 (基于ewotrend_state字段)
        if 'ewotrend_state' in raw_data:
            ewo_trend = str(raw_data['ewotrend_state'])
            if 'Strong Bullish' in ewo_trend:
                signals.append('艾略特波浪趋势: 强烈上涨趋势')
            elif 'Strong Bearish' in ewo_trend:
                signals.append('艾略特波浪趋势: 强烈下跌趋势')
            elif 'Bullish' in ewo_trend:
                signals.append('艾略特波浪趋势: 上涨趋势')
            elif 'Bearish' in ewo_trend:
                signals.append('艾略特波浪趋势: 下跌趋势')
        
        # 高时间框架波浪信号 (基于HTFwave_signal字段)
        if 'HTFwave_signal' in raw_data:
            htf_wave = str(raw_data['HTFwave_signal'])
            if 'Bullish' in htf_wave:
                signals.append('高时间框架波浪信号: 看涨')
            elif 'Bearish' in htf_wave:
                signals.append('高时间框架波浪信号: 看跌')
        
        # 根据ADX值判断趋势强度描述
        if 'adxValue' in raw_data:
            try:
                adx_value = float(raw_data['adxValue'])
                if adx_value > 30:
                    signals.append('趋势主导，方向性强，波动相对平稳')
            except:
                pass
        
        # 添加止损止盈信息
        if 'stopLoss' in raw_data and raw_data['stopLoss']:
            stop_price = raw_data['stopLoss'].get('stopPrice', '')
            if stop_price:
                signals.append(f'止损价格: {stop_price}')
        
        if 'takeProfit' in raw_data and raw_data['takeProfit']:
            take_price = raw_data['takeProfit'].get('limitPrice', '')
            if take_price:
                signals.append(f'止盈价格: {take_price}')
        
        if 'risk' in raw_data:
            risk = raw_data['risk']
            signals.append(f'风险等级: {risk}')
        
        # extras信息
        if 'extras' in raw_data and raw_data['extras']:
            extras = raw_data['extras']
            if 'oscrating' in extras:
                signals.append(f'震荡指标评级: {extras["oscrating"]}')
            if 'trendrating' in extras:
                signals.append(f'趋势指标评级: {extras["trendrating"]}')
        
        # 如果有交易建议
        if 'tradingAdvice' in raw_data:
            advice = raw_data['tradingAdvice']
            signals.append(f'交易建议: {advice}')
        
        return signals
    
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
            return eastern_time.strftime('%Y年%m月%d日 (美东时间)')
        except:
            # 回退到UTC时间
            return datetime.now().strftime('%Y年%m月%d日 (UTC时间)')
    
    def _extract_and_update_title(self, markdown_text: str, eastern_date: str) -> str:
        """提取标题并替换日期为当前美东时间"""
        match = re.search(r'^#\s+(.*)', markdown_text, re.MULTILINE)
        title = match.group(1).strip() if match else "交易分析报告"
        
        # 替换日期部分为当前美东时间
        title = re.sub(r'\(\d{4}年\d{1,2}月\d{1,2}日.*?\)', f'({eastern_date})', title)
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
        header = f"📊 **{trading_data.symbol} 技术分析报告**\n"
        header += f"⏰ 时间框架: {trading_data.timeframe}\n"
        header += f"📅 分析时间: {trading_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "=" * 40 + "\n\n"
        
        return header + report_text.strip()
    
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