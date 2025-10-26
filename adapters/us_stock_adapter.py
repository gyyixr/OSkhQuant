#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股市场适配器
支持通过Alpaca API和Yahoo Finance获取美股数据和交易
"""

from typing import List, Dict, Optional, Union, Callable, Any
from datetime import datetime, time, date, timedelta
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
        self.market_name = '美股市场'
        self.timezone = pytz.timezone('America/New_York')
        try:
            self.us_holidays = holidays.country_holidays('US')
        except Exception:
            # 如果无法获取美国假日，使用空集合
            self.us_holidays = set()
        
        # 数据提供商
        self.provider = config.get('data_provider', 'yahoo_finance')
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
            import alpaca_trade_api as tradeapi  # type: ignore
            
            # 从配置获取API凭证
            api_key = self.config.get('api_key', '')
            api_secret = self.config.get('api_secret', '')
            endpoint = self.config.get('endpoint', 'https://paper-api.alpaca.markets')
            
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
            
            print(f"✓ Connected to Alpaca API, account status: {account.status}")
            return True
            
        except ImportError:
            raise ImportError("alpaca-trade-api not installed. Run: pip install alpaca-trade-api")
        except Exception as e:
            print(f"✗ Failed to connect to Alpaca: {e}")
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
            
            print("✓ Connected to Yahoo Finance")
            return True
            
        except ImportError:
            raise ImportError("yfinance not installed. Run: pip install yfinance")
        except Exception as e:
            print(f"✗ Failed to connect to Yahoo Finance: {e}")
            raise ConnectionError(f"Yahoo Finance connection failed: {e}")
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.api_client = None
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def get_market_info(self) -> Dict[str, Any]:
        """获取市场基本信息"""
        return {
            'market_type': self.market_type,
            'market_name': self.market_name,
            'trading_hours': [
                (self.MARKET_OPEN.strftime('%H:%M:%S'), self.MARKET_CLOSE.strftime('%H:%M:%S'))
            ],
            'timezone': 'America/New_York',
            'currency': 'USD',
            'tick_size': 0.01,
            'lot_size': 1,
            'price_limit': None,  # 美股无涨跌停限制
            't_plus': 0  # T+0交易
        }
    
    def get_market_data(
        self,
        symbols: List[str],
        period: str = '1d',
        start: Optional[str] = None,
        end: Optional[str] = None,
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
            df = self._get_data_alpaca(raw_symbols, period, start, end)
        elif self.provider == 'yahoo_finance':
            df = self._get_data_yahoo(raw_symbols, period, start, end, dividend_type)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        # 标准化数据
        df = DataNormalizer.normalize_dataframe(df, self.market_type)
        
        # 筛选字段
        if fields:
            available_fields = [f for f in fields if f in df.columns]
            df = df[['symbol', 'time'] + available_fields]
        
        return df  # type: ignore
    
    def _get_data_alpaca(
        self,
        symbols: List[str],
        period: str,
        start_time: Optional[str],
        end_time: Optional[str]
    ) -> pd.DataFrame:
        """从Alpaca获取数据"""
        if self.api_client is None:
            raise RuntimeError("API client not initialized")
        
        # 映射周期
        timeframe_map = {
            '1m': '1Min',
            '5m': '5Min',
            '15m': '15Min',
            '30m': '30Min',
            '60m': '1Hour',
            '1h': '1Hour',
            '1d': '1Day',
            'd': '1Day',
        }
        
        timeframe = timeframe_map.get(period, '1Day')
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 获取历史数据
                bars = self.api_client.get_bars(
                    symbol,
                    timeframe,
                    start=start_time,
                    end=end_time
                ).df
                
                if not bars.empty:
                    # 添加symbol列
                    bars['symbol'] = symbol
                    # 重置索引
                    bars = bars.reset_index()
                    bars = bars.rename(columns={'timestamp': 'time'})
                    all_data.append(bars)
                    
            except Exception as e:
                print(f"Error getting Alpaca data for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # 合并所有数据
        df = pd.concat(all_data, ignore_index=True)
        
        return df
    
    def _get_data_yahoo(
        self,
        symbols: List[str],
        period: str,
        start_time: Optional[str],
        end_time: Optional[str],
        dividend_type: str
    ) -> pd.DataFrame:
        """从Yahoo Finance获取数据"""
        import yfinance as yf
        
        # 映射周期
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '60m': '60m',
            '1h': '1h',
            '1d': '1d',
            'd': '1d',
            '1w': '1wk',
            'w': '1wk',
        }
        
        interval = interval_map.get(period, '1d')
        
        # 映射复权类型
        auto_adjust = dividend_type != 'none'
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 下载数据
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_time,
                    end=end_time,
                    interval=interval,
                    auto_adjust=auto_adjust
                )
                
                if not df.empty:
                    # 添加symbol列
                    df['symbol'] = symbol
                    # 重置索引
                    df = df.reset_index()
                    # 标准化列名
                    df = df.rename(columns={
                        'Date': 'time',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    # 计算成交额
                    if 'amount' not in df.columns:
                        df['amount'] = df['close'] * df['volume']
                    
                    all_data.append(df)
                    
            except Exception as e:
                print(f"Error getting Yahoo Finance data for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # 合并所有数据
        df = pd.concat(all_data, ignore_index=True)
        
        return df
    
    def get_realtime_data(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取实时行情"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Real-time data only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        if isinstance(symbols, str):
            symbols = [symbols]
        
        try:
            # 获取最新行情
            snapshots = self.api_client.get_snapshots(symbols)
            
            data_list = []
            for symbol, snapshot in snapshots.items():
                if snapshot and hasattr(snapshot, 'latest_trade'):
                    data_list.append({
                        'symbol': symbol,
                        'time': snapshot.latest_trade.timestamp,
                        'close': snapshot.latest_trade.price,
                        'volume': snapshot.latest_trade.size,
                        'open': snapshot.daily_bar.open if hasattr(snapshot, 'daily_bar') else None,
                        'high': snapshot.daily_bar.high if hasattr(snapshot, 'daily_bar') else None,
                        'low': snapshot.daily_bar.low if hasattr(snapshot, 'daily_bar') else None,
                    })
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list)
            
            # 使用DataNormalizer标准化数据
            df = DataNormalizer.normalize_dataframe(df, self.market_type)
            
            # 筛选字段
            if fields:
                available_fields = [f for f in fields if f in df.columns]
                df = df[['symbol', 'time'] + available_fields]
            
            return df
            
        except Exception as e:
            print(f"Error getting realtime data: {e}")
            raise
    
    def get_symbols(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取标的列表"""
        if self.provider == 'alpaca':
            if not self.is_connected():
                raise ConnectionError("Not connected to Alpaca")
            
            try:
                # 获取所有可交易资产
                assets = self.api_client.list_assets(
                    status='active',
                    asset_class=category if category else 'us_equity'
                )
                
                result = []
                for asset in assets:
                    result.append({
                        'symbol': self.normalize_symbol(asset.symbol),
                        'name': asset.name,
                        'category': asset.asset_class,
                        'exchange': asset.exchange,
                        'tradable': asset.tradable
                    })
                
                return result
                
            except Exception as e:
                print(f"Error getting symbols: {e}")
                return []
        else:
            # Yahoo Finance没有直接获取列表的API
            print("Symbol list not available with Yahoo Finance provider")
            return []
    
    def download_history_data(
        self,
        symbols: List[str],
        period: str,
        start: str,
        end: str
    ) -> bool:
        """下载历史数据到本地"""
        import os
        
        try:
            # 获取数据
            df = self.get_market_data(
                symbols=symbols,
                period=period,
                start=start,
                end=end
            )
            
            if df.empty:
                print("No data to download")
                return False
            
            # 创建数据目录
            data_dir = self.config.get('data_dir', './data/us_stock')
            os.makedirs(data_dir, exist_ok=True)
            
            # 保存数据
            for symbol in symbols:
                symbol_data = df[df['symbol'] == symbol]
                if not symbol_data.empty:
                    # 提取原始代码作为文件名
                    raw_symbol = self._extract_symbol(symbol)
                    filename = f"{raw_symbol}_{period}_{start}_{end}.csv"
                    filepath = os.path.join(data_dir, filename)
                    symbol_data.to_csv(filepath, index=False)
                    print(f"Saved {symbol} data to {filepath}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading history data: {e}")
            return False
    
    def subscribe_quote(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> bool:
        """订阅实时行情"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Quote subscription only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            # Alpaca的WebSocket订阅需要使用alpaca_trade_api.stream
            # 这里提供基本实现
            from alpaca_trade_api.stream import Stream  # type: ignore
            
            # 创建流对象
            api_key = self.config.get('api_key', '')
            api_secret = self.config.get('api_secret', '')
            
            stream = Stream(
                api_key,
                api_secret,
                base_url=self.config.get('endpoint', 'https://paper-api.alpaca.markets')
            )
            
            # 订阅行情
            for symbol in symbols:
                stream.subscribe_quotes(callback, symbol)
            
            # 启动流
            stream.run()
            
            print(f"Successfully subscribed to {len(symbols)} symbols")
            return True
            
        except Exception as e:
            print(f"Error subscribing to quotes: {e}")
            return False
    
    def unsubscribe_quote(self, symbols: List[str]) -> bool:
        """取消订阅"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Unsubscribe only available with Alpaca")
        
        # Alpaca WebSocket取消订阅
        # 实际实现需要保存stream对象引用
        print(f"Unsubscribe from {len(symbols)} symbols - Not fully implemented")
        return True
    
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
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        # 提取symbol
        raw_symbol = self._extract_symbol(symbol)
        
        try:
            # 下单
            order = self.api_client.submit_order(
                symbol=raw_symbol,
                qty=int(quantity),
                side=side.lower(),
                type=order_type.lower(),
                time_in_force='day',
                limit_price=price if order_type.lower() == 'limit' else None
            )
            
            return {
                'order_id': order.id,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'status': order.status,
                'timestamp': order.submitted_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error placing order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Trading only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            self.api_client.cancel_order(order_id)
            print(f"Successfully cancelled order {order_id}")
            return True
            
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Trading only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            order = self.api_client.get_order(order_id)
            
            return {
                'order_id': order.id,
                'symbol': self.normalize_symbol(order.symbol),
                'side': order.side,
                'quantity': float(order.qty),
                'price': float(order.limit_price) if order.limit_price else None,
                'status': order.status,
                'filled_quantity': float(order.filled_qty),
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                'order_type': order.order_type,
                'timestamp': order.submitted_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error getting order status: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Account info only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            account = self.api_client.get_account()
            
            return {
                'account_id': account.id,
                'balance': float(account.equity),
                'available_cash': float(account.cash),
                'market_value': float(account.long_market_value),
                'currency': 'USD',
                'buying_power': float(account.buying_power),
                'pattern_day_trader': account.pattern_day_trader,
                'account_status': account.status
            }
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            raise
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        if self.provider != 'alpaca':
            raise NotImplementedError("Positions only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            positions = self.api_client.list_positions()
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': self.normalize_symbol(pos.symbol),
                    'quantity': float(pos.qty),
                    'available_quantity': float(pos.qty),  # Alpaca中没有可用量概念
                    'avg_price': float(pos.avg_entry_price),
                    'market_price': float(pos.current_price),
                    'profit_loss': float(pos.unrealized_pl),
                    'profit_loss_ratio': float(pos.unrealized_plpc),
                    'market_value': float(pos.market_value),
                    'side': pos.side
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            raise
    
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
        
        # 检查是否为交易日 (使用YYYYMMDD格式)
        if not self.is_trading_day(et_time.strftime('%Y%m%d')):
            return False
        
        # 检查是否在交易时间内
        current_time = et_time.time()
        return self.MARKET_OPEN <= current_time <= self.MARKET_CLOSE
    
    def is_trading_day(self, date_str: Optional[str] = None) -> bool:
        """
        判断是否为交易日
        
        Args:
            date_str: 日期字符串 'YYYYMMDD'
            
        Returns:
            bool: 是交易日返回True
        """
        if date_str is None:
            dt = datetime.now(self.timezone)
        else:
            dt = datetime.strptime(date_str, '%Y%m%d')
        
        # 周末不交易
        if dt.weekday() >= 5:
            return False
        
        # 检查节假日
        if dt.date() in self.us_holidays:
            return False
        
        return True
    
    def get_trading_calendar(
        self,
        start: str,
        end: str
    ) -> List[date]:
        """
        获取交易日历
        
        Args:
            start: 开始日期 'YYYYMMDD'
            end: 结束日期 'YYYYMMDD'
            
        Returns:
            List[date]: 交易日列表
        """
        start_date = datetime.strptime(start, '%Y%m%d').date()
        end_date = datetime.strptime(end, '%Y%m%d').date()
        
        trading_days = []
        current = start_date
        
        while current <= end_date:
            # 检查是否为交易日
            if current.weekday() < 5 and current not in self.us_holidays:
                trading_days.append(current)
            current += timedelta(days=1)
        
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
        commission_rate = self.config.get('backtest', {}).get(
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
        if self.provider != 'alpaca':
            raise NotImplementedError("PDT rule check only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            # 获取账户信息
            account = self.api_client.get_account()
            
            # 计算近5个交易日的日内交易次数
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # 过去7天以确保包含5个交易日
            
            # 获取最近的订单
            orders = self.api_client.list_orders(
                status='all',
                after=start_date.isoformat(),
                until=end_date.isoformat(),
                limit=500
            )
            
            # 统计日内交易次数
            day_trades = {}
            for order in orders:
                if order.filled_at:
                    trade_date = order.filled_at.date()
                    symbol = order.symbol
                    
                    # 检查是否在同一天内先买后卖或先卖后买
                    key = f"{trade_date}_{symbol}"
                    if key not in day_trades:
                        day_trades[key] = []
                    day_trades[key].append(order)
            
            # 计算日内交易次数
            day_trade_count = 0
            for trades in day_trades.values():
                if len(trades) >= 2:
                    # 简单判断:如果同一天对同一股票有2笔以上交易
                    day_trade_count += 1
            
            return {
                'is_pdt': account.pattern_day_trader,
                'day_trade_count': day_trade_count,
                'account_value': float(account.equity),
                'pdt_threshold': 25000.0,
                'warning': day_trade_count >= 3 and float(account.equity) < 25000
            }
            
        except Exception as e:
            print(f"Error checking PDT rule: {e}")
            raise
    
    def get_market_hours(self) -> List[tuple]:
        """
        获取交易时间段
        
        Returns:
            list[tuple]: 时间段列表,每个元组为(开始时间, 结束时间)
        """
        return [
            (self.MARKET_OPEN.strftime('%H:%M:%S'), self.MARKET_CLOSE.strftime('%H:%M:%S'))
        ]
    
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
        if self.provider != 'alpaca':
            raise NotImplementedError("Trade history only available with Alpaca")
        
        if not self.is_connected():
            raise ConnectionError("Not connected to Alpaca")
        
        try:
            # 转换时间格式
            start_date = None
            end_date = None
            
            if start:
                start_date = datetime.strptime(start, '%Y%m%d').isoformat()
            if end:
                end_date = datetime.strptime(end, '%Y%m%d').isoformat()
            
            # 查询成交记录
            orders = self.api_client.list_orders(
                status='closed',
                after=start_date,
                until=end_date
            )
            
            trades = []
            for order in orders:
                if order.filled_qty and float(order.filled_qty) > 0:
                    trades.append({
                        'trade_id': order.id,
                        'order_id': order.id,
                        'symbol': self.normalize_symbol(order.symbol),
                        'side': order.side,
                        'quantity': float(order.filled_qty),
                        'price': float(order.filled_avg_price) if order.filled_avg_price else 0,
                        'amount': float(order.filled_qty) * float(order.filled_avg_price) if order.filled_avg_price else 0,
                        'timestamp': order.filled_at.isoformat() if order.filled_at else order.submitted_at.isoformat()
                    })
            
            return trades
            
        except Exception as e:
            print(f"Error getting trade history: {e}")
            return []
