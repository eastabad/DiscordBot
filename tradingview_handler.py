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
            
            # 提取技术指标数据
            parsed_data = {
                'symbol': symbol.upper(),
                'timeframe': primary_timeframe,
                'timestamp': datetime.now(),
                
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