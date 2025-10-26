#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场适配器
支持通过富途OpenAPI获取港股数据和交易
"""

from typing import List, Dict, Optional, Union, Callable
from datetime import datetime, time
import pandas as pd
import pytz
import holidays

from .base_adapter import BaseMarketAdapter
from .market_registry import register_adapter
from .data_normalizer import DataNormalizer


@register_adapter('hk_stock')
class HKStockAdapter(BaseMarketAdapter):
    """
    港股市场适配器
    
    支持的数据提供商:
    - 富途OpenAPI (Futu OpenD)
    """
    
    # 港股交易时间 (香港时间)
    MORNING_OPEN = time(9, 30, 0)
    MORNING_CLOSE = time(12, 0, 0)
    AFTERNOON_OPEN = time(13, 0, 0)
    AFTERNOON_CLOSE = time(16, 0, 0)
    
    # 港股价格档位表
    TICK_SIZE_TABLE = [
        {'min_price': 0.01, 'max_price': 0.25, 'tick': 0.001},
        {'min_price': 0.25, 'max_price': 0.50, 'tick': 0.005},
        {'min_price': 0.50, 'max_price': 10.00, 'tick': 0.01},
        {'min_price': 10.00, 'max_price': 20.00, 'tick': 0.02},
        {'min_price': 20.00, 'max_price': 100.00, 'tick': 0.05},
        {'min_price': 100.00, 'max_price': 200.00, 'tick': 0.10},
        {'min_price': 200.00, 'max_price': 500.00, 'tick': 0.20},
        {'min_price': 500.00, 'max_price': 1000.00, 'tick': 0.50},
        {'min_price': 1000.00, 'max_price': 2000.00, 'tick': 1.00},
        {'min_price': 2000.00, 'max_price': 5000.00, 'tick': 2.00},
        {'min_price': 5000.00, 'max_price': 9995.00, 'tick': 5.00},
    ]
    
    def __init__(self, config):
        """初始化港股适配器"""
        super().__init__(config)
        self.market_type = 'hk_stock'
        self.timezone = pytz.timezone('Asia/Hong_Kong')
        self.hk_holidays = holidays.HongKong()
        
        self.provider = config.data_provider
        self.api_client = None
        self.connected = False
        
        # 手数缓存
        self.lot_size_cache = {}
    
    def connect(self) -> bool:
        """连接到富途OpenD"""
        try:
            # 需要安装 futu-api
            # pip install futu-api
            from futu import OpenQuoteContext, OpenSecTradeContext
            
            host = self.config.config_dict.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.config_dict.get('data_source', {}).get('port', 11111)
            
            # 创建行情连接
            self.quote_ctx = OpenQuoteContext(host=host, port=port)
            
            # 测试连接
            ret, data = self.quote_ctx.get_market_state(['HK.00700'])
            if ret != 0:
                raise ConnectionError(f"Failed to connect: {data}")
            
            self.connected = True
            self.logger.info(f"Connected to Futu OpenD at {host}:{port}")
            return True
            
        except ImportError:
            raise ImportError("futu-api not installed. Run: pip install futu-api")
        except Exception as e:
            self.logger.error(f"Failed to connect to Futu: {e}")
            raise ConnectionError(f"Futu connection failed: {e}")
    
    def disconnect(self) -> bool:
        """断开连接"""
        if hasattr(self, 'quote_ctx'):
            self.quote_ctx.close()
        if hasattr(self, 'trade_ctx'):
            self.trade_ctx.close()
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_market_type(self) -> str:
        """获取市场类型"""
        return self.market_type
    
    def get_market_data(
        self,
        symbols: Union[str, List[str]],
        period: str = '1d',
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        fields: Optional[List[str]] = None,
        dividend_type: str = 'none'
    ) -> pd.DataFrame:
        """获取历史行情数据"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        # 标准化symbol
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # TODO: 实现Futu API数据获取
        raise NotImplementedError("Futu data fetching not yet implemented")
    
    def get_realtime_data(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取实时行情"""
        # TODO: 实现实时数据获取
        raise NotImplementedError("Real-time data not yet implemented")
    
    def subscribe_quote(
        self,
        symbols: Union[str, List[str]],
        callback: Callable
    ) -> bool:
        """订阅实时行情"""
        # TODO: 实现行情订阅
        raise NotImplementedError("Quote subscription not yet implemented")
    
    def unsubscribe_quote(self, symbols: Union[str, List[str]]) -> bool:
        """取消订阅"""
        # TODO: 实现取消订阅
        raise NotImplementedError("Unsubscribe not yet implemented")
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> str:
        """下单"""
        # TODO: 实现下单功能
        raise NotImplementedError("Order placement not yet implemented")
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        # TODO: 实现撤单
        raise NotImplementedError("Order cancellation not yet implemented")
    
    def get_order_status(self, order_id: str) -> dict:
        """查询订单状态"""
        # TODO: 实现订单查询
        raise NotImplementedError("Order status not yet implemented")
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        # TODO: 实现账户信息获取
        raise NotImplementedError("Account info not yet implemented")
    
    def get_positions(self) -> pd.DataFrame:
        """获取持仓信息"""
        # TODO: 实现持仓查询
        raise NotImplementedError("Positions not yet implemented")
    
    def is_trading_time(self, dt: Optional[datetime] = None) -> bool:
        """判断是否为交易时间"""
        if dt is None:
            dt = datetime.now(pytz.UTC)
        
        # 转换为香港时间
        hk_time = dt.astimezone(self.timezone)
        
        # 检查是否为交易日
        if not self.is_trading_day(hk_time.strftime('%Y-%m-%d')):
            return False
        
        # 检查是否在交易时间内
        current_time = hk_time.time()
        
        # 上午交易时段
        if self.MORNING_OPEN <= current_time <= self.MORNING_CLOSE:
            return True
        
        # 下午交易时段
        if self.AFTERNOON_OPEN <= current_time <= self.AFTERNOON_CLOSE:
            return True
        
        return False
    
    def is_trading_day(self, date: Optional[str] = None) -> bool:
        """判断是否为交易日"""
        if date is None:
            date = datetime.now(self.timezone).strftime('%Y-%m-%d')
        
        dt = datetime.strptime(date, '%Y-%m-%d')
        
        # 周末不交易
        if dt.weekday() >= 5:
            return False
        
        # 检查香港节假日
        if dt.date() in self.hk_holidays:
            return False
        
        return True
    
    def get_trading_calendar(
        self,
        start_date: str,
        end_date: str
    ) -> List[str]:
        """获取交易日历"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        trading_days = []
        current = start
        
        while current <= end:
            if self.is_trading_day(current.strftime('%Y-%m-%d')):
                trading_days.append(current.strftime('%Y-%m-%d'))
            current += pd.Timedelta(days=1)
        
        return trading_days
    
    def calculate_commission(
        self,
        price: float,
        quantity: float,
        side: str
    ) -> dict:
        """
        计算港股交易费用
        
        费用结构:
        - 佣金: 一般为成交金额的0.25%
        - 印花税: 成交金额的0.1%
        - 交易征费: 成交金额的0.0027%
        - 交易费: 成交金额的0.005%
        - 结算费: 成交金额的0.002%
        """
        turnover = price * quantity
        
        # 佣金
        commission_rate = self.config.config_dict.get('backtest', {}).get(
            'trade_cost', {}
        ).get('commission_rate', 0.0025)
        min_commission = self.config.config_dict.get('backtest', {}).get(
            'trade_cost', {}
        ).get('min_commission', 50.0)
        commission = max(turnover * commission_rate, min_commission)
        
        # 印花税 (仅买卖双边都收取)
        stamp_duty = turnover * 0.001
        
        # 交易征费
        trading_levy = turnover * 0.000027
        
        # 交易费
        trading_fee = turnover * 0.00005
        
        # 结算费
        settlement_fee = turnover * 0.00002
        
        total = commission + stamp_duty + trading_levy + trading_fee + settlement_fee
        
        return {
            'commission': commission,
            'stamp_duty': stamp_duty,
            'trading_levy': trading_levy,
            'trading_fee': trading_fee,
            'settlement_fee': settlement_fee,
            'total': total
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """标准化标的代码"""
        return DataNormalizer.normalize_symbol(symbol, self.market_type)
    
    def get_lot_size(self, symbol: str) -> int:
        """
        获取最小交易单位(每手股数)
        
        Args:
            symbol: 标的代码 (如 'HK.00700')
            
        Returns:
            int: 每手股数
        """
        # 检查缓存
        if symbol in self.lot_size_cache:
            return self.lot_size_cache[symbol]
        
        # TODO: 从Futu API查询实际手数
        # 这里提供常见股票的默认值
        default_lot_sizes = {
            'HK.00700': 100,  # 腾讯
            'HK.09988': 50,   # 阿里巴巴
            'HK.00941': 50,   # 中国移动
            'HK.01299': 500,  # 友邦保险
            'HK.00005': 400,  # 汇丰控股
        }
        
        lot_size = default_lot_sizes.get(symbol, 100)  # 默认100股
        self.lot_size_cache[symbol] = lot_size
        
        return lot_size
    
    def get_tick_size(self, symbol: str, price: float) -> float:
        """
        获取最小价格变动单位
        
        Args:
            symbol: 标的代码
            price: 当前价格
            
        Returns:
            float: 最小价格变动单位
        """
        # 根据价格档位表查找
        for tier in self.TICK_SIZE_TABLE:
            if tier['min_price'] <= price < tier['max_price']:
                return tier['tick']
        
        # 超过最高档位,使用最后一档
        return self.TICK_SIZE_TABLE[-1]['tick']
    
    def validate_price(self, symbol: str, price: float) -> bool:
        """
        验证价格是否符合价格档位要求
        
        Args:
            symbol: 标的代码
            price: 价格
            
        Returns:
            bool: 价格有效返回True
        """
        tick_size = self.get_tick_size(symbol, price)
        
        # 检查价格是否为tick_size的整数倍
        remainder = price % tick_size
        return abs(remainder) < 1e-8 or abs(remainder - tick_size) < 1e-8
    
    def adjust_price_to_tick(self, symbol: str, price: float, direction: str = 'nearest') -> float:
        """
        调整价格到合法档位
        
        Args:
            symbol: 标的代码
            price: 原始价格
            direction: 调整方向 ('up', 'down', 'nearest')
            
        Returns:
            float: 调整后的价格
        """
        tick_size = self.get_tick_size(symbol, price)
        
        if direction == 'up':
            return ((price // tick_size) + 1) * tick_size
        elif direction == 'down':
            return (price // tick_size) * tick_size
        else:  # nearest
            return round(price / tick_size) * tick_size
    
    def validate_quantity(self, symbol: str, quantity: float) -> bool:
        """
        验证数量是否为手数的整数倍
        
        Args:
            symbol: 标的代码
            quantity: 数量
            
        Returns:
            bool: 数量有效返回True
        """
        lot_size = self.get_lot_size(symbol)
        return quantity % lot_size == 0
