"""
TradingView数据处理器
用于接收、解析和存储TradingView推送的数据
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models import TradingViewData, get_db_session

class TradingViewHandler:
    """TradingView数据处理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_webhook_data(self, webhook_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析webhook数据，提取TradingView信息"""
        try:
            # 从webhook数组中提取第一个元素
            if isinstance(webhook_payload, list) and len(webhook_payload) > 0:
                data = webhook_payload[0]
            else:
                data = webhook_payload
            
            # 提取body中的TradingView数据
            body = data.get('body', {})
            if not body:
                self.logger.warning("Webhook数据中没有找到body字段")
                return None
            
            # 获取股票代码
            symbol = body.get('symbol')
            if not symbol:
                self.logger.warning("TradingView数据中没有找到symbol字段")
                return None
            
            # 解析时间框架 - 从adaptive_timeframe字段获取
            timeframe_1 = body.get('adaptive_timeframe_1', '15')  # 默认15分钟
            timeframe_2 = body.get('adaptive_timeframe_2', '60')  # 默认1小时
            
            # 根据数据内容判断主要时间框架，转换为标准格式
            tf1_int = int(timeframe_1) if timeframe_1 else 15
            if tf1_int == 15:
                primary_timeframe = "15m"
            elif tf1_int == 60:
                primary_timeframe = "1h"  # 1小时用1h表示
            elif tf1_int == 240:
                primary_timeframe = "4h"  # 4小时用4h表示
            else:
                primary_timeframe = f"{tf1_int}m"  # 其他情况用分钟
            
            # 解析详细的交易信号
            signals = self._parse_detailed_signals(body, timeframe_1, timeframe_2, primary_timeframe)
            
            # 提取技术指标数据
            parsed_data = {
                'symbol': symbol.upper(),
                'timeframe': primary_timeframe,
                'timestamp': datetime.now(),
                'signals': signals,  # 新增详细信号解析
                
                # 技术指标
                'cvd_signal': body.get('CVDsignal', ''),
                'choppiness': self._safe_float(body.get('choppiness')),
                'adx_value': self._safe_float(body.get('adxValue')),
                'bbp_signal': body.get('BBPsignal', ''),
                'rsi_ha_signal': body.get('RSIHAsignal', ''),
                'sqz_signal': body.get('SQZsignal', ''),
                'chopping_range_signal': body.get('choppingrange_signal', ''),
                'rsi_state_trend': body.get('rsi_state_trend', ''),
                'center_trend': body.get('center_trend', ''),
                'ma_trend': self._safe_float(body.get('MAtrend')),
                'ma_trend_tf1': self._safe_float(body.get('MAtrend_timeframe1')),
                'ma_trend_tf2': self._safe_float(body.get('MAtrend_timeframe2')),
                'momo_signal': body.get('MOMOsignal', ''),
                'middle_smooth_trend': body.get('Middle_smooth_trend', ''),
                'trend_tracer_signal': self._safe_float(body.get('TrendTracersignal')),
                'trend_tracer_htf': self._safe_float(body.get('TrendTracerHTF')),
                'pma_text': body.get('pmaText', ''),
                'trend_change_volatility_stop': self._safe_float(body.get('trend_change_volatility_stop')),
                'ai_band_signal': body.get('AIbandsignal', ''),
                'htf_wave_signal': body.get('HTFwave_signal', ''),
                'wave_market_state': body.get('wavemarket_state', ''),
                'ewo_trend_state': body.get('ewotrend_state', ''),
                
                # 止损止盈相关
                'stop_loss': body.get('stopLoss', {}),
                'take_profit': body.get('takeProfit', {}),
                'risk': body.get('risk', ''),
                'action': body.get('action', ''),
                
                # 额外评级信息
                'extras': body.get('extras', {}),
                
                # 原始数据
                'raw_data': json.dumps(body, ensure_ascii=False)
            }
            
            self.logger.info(f"成功解析TradingView数据: {symbol} ({primary_timeframe})")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"解析TradingView数据失败: {e}")
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_str(self, value: Any) -> str:
        """安全转换为字符串"""
        if value is None:
            return ''
        return str(value)
    
    def _parse_detailed_signals(self, data: Dict[str, Any], timeframe_1: str, timeframe_2: str, current_timeframe: str) -> list:
        """解析详细的交易信号"""
        signals = []
        
        # 安全获取数值
        choppiness = self._safe_float(data.get('choppiness'))
        adxValue = self._safe_float(data.get('adxValue'))
        MAtrend = self._safe_float(data.get('MAtrend'))
        MAtrend1 = self._safe_float(data.get('MAtrend_timeframe1'))
        MAtrend2 = self._safe_float(data.get('MAtrend_timeframe2'))
        TrendTracersignal = self._safe_float(data.get('TrendTracersignal'))
        TrendTracerHTF = self._safe_float(data.get('TrendTracerHTF'))
        trendStop = self._safe_float(data.get('trend_change_volatility_stop'))
        oscrating = self._safe_float(data.get('extras', {}).get('oscrating'))
        trendrating = self._safe_float(data.get('extras', {}).get('trendrating'))
        
        # PMA 信号
        pma_text = self._safe_str(data.get('pmaText'))
        pma_mapping = {
            'PMA Strong Bullish': 'PMA 强烈看涨',
            'PMA Bullish': 'PMA 看涨',
            'PMA Trendless': 'PMA 无明确趋势',
            'PMA Strong Bearish': 'PMA 强烈看跌',
            'PMA Bearish': 'PMA 看跌'
        }
        signals.append(pma_mapping.get(pma_text, 'PMA 状态未知'))
        
        # CVD 信号
        cvd_signal = self._safe_str(data.get('CVDsignal'))
        cvd_mapping = {
            'cvdAboveMA': 'CVD 高于移动平均线 (买压增加，资金流入)',
            'cvdBelowMA': 'CVD 低于移动平均线 (卖压增加，资金流出)'
        }
        signals.append(cvd_mapping.get(cvd_signal, 'CVD 状态未知'))
        
        # RSIHAsignal 信号
        rsi_ha_signal = self._safe_str(data.get('RSIHAsignal'))
        rsi_ha_mapping = {
            'BullishHA': 'Heikin Ashi RSI 看涨',
            'BearishHA': 'Heikin Ashi RSI 看跌'
        }
        signals.append(rsi_ha_mapping.get(rsi_ha_signal, 'Heikin Ashi RSI 状态未知'))
        
        # BBPsignal 信号
        bbp_signal = self._safe_str(data.get('BBPsignal'))
        bbp_mapping = {
            'bullpower': '多头主导控场',
            'bearpower': '空头主导控场'
        }
        signals.append(bbp_mapping.get(bbp_signal, '市场控场状态未知'))
        
        # Choppiness 信号
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
        if adxValue is not None:
            if adxValue < 20:
                signals.append('ADX 无趋势或弱趋势')
            elif adxValue < 25:
                signals.append('ADX 趋势开始形成')
            elif adxValue < 50:
                signals.append('ADX 强趋势')
            elif adxValue < 75:
                signals.append('ADX 非常强趋势')
            else:
                signals.append('ADX 极强趋势')
        else:
            signals.append('ADX: 数据无效')
        
        # RSI 信号
        rsi_state = self._safe_str(data.get('rsi_state_trend'))
        rsi_mapping = {
            'Bullish': 'RSI 看涨',
            'Bearish': 'RSI 看跌',
            'Neutral': 'RSI 中性'
        }
        signals.append(rsi_mapping.get(rsi_state, 'RSI 趋势: 状态未知'))
        
        # MA趋势信号
        ma_trend_mapping = {
            1: '上涨',
            0: '短线回调但未跌破 200 周期均线，观望',
            -1: '下跌'
        }
        
        # 当前时间框架MA趋势
        if MAtrend is not None:
            trend_desc = ma_trend_mapping.get(int(MAtrend), '状态未知')
            signals.append(f"{current_timeframe} 当前MA趋势: {trend_desc}")
        
        # 15分钟MA趋势
        if MAtrend1 is not None:
            trend_desc = ma_trend_mapping.get(int(MAtrend1), '状态未知')
            signals.append(f"{timeframe_1} 分钟 MA 趋势: {trend_desc}")
        
        # 1小时MA趋势
        if MAtrend2 is not None:
            trend_desc = ma_trend_mapping.get(int(MAtrend2), '状态未知')
            signals.append(f"{timeframe_2} 分钟 MA 趋势: {trend_desc}")
        
        # Middle Smooth Trend 信号
        smooth_trend = self._safe_str(data.get('Middle_smooth_trend'))
        smooth_mapping = {
            'Bullish +': '平滑趋势: 强烈看涨',
            'Bullish': '平滑趋势: 看涨',
            'Bearish +': '平滑趋势: 强烈看跌',
            'Bearish': '平滑趋势: 看跌'
        }
        signals.append(smooth_mapping.get(smooth_trend, '平滑趋势: 状态未知'))
        
        # MOMO信号
        momo_signal = self._safe_str(data.get('MOMOsignal'))
        momo_mapping = {
            'bullishmomo': '动量指标: 看涨',
            'bearishmomo': '动量指标: 看跌'
        }
        signals.append(momo_mapping.get(momo_signal, '动量指标: 状态未知'))
        
        # TrendTracer信号
        if TrendTracersignal is not None:
            if int(TrendTracersignal) == 1:
                signals.append(f"{current_timeframe} TrendTracer 趋势: 蓝色上涨趋势")
            elif int(TrendTracersignal) == -1:
                signals.append(f"{current_timeframe} TrendTracer 趋势: 粉色下跌趋势")
            else:
                signals.append(f"{current_timeframe} TrendTracer 趋势: 状态未知")
        
        if TrendTracerHTF is not None:
            if int(TrendTracerHTF) == 1:
                signals.append(f"{timeframe_2} 分钟 TrendTracer 趋势: 蓝色上涨趋势")
            elif int(TrendTracerHTF) == -1:
                signals.append(f"{timeframe_2} 分钟 TrendTracer 趋势: 粉色下跌趋势")
            else:
                signals.append(f"{timeframe_2} 分钟 TrendTracer 趋势: 状态未知")
        
        # 趋势改变止损点
        signals.append(f"趋势改变止损点: {trendStop if trendStop is not None else '未知'}")
        
        # AI智能趋势带信号
        ai_band = self._safe_str(data.get('AIbandsignal'))
        ai_mapping = {
            'green uptrend': 'AI 智能趋势带: 上升趋势',
            'red downtrend': 'AI 智能趋势带: 下降趋势'
        }
        signals.append(ai_mapping.get(ai_band, 'AI 智能趋势带: 状态未知'))
        
        # Squeeze Momentum 信号
        sqz_signal = self._safe_str(data.get('SQZsignal'))
        sqz_mapping = {
            'squeeze': '市场处于横盘挤压',
            'no squeeze': '市场不在横盘挤压'
        }
        signals.append(sqz_mapping.get(sqz_signal, 'Squeeze Momentum: 状态未知'))
        
        # Chopping Range 信号
        chopping_signal = self._safe_str(data.get('choppingrange_signal'))
        chopping_mapping = {
            'chopping': '市场处于震荡区间',
            'no chopping': '市场处于非震荡区间'
        }
        signals.append(chopping_mapping.get(chopping_signal, 'Chopping Range: 状态未知'))
        
        # Center Trend 信号
        center_trend = self._safe_str(data.get('center_trend'))
        center_mapping = {
            'Strong Bullish': '中心趋势强烈看涨',
            'Weak Bullish': '中心趋势弱看涨',
            'Weak Bearish': '中心趋势弱看跌',
            'Strong Bearish': '中心趋势强烈看跌'
        }
        signals.append(center_mapping.get(center_trend, '中心趋势: 状态未知'))
        
        # WaveMatrix 状态信号
        wave_state = self._safe_str(data.get('wavemarket_state'))
        wave_mapping = {
            'Long Strong': 'WaveMatrix 状态: 强烈上涨趋势',
            'Long Weak': 'WaveMatrix 状态: 弱上涨趋势',
            'Short Strong': 'WaveMatrix 状态: 强烈下跌趋势',
            'Short Weak': 'WaveMatrix 状态: 弱下跌趋势',
            'Neutral': 'WaveMatrix 状态: 中性'
        }
        signals.append(wave_mapping.get(wave_state, 'WaveMatrix 状态: 状态未知'))
        
        # Elliott Wave Trend 信号
        ewo_trend = self._safe_str(data.get('ewotrend_state'))
        ewo_mapping = {
            'Strong Bullish': '艾略特波浪趋势: 强烈上涨趋势',
            'Weak Bullish': '艾略特波浪趋势: 弱上涨趋势',
            'Weak Bearish': '艾略特波浪趋势: 弱下跌趋势',
            'Strong Bearish': '艾略特波浪趋势: 强烈下跌趋势'
        }
        signals.append(ewo_mapping.get(ewo_trend, '艾略特波浪趋势: 状态未知'))
        
        # HTFwave_signal 信号
        htf_wave = self._safe_str(data.get('HTFwave_signal'))
        htf_mapping = {
            'Bullish': '高时间框架波浪信号: 看涨',
            'Bearish': '高时间框架波浪信号: 看跌',
            'Neutral': '高时间框架波浪信号: 中性'
        }
        signals.append(htf_mapping.get(htf_wave, '高时间框架波浪信号: 状态未知'))
        
        # OscRating 和 TrendRating 比较
        if oscrating is not None and trendrating is not None:
            if oscrating > trendrating:
                signals.append('趋势初期，结构不稳，波动幅度较高')
            elif oscrating < trendrating:
                signals.append('趋势主导，方向性强，波动相对平稳')
            else:
                signals.append('趋势状态平衡，波动适中')
        else:
            signals.append('趋势评级状态: 未知')
        
        # 止损和止盈信号
        stop_loss = data.get('stopLoss', {})
        if stop_loss and isinstance(stop_loss.get('stopPrice'), (int, float)):
            signals.append(f"止损价格: {stop_loss['stopPrice']}")
        
        take_profit = data.get('takeProfit', {})
        if take_profit and isinstance(take_profit.get('limitPrice'), (int, float)):
            signals.append(f"止盈价格: {take_profit['limitPrice']}")
        
        risk = data.get('risk')
        if risk:
            signals.append(f"风险等级: {risk}")
        
        return signals
    
    def store_enhanced_data(self, raw_payload: Dict) -> bool:
        """存储增强版TradingView数据到数据库 - 支持三种数据类型"""
        try:
            session = get_db_session()
            
            # 自动检测数据类型
            data_type = self._detect_data_type(raw_payload)
            
            # 提取基本信息
            symbol, timeframe = self._extract_basic_info(raw_payload, data_type)
            
            if not symbol:
                self.logger.warning("无法提取symbol信息")
                return False
            
            # 创建新的数据记录
            tv_data = TradingViewData(
                symbol=symbol.upper(),
                timeframe=timeframe,
                data_type=data_type,
                raw_data=json.dumps(raw_payload, ensure_ascii=False),
                received_at=datetime.now()
            )
            
            # 根据数据类型提取相关字段
            if data_type == 'trade':
                self._extract_trade_fields(tv_data, raw_payload)
            elif data_type == 'close':
                self._extract_close_fields(tv_data, raw_payload)
            # signal类型只需要基本字段
            
            session.add(tv_data)
            session.commit()
            session.close()
            
            self.logger.info(f"✅ 成功存储TradingView数据: {data_type}:{symbol}-{timeframe}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 存储TradingView数据失败: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    def _detect_data_type(self, data: Dict) -> str:
        """自动检测数据类型"""
        # 检查是否是平仓数据 (有sentiment: flat)
        if 'sentiment' in data and data.get('sentiment') == 'flat':
            return 'close'
        
        # 检查是否包含完整的交易信息 (有takeProfit和stopLoss)
        if 'takeProfit' in data and 'stopLoss' in data and 'action' in data:
            return 'trade'
        
        # 检查是否是顶层包含ticker和action字段的交易数据
        if 'ticker' in data and 'action' in data and 'takeProfit' in data:
            return 'trade'
        
        # 默认为信号数据
        return 'signal'
    
    def _extract_basic_info(self, data: Dict, data_type: str) -> tuple:
        """提取基本的symbol和timeframe信息"""
        symbol = None
        timeframe = "15m"  # 默认值
        
        if data_type == 'signal':
            # 信号数据直接包含symbol
            symbol = data.get('symbol')
            # 从adaptive_timeframe获取时间框架
            tf1 = data.get('adaptive_timeframe_1', '15')
            timeframe = f"{tf1}m" if tf1 != '60' else "1h"
            
        elif data_type in ['trade', 'close']:
            # 交易/平仓数据包含ticker
            symbol = data.get('ticker')
            # 从extras获取时间框架
            extras = data.get('extras', {})
            tf = extras.get('timeframe', '15m')
            timeframe = tf
        
        return symbol, timeframe
    
    def _extract_trade_fields(self, tv_data, data: Dict):
        """提取交易类型数据的字段"""
        tv_data.action = data.get('action')
        tv_data.quantity = data.get('quantity')
        
        # 提取止盈止损
        if 'takeProfit' in data and isinstance(data['takeProfit'], dict):
            tv_data.take_profit_price = data['takeProfit'].get('limitPrice')
        
        if 'stopLoss' in data and isinstance(data['stopLoss'], dict):
            tv_data.stop_loss_price = data['stopLoss'].get('stopPrice')
        
        # 提取extras信息
        if 'extras' in data and isinstance(data['extras'], dict):
            extras = data['extras']
            tv_data.osc_rating = extras.get('oscrating')
            tv_data.trend_rating = extras.get('trendrating')
            tv_data.risk_level = extras.get('risk')
            tv_data.trigger_indicator = extras.get('indicator')
            tv_data.trigger_timeframe = extras.get('timeframe')
    
    def _extract_close_fields(self, tv_data, data: Dict):
        """提取平仓类型数据的字段"""
        tv_data.action = data.get('action')  # 'buy' 或 'sell'
        tv_data.quantity = data.get('quantity')
        
        # 提取extras信息
        if 'extras' in data and isinstance(data['extras'], dict):
            extras = data['extras']
            tv_data.trigger_indicator = extras.get('indicator')
            tv_data.trigger_timeframe = extras.get('timeframe')
        
        # 平仓通常不需要止盈止损信息
    
    def save_to_database(self, parsed_data: Dict[str, Any]) -> bool:
        """保存数据到数据库"""
        db = None
        try:
            db = get_db_session()
            
            # 创建新的TradingView数据记录
            tv_data = TradingViewData(
                symbol=parsed_data['symbol'],
                timeframe=parsed_data['timeframe'],
                timestamp=parsed_data['timestamp'],
                
                # 技术指标数据存储在raw_data的JSON中
                # 这里可以根据需要提取特定字段到专门的列
                rsi=None,  # 需要时可以从raw_data中解析
                macd=None,
                sma_20=None,
                sma_50=None,
                
                raw_data=parsed_data['raw_data']
            )
            
            db.add(tv_data)
            db.commit()
            
            self.logger.info(f"成功保存TradingView数据到数据库: {parsed_data['symbol']} ({parsed_data['timeframe']})")
            return True
            
        except Exception as e:
            self.logger.error(f"保存TradingView数据到数据库失败: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    def get_latest_data(self, symbol: str, timeframe: str) -> Optional[TradingViewData]:
        """获取指定股票和时间框架的最新数据"""
        db = None
        try:
            db = get_db_session()
            
            # 查询最新的数据记录
            latest_data = db.query(TradingViewData).filter(
                TradingViewData.symbol == symbol.upper(),
                TradingViewData.timeframe == timeframe
            ).order_by(TradingViewData.timestamp.desc()).first()
            
            return latest_data
            
        except Exception as e:
            self.logger.error(f"查询最新TradingView数据失败: {e}")
            return None
        finally:
            if db:
                db.close()
    
    def process_webhook(self, webhook_payload: Dict[str, Any]) -> bool:
        """处理完整的webhook流程：解析 + 保存"""
        parsed_data = self.parse_webhook_data(webhook_payload)
        if not parsed_data:
            return False
        
        return self.save_to_database(parsed_data)