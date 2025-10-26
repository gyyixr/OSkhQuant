# coding: utf-8
"""
A股市场适配器
封装现有miniQMT功能为标准化适配器接口
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date, timedelta
import pandas as pd
import holidays

from .base_adapter import BaseMarketAdapter
from .market_registry import register_adapter
from .data_normalizer import DataNormalizer


@register_adapter('china_a_stock')
class ChinaAStockAdapter(BaseMarketAdapter):
    """
    A股市场适配器
    基于miniQMT提供数据和交易接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化A股适配器
        
        Args:
            config: 配置字典,包含:
                - userdata_path: miniQMT用户数据路径
                - client_path: miniQMT客户端路径(可选)
        """
        super().__init__(config)
        self.market_type = 'china_a_stock'
        self.market_name = 'A股市场'
        
        # miniQMT相关配置
        self.userdata_path = config.get('userdata_path', '')
        self.client_path = config.get('client_path', '')
        
        # 延迟加载xtquant,避免在配置阶段就需要miniQMT
        self.xtdata = None
        self.xttrader = None
        
        # 中国节假日
        self.cn_holidays = holidays.China()
        
        # A股交易时间段
        self.trading_hours = [
            ("09:30:00", "11:30:00"),  # 上午
            ("13:00:00", "15:00:00")   # 下午
        ]
    
    # ==================== 基础接口 ====================
    
    def connect(self) -> bool:
        """连接到miniQMT"""
        try:
            # 导入xtquant模块
            from xtquant import xtdata
            self.xtdata = xtdata
            
            # 如果配置了userdata_path,连接到miniQMT
            if self.userdata_path:
                # 这里可以添加miniQMT的连接逻辑
                pass
            
            self.connected = True
            print(f"✓ {self.market_name} 适配器已连接")
            return True
            
        except ImportError as e:
            print(f"✗ 无法导入xtquant模块: {e}")
            print("  请确保已安装miniQMT")
            return False
        except Exception as e:
            print(f"✗ 连接{self.market_name}失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        print(f"✓ {self.market_name} 适配器已断开")
        return True
    
    def get_market_info(self) -> Dict[str, Any]:
        """获取市场基本信息"""
        return {
            'market_type': self.market_type,
            'market_name': self.market_name,
            'trading_hours': self.trading_hours,
            'timezone': 'Asia/Shanghai',
            'currency': 'CNY',
            'tick_size': 0.01,
            'lot_size': 100,  # A股最小交易单位为100股(1手)
            'price_limit': 0.10,  # 涨跌停限制10%
            't_plus': 1  # T+1交易
        }
    
    # ==================== 数据接口 ====================
    
    def get_symbols(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取标的列表
        
        Args:
            category: 分类(stock/etf/index等)
            
        Returns:
            list[dict]: 标的信息列表
        """
        if not self.connected or self.xtdata is None:
            print("✗ 未连接到数据源")
            return []
        
        try:
            # 使用miniQMT获取股票列表
            # 这里需要根据实际的miniQMT API调整
            symbols = []
            
            # 示例:获取所有股票
            # stock_list = self.xtdata.get_stock_list_in_sector('沪深A股')
            # for stock_code in stock_list:
            #     symbols.append({
            #         'symbol': DataNormalizer.normalize_symbol(stock_code, 'china_a_stock'),
            #         'name': '',  # 可以通过xtdata.get_instrument_detail获取
            #         'category': 'stock',
            #         'exchange': 'SH' if stock_code.endswith('.SH') else 'SZ'
            #     })
            
            return symbols
            
        except Exception as e:
            print(f"✗ 获取标的列表失败: {e}")
            return []
    
    def get_market_data(
        self,
        symbols: List[str],
        period: str,
        start: str,
        end: str,
        fields: Optional[List[str]] = None,
        dividend_type: str = 'none'
    ) -> pd.DataFrame:
        """
        获取历史行情数据
        
        Args:
            symbols: 标的代码列表(标准化格式 CN.XXXXXX.SH/SZ)
            period: 周期
            start: 开始时间
            end: 结束时间
            fields: 数据字段
            dividend_type: 复权方式
            
        Returns:
            DataFrame: 标准化的行情数据
        """
        if not self.connected or self.xtdata is None:
            print("✗ 未连接到数据源")
            return pd.DataFrame()
        
        try:
            # 反标准化symbol(去除CN.前缀)
            original_symbols = [DataNormalizer.denormalize_symbol(s) for s in symbols]
            
            # 调用miniQMT获取数据
            # data = self.xtdata.get_market_data(
            #     stock_list=original_symbols,
            #     period=period,
            #     start_time=start,
            #     end_time=end,
            #     dividend_type=dividend_type
            # )
            
            # 标准化数据字段
            # normalized_data = self._normalize_market_data(data)
            
            # 暂时返回空DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            print(f"✗ 获取行情数据失败: {e}")
            return pd.DataFrame()
    
    def download_history_data(
        self,
        symbols: List[str],
        period: str,
        start: str,
        end: str
    ) -> bool:
        """下载历史数据到本地"""
        if not self.connected or self.xtdata is None:
            print("✗ 未连接到数据源")
            return False
        
        try:
            # 反标准化symbol
            original_symbols = [DataNormalizer.denormalize_symbol(s) for s in symbols]
            
            # 调用miniQMT下载数据
            # self.xtdata.download_history_data(
            #     stock_list=original_symbols,
            #     period=period,
            #     start_time=start,
            #     end_time=end
            # )
            
            return True
            
        except Exception as e:
            print(f"✗ 下载历史数据失败: {e}")
            return False
    
    def subscribe_quote(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> bool:
        """订阅实时行情"""
        if not self.connected or self.xtdata is None:
            print("✗ 未连接到数据源")
            return False
        
        try:
            # 反标准化symbol
            original_symbols = [DataNormalizer.denormalize_symbol(s) for s in symbols]
            
            # 调用miniQMT订阅行情
            # self.xtdata.subscribe_quote(
            #     stock_code=original_symbols,
            #     period='tick',
            #     callback=callback
            # )
            
            return True
            
        except Exception as e:
            print(f"✗ 订阅行情失败: {e}")
            return False
    
    def unsubscribe_quote(self, symbols: List[str]) -> bool:
        """取消行情订阅"""
        if not self.connected or self.xtdata is None:
            return False
        
        try:
            # 反标准化symbol
            original_symbols = [DataNormalizer.denormalize_symbol(s) for s in symbols]
            
            # 调用miniQMT取消订阅
            # self.xtdata.unsubscribe_quote(stock_code=original_symbols)
            
            return True
            
        except Exception as e:
            print(f"✗ 取消订阅失败: {e}")
            return False
    
    # ==================== 交易接口 ====================
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        # 这里需要集成miniQMT的交易接口
        return {
            'account_id': '',
            'balance': 0.0,
            'available_cash': 0.0,
            'market_value': 0.0,
            'currency': 'CNY'
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        return []
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = 'limit'
    ) -> Dict[str, Any]:
        """下单"""
        return {}
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        return False
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        return {}
    
    def get_trade_history(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取成交记录"""
        return []
    
    # ==================== 市场特有接口 ====================
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化标的代码
        
        Args:
            symbol: 原始代码,如 000001.SZ, 600000.SH
            
        Returns:
            str: 标准化代码,如 CN.000001.SZ, CN.600000.SH
        """
        return DataNormalizer.normalize_symbol(symbol, self.market_type)
    
    def get_trading_calendar(self, start: str, end: str) -> List[date]:
        """
        获取交易日历
        
        Args:
            start: 开始日期,格式YYYYMMDD
            end: 结束日期,格式YYYYMMDD
            
        Returns:
            list[date]: 交易日列表
        """
        try:
            # 解析日期
            start_date = datetime.strptime(start, "%Y%m%d").date()
            end_date = datetime.strptime(end, "%Y%m%d").date()
            
            trading_days = []
            current_date = start_date
            
            while current_date <= end_date:
                # 排除周末
                if current_date.weekday() < 5:
                    # 排除法定节假日
                    if current_date not in self.cn_holidays:
                        trading_days.append(current_date)
                
                current_date += timedelta(days=1)
            
            return trading_days
            
        except Exception as e:
            print(f"✗ 获取交易日历失败: {e}")
            return []
    
    def get_market_hours(self) -> List[tuple]:
        """获取交易时间段"""
        return self.trading_hours
    
    def calculate_commission(
        self,
        price: float,
        quantity: float,
        side: str
    ) -> Dict[str, float]:
        """
        计算A股交易费用
        
        Args:
            price: 价格
            quantity: 数量
            side: 买卖方向
            
        Returns:
            dict: 费用明细
        """
        turnover = price * quantity  # 成交金额
        
        # 佣金(默认万分之三,最低5元)
        commission_rate = 0.0003
        commission = max(turnover * commission_rate, 5.0)
        
        # 印花税(仅卖出收取,千分之一)
        stamp_tax = 0.0
        if side == 'sell':
            stamp_tax = turnover * 0.001
        
        # 过户费(仅沪市收取,成交金额的0.002%)
        transfer_fee = 0.0
        # 这里需要判断是否为沪市股票
        # if symbol.endswith('.SH'):
        #     transfer_fee = turnover * 0.00002
        
        # 总费用
        total = commission + stamp_tax + transfer_fee
        
        return {
            'commission': round(commission, 2),
            'stamp_tax': round(stamp_tax, 2),
            'transfer_fee': round(transfer_fee, 2),
            'total': round(total, 2)
        }
    
    def get_lot_size(self, symbol: str) -> int:
        """
        获取最小交易单位
        
        A股统一为100股(1手)
        """
        return 100
    
    def get_tick_size(self, symbol: str, price: float) -> float:
        """
        获取最小价格变动
        
        A股统一为0.01元
        """
        return 0.01
    
    # ==================== 私有方法 ====================
    
    def _normalize_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        标准化行情数据字段
        
        将miniQMT的数据格式转换为标准格式
        """
        # 获取字段映射
        field_mapping = DataNormalizer.get_market_field_mapping(self.market_type)
        
        # 重命名列
        data = data.rename(columns=field_mapping)
        
        # 标准化symbol列
        if 'symbol' in data.columns:
            data['symbol'] = data['symbol'].apply(
                lambda x: self.normalize_symbol(x)
            )
        
        return data
