# coding: utf-8
"""
加密货币市场适配器
支持币安(Binance)等主流加密货币交易所
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date, timedelta
import pandas as pd
import pytz
from .base_adapter import BaseMarketAdapter
from .market_registry import register_adapter
from .data_normalizer import DataNormalizer


@register_adapter('cryptocurrency')
class CryptoAdapter(BaseMarketAdapter):
    """
    加密货币市场适配器
    支持通过Binance或CCXT进行加密货币交易
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化加密货币适配器
        
        Args:
            config: 配置字典,包含API密钥等信息
        """
        super().__init__(config)
        self.market_type = "cryptocurrency"
        self.market_name = "加密货币市场"
        
        # 获取配置
        data_source = config.get('data_source', {})
        self.provider = data_source.get('provider', 'binance')  # binance 或 ccxt
        self.api_key = data_source.get('api_key', '')
        self.api_secret = data_source.get('api_secret', '')
        self.endpoint = data_source.get('endpoint', 'https://api.binance.com')
        self.testnet = data_source.get('testnet', False)
        
        # 客户端对象
        self.client = None
        self.exchange = None  # CCXT交易所对象
        
        # 数据缓存
        self._symbols_cache = None
        self._cache_time = None
        
    # ==================== 基础接口 ====================
    
    def connect(self) -> bool:
        """
        连接到加密货币交易所
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.provider == 'binance':
                return self._connect_binance()
            elif self.provider == 'ccxt':
                return self._connect_ccxt()
            else:
                print(f"❌ 不支持的数据提供商: {self.provider}")
                return False
        except Exception as e:
            print(f"❌ 连接加密货币交易所失败: {e}")
            return False
    
    def _connect_binance(self) -> bool:
        """使用python-binance连接"""
        try:
            from binance.client import Client  # type: ignore
            from binance.exceptions import BinanceAPIException  # type: ignore
            
            # 创建客户端
            if self.testnet:
                # 测试网
                self.client = Client(
                    self.api_key,
                    self.api_secret,
                    testnet=True
                )
            else:
                # 正式网
                self.client = Client(
                    self.api_key,
                    self.api_secret
                )
            
            # 测试连接
            self.client.ping()
            self.connected = True
            print(f"✓ 已连接到Binance ({'测试网' if self.testnet else '正式网'})")
            return True
            
        except Exception as e:
            print(f"❌ Binance连接失败: {e}")
            return False
    
    def _connect_ccxt(self) -> bool:
        """使用CCXT连接"""
        try:
            import ccxt  # type: ignore
            
            # 创建交易所对象
            exchange_id = self.config.get('data_source', {}).get('exchange_id', 'binance')
            exchange_class = getattr(ccxt, exchange_id)
            
            self.exchange = exchange_class({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            })
            
            # 测试网配置
            if self.testnet and hasattr(self.exchange, 'set_sandbox_mode'):
                self.exchange.set_sandbox_mode(True)
            
            # 测试连接
            self.exchange.load_markets()
            self.connected = True
            print(f"✓ 已连接到{exchange_id} (CCXT)")
            return True
            
        except Exception as e:
            print(f"❌ CCXT连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            self.client = None
            self.exchange = None
            self.connected = False
            print("✓ 已断开加密货币交易所连接")
            return True
        except Exception as e:
            print(f"❌ 断开连接失败: {e}")
            return False
    
    def get_market_info(self) -> Dict[str, Any]:
        """
        获取市场基本信息
        
        Returns:
            dict: 市场信息
        """
        return {
            'market_type': self.market_type,
            'market_name': self.market_name,
            'provider': self.provider,
            'trading_hours': '24/7',
            'timezone': 'UTC',
            'testnet': self.testnet,
            'features': [
                '24小时交易',
                '无涨跌停限制',
                '支持杠杆交易',
                '现货和合约'
            ]
        }
    
    def get_market_type(self) -> str:
        """
        获取市场类型标识
        
        Returns:
            str: 'cryptocurrency'
        """
        return self.market_type
    
    # ==================== 数据接口 ====================
    
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
            DataFrame: 行情数据
        """
        # 加密货币适配器支持单个标的查询
        if not symbols:
            return pd.DataFrame()
        
        # 只获取第一个标的的数据
        symbol = symbols[0]
        if not self.is_connected():
            print("❌ 未连接到交易所,请先调用connect()")
            return pd.DataFrame()
        
        try:
            if self.provider == 'binance':
                return self._get_data_binance(symbol, period, start, end)
            elif self.provider == 'ccxt':
                return self._get_data_ccxt(symbol, period, start, end)
            else:
                print(f"❌ 不支持的数据提供商: {self.provider}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ 获取行情数据失败: {e}")
            return pd.DataFrame()
    
    def _get_data_binance(
        self,
        symbol: str,
        period: str,
        start: Optional[str],
        end: Optional[str]
    ) -> pd.DataFrame:
        """使用Binance API获取数据"""
        from binance.client import Client  # type: ignore
        
        # 转换周期格式
        interval_map = {
            '1m': Client.KLINE_INTERVAL_1MINUTE,
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '30m': Client.KLINE_INTERVAL_30MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
            '1w': Client.KLINE_INTERVAL_1WEEK,
        }
        
        interval = interval_map.get(period, Client.KLINE_INTERVAL_1DAY)
        
        # 准备参数
        kwargs = {'symbol': symbol, 'interval': interval}
        
        if start:
            kwargs['start_str'] = start
        if end:
            kwargs['end_str'] = end
        else:
            # 默认获取最近100条
            kwargs['limit'] = 100
        
        # 获取K线数据
        if self.client:
            klines = self.client.get_historical_klines(**kwargs)
        else:
            return pd.DataFrame()
        
        if not klines:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(klines, columns=[  # type: ignore
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # 数据类型转换
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df['amount'] = df['quote_volume'].astype(float)
        df['symbol'] = symbol
        
        return df
    
    def _get_data_ccxt(
        self,
        symbol: str,
        period: str,
        start: Optional[str],
        end: Optional[str]
    ) -> pd.DataFrame:
        """使用CCXT获取数据"""
        # 转换symbol格式: BTCUSDT -> BTC/USDT
        if '/' not in symbol:
            # 简单分割,假设计价货币为USDT
            for quote in ['USDT', 'BUSD', 'BTC', 'ETH', 'BNB']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    symbol = f"{base}/{quote}"
                    break
        
        # 准备参数
        since = None
        if start:
            dt = datetime.strptime(start, '%Y%m%d')
            since = int(dt.timestamp() * 1000)
        
        limit = 1000
        
        # 获取OHLCV数据
        if self.exchange:
            ohlcv = self.exchange.fetch_ohlcv(symbol, period, since, limit)
        else:
            return pd.DataFrame()
        
        if not ohlcv:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  # type: ignore
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['amount'] = df['close'] * df['volume']  # 估算成交额
        df['symbol'] = symbol
        
        return df
    
    def get_realtime_data(
        self,
        symbols: List[str],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取实时行情数据
        
        Args:
            symbols: 交易对列表
            fields: 需要的字段列表
            
        Returns:
            dict: {symbol: {field: value}}
        """
        if not self.is_connected():
            print("❌ 未连接到交易所")
            return {}
        
        try:
            if self.provider == 'binance':
                return self._get_realtime_binance(symbols, fields)
            elif self.provider == 'ccxt':
                return self._get_realtime_ccxt(symbols, fields)
            else:
                return {}
        except Exception as e:
            print(f"❌ 获取实时数据失败: {e}")
            return {}
    
    def _get_realtime_binance(self, symbols: List[str], fields: Optional[List[str]]) -> Dict:
        """使用Binance获取实时数据"""
        result = {}
        
        if not self.client:
            return result
        
        for symbol in symbols:
            ticker = self.client.get_ticker(symbol=symbol)
            
            result[symbol] = {
                'symbol': symbol,
                'last_price': float(ticker['lastPrice']),
                'bid_price': float(ticker['bidPrice']),
                'ask_price': float(ticker['askPrice']),
                'volume': float(ticker['volume']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'open': float(ticker['openPrice']),
                'change_pct': float(ticker['priceChangePercent']),
                'timestamp': pd.Timestamp.now(tz='UTC')
            }
        
        return result
    
    def _get_realtime_ccxt(self, symbols: List[str], fields: Optional[List[str]]) -> Dict:
        """使用CCXT获取实时数据"""
        result = {}
        
        if not self.exchange:
            return result
        
        for symbol in symbols:
            # 转换格式
            symbol_ccxt = symbol
            if '/' not in symbol:
                for quote in ['USDT', 'BUSD', 'BTC', 'ETH']:
                    if symbol.endswith(quote):
                        base = symbol[:-len(quote)]
                        symbol_ccxt = f"{base}/{quote}"
                        break
            
            ticker = self.exchange.fetch_ticker(symbol_ccxt)
            
            result[symbol] = {
                'symbol': symbol,
                'last_price': ticker['last'],
                'bid_price': ticker['bid'],
                'ask_price': ticker['ask'],
                'volume': ticker['baseVolume'],
                'high': ticker['high'],
                'low': ticker['low'],
                'open': ticker['open'],
                'change_pct': ticker['percentage'],
                'timestamp': pd.Timestamp.now(tz='UTC')
            }
        
        return result
    
    def subscribe_quote(
        self,
        symbols: List[str],
        callback: Callable[[Dict], None]
    ) -> bool:
        """
        订阅实时行情
        
        Args:
            symbols: 交易对列表
            callback: 回调函数
            
        Returns:
            bool: 是否订阅成功
        """
        print(f"⚠ 加密货币WebSocket订阅功能待实现")
        print(f"💡 建议使用定时轮询get_realtime_data()方法")
        return False
    
    def unsubscribe_quote(self, symbols: List[str]) -> bool:
        """
        取消订阅
        
        Args:
            symbols: 交易对列表
            
        Returns:
            bool: 是否取消成功
        """
        return True
    
    # ==================== 交易接口 ====================
    
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
            dict: 订单信息
        """
        if not self.is_connected():
            print("❌ 未连接到交易所")
            return {}
        
        try:
            if self.provider == 'binance':
                return self._place_order_binance(symbol, side, quantity, price, order_type)
            elif self.provider == 'ccxt':
                return self._place_order_ccxt(symbol, side, quantity, price, order_type)
            else:
                return {}
        except Exception as e:
            print(f"❌ 下单失败: {e}")
            return {}
    
    def _place_order_binance(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float],
        order_type: str
    ) -> Dict:
        """使用Binance下单"""
        if not self.client:
            return {}
        
        try:
            from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET  # type: ignore
        except ImportError:
            print("❌ 请安装 python-binance: pip install python-binance")
            return {}
        
        binance_side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL
        
        if order_type.lower() == 'limit' and price:
            order = self.client.create_order(
                symbol=symbol,
                side=binance_side,
                type=ORDER_TYPE_LIMIT,
                timeInForce='GTC',
                quantity=quantity,
                price=str(price)
            )
        else:  # market
            order = self.client.create_order(
                symbol=symbol,
                side=binance_side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
        
        return {
            'order_id': str(order['orderId']),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'status': order['status'],
            'timestamp': pd.Timestamp.now(tz='UTC')
        }
    
    def _place_order_ccxt(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float],
        order_type: str
    ) -> Dict:
        """使用CCXT下单"""
        if not self.exchange:
            return {}
        
        # 转换symbol格式
        symbol_ccxt = symbol
        if '/' not in symbol:
            for quote in ['USDT', 'BUSD', 'BTC', 'ETH']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    symbol_ccxt = f"{base}/{quote}"
                    break
        
        if order_type.lower() == 'limit' and price:
            order = self.exchange.create_limit_order(symbol_ccxt, side.lower(), quantity, price)
        else:
            order = self.exchange.create_market_order(symbol_ccxt, side.lower(), quantity)
        
        return {
            'order_id': str(order['id']),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'status': order['status'],
            'timestamp': pd.Timestamp.now(tz='UTC')
        }
    
    def cancel_order(self, order_id: str, symbol: str = '') -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            
        Returns:
            bool: 是否撤单成功
        """
        if not self.is_connected():
            return False
        
        try:
            if self.provider == 'binance' and self.client:
                self.client.cancel_order(symbol=symbol, orderId=order_id)
            elif self.provider == 'ccxt' and self.exchange:
                self.exchange.cancel_order(order_id, symbol if symbol else None)
            
            print(f"✓ 订单 {order_id} 已撤销")
            return True
        except Exception as e:
            print(f"❌ 撤单失败: {e}")
            return False
    
    def get_order_status(self, order_id: str, symbol: str = '') -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            
        Returns:
            dict: 订单详情
        """
        if not self.is_connected():
            return {}
        
        try:
            if self.provider == 'binance' and self.client:
                order = self.client.get_order(symbol=symbol, orderId=order_id)
                return {
                    'order_id': str(order['orderId']),
                    'symbol': order['symbol'],
                    'status': order['status'],
                    'type': order['type'],
                    'side': order['side'],
                    'price': float(order['price']),
                    'volume': float(order['origQty']),
                    'filled': float(order['executedQty']),
                    'avg_price': float(order.get('avgPrice', 0))
                }
            elif self.provider == 'ccxt' and self.exchange:
                order = self.exchange.fetch_order(order_id, symbol)
                return {
                    'order_id': str(order['id']),
                    'symbol': order['symbol'],
                    'status': order['status'],
                    'type': order['type'],
                    'side': order['side'],
                    'price': order['price'],
                    'volume': order['amount'],
                    'filled': order['filled'],
                    'avg_price': order.get('average', 0)
                }
        except Exception as e:
            print(f"❌ 查询订单失败: {e}")
        
        return {}
    
    # ==================== 账户接口 ====================
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            dict: 账户信息
        """
        if not self.is_connected():
            return {}
        
        try:
            if self.provider == 'binance' and self.client:
                account = self.client.get_account()  # type: ignore
                
                # 计算总资产(USDT)
                total_value = 0
                balances = []
                
                for balance in account['balances']:
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    total = free + locked
                    
                    if total > 0:
                        balances.append({
                            'asset': balance['asset'],
                            'free': free,
                            'locked': locked,
                            'total': total
                        })
                
                return {
                    'account_type': 'SPOT',
                    'balances': balances,
                    'can_trade': account['canTrade'],
                    'can_withdraw': account['canWithdraw'],
                    'can_deposit': account['canDeposit']
                }
                
            elif self.provider == 'ccxt' and self.exchange:
                balance = self.exchange.fetch_balance()
                
                balances = []
                for currency, amounts in balance['total'].items():
                    if amounts > 0:
                        balances.append({
                            'asset': currency,
                            'free': balance['free'].get(currency, 0),
                            'locked': balance['used'].get(currency, 0),
                            'total': amounts
                        })
                
                return {
                    'account_type': 'SPOT',
                    'balances': balances
                }
        except Exception as e:
            print(f"❌ 获取账户信息失败: {e}")
        
        return {}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取持仓信息(现货即余额)
        
        Returns:
            list: 持仓列表
        """
        account = self.get_account_info()
        return account.get('balances', [])
    
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
            list: 成交记录
        """
        if not self.is_connected():
            return []
        
        print("⚠ 加密货币成交历史查询功能待完善")
        return []
    
    # ==================== 市场特有接口 ====================
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化交易对代码
        
        Args:
            symbol: 原始代码,如'BTCUSDT'
            
        Returns:
            str: 标准化代码,如'CRYPTO.BTC.USDT'
        """
        return DataNormalizer.normalize_symbol(symbol, self.market_type)
    
    def get_trading_calendar(self, start: str, end: str) -> List[date]:
        """
        获取交易日历(加密货币7x24小时交易)
        
        Args:
            start: 开始日期
            end: 结束日期
            
        Returns:
            list: 所有日期都是交易日
        """
        start_date = datetime.strptime(start, '%Y%m%d').date()
        end_date = datetime.strptime(end, '%Y%m%d').date()
        
        trading_days = []
        current = start_date
        while current <= end_date:
            trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days
    
    def get_market_hours(self) -> List[tuple]:
        """
        获取交易时间段(24/7)
        
        Returns:
            list: [('00:00:00', '23:59:59')]
        """
        return [('00:00:00', '23:59:59')]
    
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
            side: 方向
            
        Returns:
            dict: 费用详情
        """
        trade_cost = self.config.get('backtest', {}).get('trade_cost', {})
        
        # 默认使用taker费率
        fee_rate = trade_cost.get('taker_fee_rate', 0.001)
        
        # 如果使用BNB抵扣,可享受折扣
        bnb_discount = trade_cost.get('bnb_discount', 1.0)
        
        commission = price * quantity * fee_rate * bnb_discount
        
        return {
            'commission': commission,
            'fee_rate': fee_rate,
            'total': commission
        }
    
    def get_symbols(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取可交易的交易对列表
        
        Args:
            category: 分类(如'USDT', 'BTC')
            
        Returns:
            list: 交易对信息列表
        """
        if not self.is_connected():
            return []
        
        try:
            if self.provider == 'binance' and self.client:
                exchange_info = self.client.get_exchange_info()  # type: ignore
                
                symbols = []
                for s in exchange_info['symbols']:
                    if s['status'] == 'TRADING':
                        if category and not s['symbol'].endswith(category):
                            continue
                        
                        symbols.append({
                            'symbol': s['symbol'],
                            'base_asset': s['baseAsset'],
                            'quote_asset': s['quoteAsset'],
                            'status': s['status'],
                            'min_qty': float(s['filters'][1]['minQty']) if len(s['filters']) > 1 else 0,
                            'min_notional': float(s['filters'][2]['minNotional']) if len(s['filters']) > 2 else 0
                        })
                
                return symbols
                
            elif self.provider == 'ccxt' and self.exchange:
                markets = self.exchange.load_markets()  # type: ignore
                
                symbols = []
                for symbol, market in markets.items():
                    if market['active']:
                        if category and not symbol.endswith(f'/{category}'):
                            continue
                        
                        symbols.append({
                            'symbol': symbol,
                            'base_asset': market['base'],
                            'quote_asset': market['quote'],
                            'status': 'TRADING',
                            'min_qty': market['limits']['amount']['min'] if market['limits']['amount'] else 0
                        })
                
                return symbols
        except Exception as e:
            print(f"❌ 获取交易对列表失败: {e}")
        
        return []
    
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
        import os
        
        # 默认保存目录
        save_dir = './crypto_data'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        success_count = 0
        for symbol in symbols:
            try:
                df = self.get_market_data([symbol], period, start, end)
                if not df.empty:
                    filename = f"{symbol}_{period}_{start}_{end}.csv"
                    filepath = os.path.join(save_dir, filename)
                    df.to_csv(filepath, index=False)
                    print(f"✓ {symbol} 数据已保存到 {filepath}")
                    success_count += 1
            except Exception as e:
                print(f"❌ {symbol} 下载失败: {e}")
        
        print(f"\n共下载 {success_count}/{len(symbols)} 个交易对的数据")
        return success_count > 0
