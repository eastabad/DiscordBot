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