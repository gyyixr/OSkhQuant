#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场适配器
支持通过Alpaca API和Yahoo Finance获取美股数据和交易
"""

from typing import List, Dict, Optional, Union, Callable
from datetime import datetime, time
import pandas as pd
import pytz
import holidays

from .base_adapter import BaseMarketAdapter
from .market_registry import register_adapter
from .data_normalizer import DataNormalizer


@register_adapter('us_stock')
class USStockAdapter(BaseMarketAdapter):
    """
    美股市场适配器基类
    
    支持的数据提供商:
    - Alpaca API (实时和历史数据)
    - Yahoo Finance (历史数据)
    """
    
    # 美股交易时间 (美东时间)
    MARKET_OPEN = time(9, 30, 0)
    MARKET_CLOSE = time(16, 0, 0)
    
    # 盘前盘后交易时间
    PRE_MARKET_OPEN = time(4, 0, 0)
    AFTER_MARKET_CLOSE = time(20, 0, 0)
    
    def __init__(self, config):
        """
        初始化美股适配器
        
        Args:
            config: 配置对象,包含数据源和API凭证
        """
        super().__init__(config)
        self.market_type = 'us_stock'
        self.timezone = pytz.timezone('America/New_York')
        self.us_holidays = holidays.US()
        
        # 数据提供商
        self.provider = config.data_provider
        self.api_client = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            bool: 连接成功返回True
            
        Raises:
            ConnectionError: 连接失败时抛出
        """
        if self.provider == 'alpaca':
            return self._connect_alpaca()
        elif self.provider == 'yahoo_finance':
            return self._connect_yahoo()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _connect_alpaca(self) -> bool:
        """连接到Alpaca API"""
        try:
            # 注意: 需要安装 alpaca-trade-api
            # pip install alpaca-trade-api
            import alpaca_trade_api as tradeapi
            
            # 从配置获取API凭证
            credentials = self.config.get_decrypted_credentials()
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            endpoint = self.config.config_dict.get('data_source', {}).get('endpoint')
            
            if not api_key or not api_secret:
                raise ValueError("Missing Alpaca API credentials")
            
            # 创建API客户端
            self.api_client = tradeapi.REST(
                api_key,
                api_secret,
                endpoint,
                api_version='v2'
            )
            
            # 测试连接
            account = self.api_client.get_account()
            self.connected = True
            
            self.logger.info(f"Connected to Alpaca API, account status: {account.status}")
            return True
            
        except ImportError:
            raise ImportError("alpaca-trade-api not installed. Run: pip install alpaca-trade-api")
        except Exception as e:
            self.logger.error(f"Failed to connect to Alpaca: {e}")
            raise ConnectionError(f"Alpaca connection failed: {e}")
    
    def _connect_yahoo(self) -> bool:
        """连接到Yahoo Finance"""
        try:
            # 注意: 需要安装 yfinance
            # pip install yfinance
            import yfinance as yf
            
            # Yahoo Finance不需要API密钥
            self.api_client = yf
            self.connected = True
            
            self.logger.info("Connected to Yahoo Finance")
            return True
            
        except ImportError:
            raise ImportError("yfinance not installed. Run: pip install yfinance")
        except Exception as e:
            self.logger.error(f"Failed to connect to Yahoo Finance: {e}")
            raise ConnectionError(f"Yahoo Finance connection failed: {e}")
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.api_client = None
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
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
        """
        获取历史行情数据
        
        Args:
            symbols: 标的代码或列表 (支持US.AAPL格式或AAPL格式)
            period: K线周期 ('1m', '5m', '1h', '1d', etc.)
            start_time: 开始时间
            end_time: 结束时间
            fields: 需要的字段
            dividend_type: 复权类型 ('none', 'front', 'back')
            
        Returns:
            pd.DataFrame: 标准化的行情数据
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to data source")
        
        # 标准化symbol
        if isinstance(symbols, str):
            symbols = [symbols]
        
        raw_symbols = [self._extract_symbol(s) for s in symbols]
        
        # 根据提供商获取数据
        if self.provider == 'alpaca':
            df = self._get_data_alpaca(raw_symbols, period, start_time, end_time)
        elif self.provider == 'yahoo_finance':
            df = self._get_data_yahoo(raw_symbols, period, start_time, end_time, dividend_type)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        # 标准化数据
        df = DataNormalizer.normalize_dataframe(df, self.market_type)
        
        # 筛选字段
        if fields:
            available_fields = [f for f in fields if f in df.columns]
            df = df[['symbol', 'time'] + available_fields]
        
        return df
    
    def _get_data_alpaca(
        self,
        symbols: List[str],
        period: str,
        start_time: Optional[str],
        end_time: Optional[str]
    ) -> pd.DataFrame:
        """从Alpaca获取数据"""
        # TODO: 实现Alpaca数据获取
        # 这需要实际的API调用
        raise NotImplementedError("Alpaca data fetching not yet implemented")
    
    def _get_data_yahoo(
        self,
        symbols: List[str],
        period: str,
        start_time: Optional[str],
        end_time: Optional[str],
        dividend_type: str
    ) -> pd.DataFrame:
        """从Yahoo Finance获取数据"""
        # TODO: 实现Yahoo Finance数据获取
        # 这需要实际的API调用
        raise NotImplementedError("Yahoo Finance data fetching not yet implemented")
    
    def get_realtime_data(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取实时行情"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Real-time data only available with Alpaca")
        
        # TODO: 实现实时数据获取
        raise NotImplementedError("Real-time data not yet implemented")
    
    def subscribe_quote(
        self,
        symbols: Union[str, List[str]],
        callback: Callable
    ) -> bool:
        """订阅实时行情"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Quote subscription only available with Alpaca")
        
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
        """
        下单
        
        Args:
            symbol: 标的代码
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            quantity: 数量
            price: 价格 (限价单必填)
            **kwargs: 其他参数
            
        Returns:
            str: 订单ID
        """
        if self.provider != 'alpaca':
            raise NotImplementedError("Trading only available with Alpaca")
        
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
        if self.provider != 'alpaca':
            raise NotImplementedError("Account info only available with Alpaca")
        
        # TODO: 实现账户信息获取
        raise NotImplementedError("Account info not yet implemented")
    
    def get_positions(self) -> pd.DataFrame:
        """获取持仓信息"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Positions only available with Alpaca")
        
        # TODO: 实现持仓查询
        raise NotImplementedError("Positions not yet implemented")
    
    def is_trading_time(self, dt: Optional[datetime] = None) -> bool:
        """
        判断是否为交易时间
        
        Args:
            dt: 指定时间 (UTC), None表示当前时间
            
        Returns:
            bool: 是交易时间返回True
        """
        if dt is None:
            dt = datetime.now(pytz.UTC)
        
        # 转换为美东时间
        et_time = dt.astimezone(self.timezone)
        
        # 检查是否为交易日
        if not self.is_trading_day(et_time.strftime('%Y-%m-%d')):
            return False
        
        # 检查是否在交易时间内
        current_time = et_time.time()
        return self.MARKET_OPEN <= current_time <= self.MARKET_CLOSE
    
    def is_trading_day(self, date: Optional[str] = None) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串 'YYYY-MM-DD'
            
        Returns:
            bool: 是交易日返回True
        """
        if date is None:
            date = datetime.now(self.timezone).strftime('%Y-%m-%d')
        
        dt = datetime.strptime(date, '%Y-%m-%d')
        
        # 周末不交易
        if dt.weekday() >= 5:
            return False
        
        # 检查节假日
        if dt.date() in self.us_holidays:
            return False
        
        return True
    
    def get_trading_calendar(
        self,
        start_date: str,
        end_date: str
    ) -> List[str]:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            
        Returns:
            List[str]: 交易日列表
        """
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
        计算美股交易费用
        
        Args:
            price: 价格
            quantity: 数量
            side: 'buy' or 'sell'
            
        Returns:
            dict: 费用明细
                {
                    'commission': 佣金,
                    'sec_fee': SEC费 (仅卖出),
                    'finra_taf': FINRA TAF (仅卖出),
                    'total': 总费用
                }
        """
        turnover = price * quantity
        
        # 佣金 (多数券商已免佣)
        commission_rate = self.config.config_dict.get('backtest', {}).get(
            'trade_cost', {}
        ).get('commission_per_share', 0.0)
        commission = quantity * commission_rate
        
        # SEC费 (仅卖出时收取)
        sec_fee = 0.0
        if side == 'sell':
            sec_fee_rate = 0.0000278  # 2024年费率
            sec_fee = turnover * sec_fee_rate
        
        # FINRA TAF (仅卖出时收取)
        finra_taf = 0.0
        if side == 'sell':
            finra_taf_rate = 0.000166  # 2024年费率
            finra_taf = turnover * finra_taf_rate
        
        total = commission + sec_fee + finra_taf
        
        return {
            'commission': commission,
            'sec_fee': sec_fee,
            'finra_taf': finra_taf,
            'total': total
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化标的代码
        
        Args:
            symbol: 原始代码 (如 'AAPL' 或 'US.AAPL')
            
        Returns:
            str: 标准化代码 'US.AAPL'
        """
        return DataNormalizer.normalize_symbol(symbol, self.market_type)
    
    def _extract_symbol(self, symbol: str) -> str:
        """
        从标准化代码提取原始symbol
        
        Args:
            symbol: 标准化代码 'US.AAPL'
            
        Returns:
            str: 原始代码 'AAPL'
        """
        if symbol.startswith('US.'):
            return symbol[3:]
        return symbol
    
    def check_pdt_rule(self) -> dict:
        """
        检查PDT规则 (Pattern Day Trader)
        
        PDT规则: 账户价值低于$25,000时,5个交易日内不能超过3次日内交易
        
        Returns:
            dict: PDT检查结果
                {
                    'is_pdt': bool,
                    'day_trade_count': int,
                    'account_value': float
                }
        """
        # TODO: 实现PDT规则检查
        # 需要查询账户信息和交易历史
        raise NotImplementedError("PDT rule check not yet implemented")
