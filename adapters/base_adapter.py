# coding: utf-8
"""
市场适配器基类
定义所有市场适配器必须实现的统一接口规范
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date
import pandas as pd


class BaseMarketAdapter(ABC):
    """
    市场适配器基类
    所有市场适配器必须继承此类并实现所有抽象方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化市场适配器
        
        Args:
            config: 市场配置字典,包含API密钥、端点等信息
        """
        self.config = config
        self.connected = False
        self.market_type = ""  # 子类需要设置,如: china_a_stock, us_stock, hk_stock, cryptocurrency
        self.market_name = ""  # 市场显示名称,如: A股市场, 美股市场
        
    # ==================== 基础接口 ====================
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            bool: 断开是否成功
        """
        pass
    
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 是否已连接
        """
        return self.connected
    
    @abstractmethod
    def get_market_info(self) -> Dict[str, Any]:
        """
        获取市场基本信息
        
        Returns:
            dict: 市场信息字典,包含:
                - market_type: 市场类型
                - market_name: 市场名称
                - trading_hours: 交易时间段
                - timezone: 时区
                - currency: 货币单位
        """
        pass
    
    # ==================== 数据接口 ====================
    
    @abstractmethod
    def get_symbols(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取标的列表
        
        Args:
            category: 分类(股票/期货/加密货币等),None表示全部
            
        Returns:
            list[dict]: 标的信息列表,每个字典包含:
                - symbol: 标准化代码
                - name: 标的名称
                - category: 分类
                - exchange: 交易所
        """
        pass
    
    @abstractmethod
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
            symbols: 标的代码列表(标准化格式)
            period: 周期,如'1m', '5m', '1d'等
            start: 开始时间,格式YYYYMMDD
            end: 结束时间,格式YYYYMMDD
            fields: 数据字段列表,None表示全部字段
            dividend_type: 复权方式,'none'/'front'/'back'
            
        Returns:
            DataFrame: 行情数据,标准化字段:
                - symbol: 标的代码
                - timestamp: 时间戳
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - amount: 成交额
        """
        pass
    
    @abstractmethod
    def download_history_data(
        self,
        symbols: List[str],
        period: str,
        start: str,
        end: str
    ) -> bool:
        """
        下载历史数据到本地
        
        Args:
            symbols: 标的代码列表
            period: 周期
            start: 开始时间
            end: 结束时间
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def subscribe_quote(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> bool:
        """
        订阅实时行情
        
        Args:
            symbols: 标的代码列表
            callback: 回调函数,接收行情数据字典
            
        Returns:
            bool: 订阅是否成功
        """
        pass
    
    @abstractmethod
    def unsubscribe_quote(self, symbols: List[str]) -> bool:
        """
        取消行情订阅
        
        Args:
            symbols: 标的代码列表
            
        Returns:
            bool: 是否成功
        """
        pass
    
    # ==================== 交易接口 ====================
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            dict: 账户信息,包含:
                - account_id: 账户ID
                - balance: 总资产
                - available_cash: 可用资金
                - market_value: 持仓市值
                - currency: 货币单位
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Returns:
            list[dict]: 持仓列表,每个字典包含:
                - symbol: 标的代码
                - quantity: 持仓数量
                - available_quantity: 可用数量
                - avg_price: 平均成本
                - market_price: 最新价
                - profit_loss: 浮动盈亏
        """
        pass
    
    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = 'limit'
    ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 标的代码
            side: 买卖方向,'buy'/'sell'
            quantity: 数量
            price: 价格,None表示市价单
            order_type: 订单类型,'limit'/'market'等
            
        Returns:
            dict: 订单信息,包含:
                - order_id: 订单ID
                - symbol: 标的代码
                - side: 买卖方向
                - quantity: 数量
                - price: 价格
                - status: 订单状态
                - timestamp: 下单时间
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            dict: 订单状态信息
        """
        pass
    
    @abstractmethod
    def get_trade_history(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取成交记录
        
        Args:
            start: 开始时间,格式YYYYMMDD
            end: 结束时间,格式YYYYMMDD
            
        Returns:
            list[dict]: 成交记录列表
        """
        pass
    
    # ==================== 市场特有接口 ====================
    
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化标的代码格式
        
        Args:
            symbol: 原始代码
            
        Returns:
            str: 标准化后的代码
            
        Examples:
            A股: 000001.SZ -> CN.000001.SZ
            美股: AAPL -> US.AAPL
            港股: 00700 -> HK.00700
            加密货币: BTCUSDT -> CRYPTO.BTC.USDT
        """
        pass
    
    def denormalize_symbol(self, symbol: str) -> str:
        """
        反标准化标的代码(转换为原始格式)
        
        Args:
            symbol: 标准化代码
            
        Returns:
            str: 原始代码
        """
        # 默认实现:去除市场前缀
        if '.' in symbol:
            parts = symbol.split('.', 1)
            if parts[0] in ['CN', 'US', 'HK', 'CRYPTO']:
                return parts[1]
        return symbol
    
    @abstractmethod
    def get_trading_calendar(
        self,
        start: str,
        end: str
    ) -> List[date]:
        """
        获取交易日历
        
        Args:
            start: 开始日期,格式YYYYMMDD
            end: 结束日期,格式YYYYMMDD
            
        Returns:
            list[date]: 交易日列表
        """
        pass
    
    @abstractmethod
    def get_market_hours(self) -> List[tuple]:
        """
        获取交易时间段
        
        Returns:
            list[tuple]: 时间段列表,每个元组为(开始时间, 结束时间)
                格式: ("HH:MM:SS", "HH:MM:SS")
        """
        pass
    
    def is_trading_time(self, dt: datetime) -> bool:
        """
        判断指定时间是否为交易时间
        
        Args:
            dt: 日期时间对象
            
        Returns:
            bool: 是否为交易时间
        """
        # 首先检查是否为交易日
        trading_days = self.get_trading_calendar(
            dt.strftime("%Y%m%d"),
            dt.strftime("%Y%m%d")
        )
        if not trading_days:
            return False
        
        # 检查是否在交易时间段内
        current_time = dt.time()
        market_hours = self.get_market_hours()
        
        for start_str, end_str in market_hours:
            start_time = datetime.strptime(start_str, "%H:%M:%S").time()
            end_time = datetime.strptime(end_str, "%H:%M:%S").time()
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    @abstractmethod
    def calculate_commission(
        self,
        price: float,
        quantity: float,
        side: str
    ) -> Dict[str, float]:
        """
        计算交易费用
        
        Args:
            price: 价格
            quantity: 数量
            side: 买卖方向,'buy'/'sell'
            
        Returns:
            dict: 费用明细,包含:
                - commission: 佣金
                - tax: 税费
                - total: 总费用
                - 以及其他市场特定费用项
        """
        pass
    
    # ==================== 辅助方法 ====================
    
    def get_tick_size(self, symbol: str, price: float) -> float:
        """
        获取最小价格变动单位
        
        Args:
            symbol: 标的代码
            price: 当前价格
            
        Returns:
            float: 最小价格变动单位
        """
        # 默认实现:返回0.01
        # 子类可以根据市场特性重写此方法(如港股的价格档位)
        return 0.01
    
    def get_lot_size(self, symbol: str) -> int:
        """
        获取最小交易单位(手数)
        
        Args:
            symbol: 标的代码
            
        Returns:
            int: 最小交易单位
        """
        # 默认实现:返回1
        # 子类可以根据市场特性重写此方法(如港股的每手股数)
        return 1
    
    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None
    ) -> tuple[bool, str]:
        """
        验证订单参数
        
        Args:
            symbol: 标的代码
            side: 买卖方向
            quantity: 数量
            price: 价格
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 基础验证
        if side not in ['buy', 'sell']:
            return False, f"无效的买卖方向: {side}"
        
        if quantity <= 0:
            return False, f"无效的数量: {quantity}"
        
        if price is not None and price <= 0:
            return False, f"无效的价格: {price}"
        
        # 检查最小交易单位
        lot_size = self.get_lot_size(symbol)
        if quantity % lot_size != 0:
            return False, f"数量必须是{lot_size}的整数倍"
        
        return True, ""
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(market={self.market_type}, connected={self.connected})>"
