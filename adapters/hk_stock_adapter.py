#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场适配器
支持通过富途OpenAPI获取港股数据和交易
"""

from typing import List, Dict, Optional, Union, Callable, Any
from datetime import datetime, time, date, timedelta
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
        # 香港假日
        try:
            self.hk_holidays = holidays.country_holidays('HK')
        except Exception:
            # 如果无法获取香港假日，使用空集合
            self.hk_holidays = set()
        
        self.provider = config.get('data_provider', 'futu')
        self.api_client = None
        self.connected = False
        
        # 手数缓存
        self.lot_size_cache = {}
        
        # 行情上下文和交易上下文
        self.quote_ctx = None
        self.trade_ctx = None
    
    def connect(self) -> bool:
        """连接到富途OpenD"""
        try:
            # 需要安装 futu-api
            # pip install futu-api
            from futu import OpenQuoteContext, OpenSecTradeContext  # type: ignore
            
            host = self.config.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.get('data_source', {}).get('port', 11111)
            
            # 创建行情连接
            self.quote_ctx = OpenQuoteContext(host=host, port=port)
            
            # 测试连接
            ret, data = self.quote_ctx.get_market_state(['HK.00700'])
            if ret != 0:
                raise ConnectionError(f"Failed to connect: {data}")
            
            self.connected = True
            print(f"✓ Connected to Futu OpenD at {host}:{port}")
            return True
            
        except ImportError:
            raise ImportError("futu-api not installed. Run: pip install futu-api")
        except Exception as e:
            print(f"✗ Failed to connect to Futu: {e}")
            raise ConnectionError(f"Futu connection failed: {e}")
    
    def disconnect(self) -> bool:
        """断开连接"""
        if hasattr(self, 'quote_ctx') and self.quote_ctx is not None:
            self.quote_ctx.close()
        if hasattr(self, 'trade_ctx') and self.trade_ctx is not None:
            self.trade_ctx.close()
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_market_info(self) -> Dict[str, Any]:
        """获取市场基本信息"""
        return {
            'market_type': self.market_type,
            'market_name': '港股市场',
            'trading_hours': [
                (self.MORNING_OPEN.strftime('%H:%M:%S'), self.MORNING_CLOSE.strftime('%H:%M:%S')),
                (self.AFTERNOON_OPEN.strftime('%H:%M:%S'), self.AFTERNOON_CLOSE.strftime('%H:%M:%S'))
            ],
            'timezone': 'Asia/Hong_Kong',
            'currency': 'HKD',
            'tick_size': 'variable',  # 港股价格档位不固定
            'lot_size': 'variable',  # 每手股数不固定
            'price_limit': None,  # 港股无涨跌停限制
            't_plus': 2  # T+2交易
        }
    
    def get_market_type(self) -> str:
        """获取市场类型"""
        return self.market_type
    
    def get_market_data(
        self,
        symbols: Union[str, List[str]],
        period: str = '1d',
        start: Optional[str] = None,
        end: Optional[str] = None,
        fields: Optional[List[str]] = None,
        dividend_type: str = 'none'
    ) -> pd.DataFrame:
        """获取历史行情数据"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        # 标准化symbol
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # 实现Futu API数据获取
        from futu import KLType, AuType, SubType  # type: ignore
        
        # 映射周期
        period_map = {
            '1m': KLType.K_1M,
            '5m': KLType.K_5M,
            '15m': KLType.K_15M,
            '30m': KLType.K_30M,
            '60m': KLType.K_60M,
            '1h': KLType.K_60M,
            '1d': KLType.K_DAY,
            'd': KLType.K_DAY,
            '1w': KLType.K_WEEK,
            'w': KLType.K_WEEK,
        }
        
        ktype = period_map.get(period, KLType.K_DAY)
        
        # 映射复权类型
        autype_map = {
            'none': AuType.QFQ,  # 前复权
            'front': AuType.QFQ,
            'back': AuType.HFQ,  # 后复权
        }
        autype = autype_map.get(dividend_type, AuType.QFQ)
        
        all_data = []
        
        for symbol in symbols:
            try:
                # 获取历史K线
                ret, data = self.quote_ctx.request_history_kline(
                    symbol,
                    start=start,
                    end=end,
                    ktype=ktype,
                    autype=autype,
                    fields=['code', 'time_key', 'open', 'close', 'high', 'low', 'volume', 'turnover']
                )
                
                if ret == 0 and data is not None and not data.empty:
                    # 添加symbol列
                    data['symbol'] = symbol
                    all_data.append(data)
                else:
                    print(f"Warning: Failed to get data for {symbol}: {data}")
                    
            except Exception as e:
                print(f"Error getting data for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # 合并所有数据
        df = pd.concat(all_data, ignore_index=True)
        
        # 标准化列名
        df = df.rename(columns={
            'code': 'symbol',
            'time_key': 'time',
            'turnover': 'amount'
        })
        
        # 使用DataNormalizer标准化数据
        df = DataNormalizer.normalize_dataframe(df, self.market_type)
        
        # 筛选字段
        if fields:
            available_fields = [f for f in fields if f in df.columns]
            df = df[['symbol', 'time'] + available_fields]
        
        return df
    
    def get_realtime_data(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取实时行情"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # 获取快照数据
        ret, data = self.quote_ctx.get_market_snapshot(symbols)
        
        if ret != 0:
            raise RuntimeError(f"Failed to get realtime data: {data}")
        
        if data is None or data.empty:
            return pd.DataFrame()
        
        # 标准化列名
        df = data.rename(columns={
            'code': 'symbol',
            'update_time': 'time',
            'last_price': 'close',
            'open_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'turnover': 'amount'
        })
        
        # 使用DataNormalizer标准化数据
        df = DataNormalizer.normalize_dataframe(df, self.market_type)
        
        # 筛选字段
        if fields:
            available_fields = [f for f in fields if f in df.columns]
            df = df[['symbol', 'time'] + available_fields]
        
        return df
    
    def subscribe_quote(
        self,
        symbols: Union[str, List[str]],
        callback: Callable
    ) -> bool:
        """订阅实时行情"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if isinstance(symbols, str):
            symbols = [symbols]
        
        from futu import SubType  # type: ignore
        
        try:
            # 订阅行情
            ret, data = self.quote_ctx.subscribe(symbols, [SubType.QUOTE], subscribe_push=True)
            if ret != 0:
                print(f"Failed to subscribe: {data}")
                return False
            
            # 设置回调
            self.quote_ctx.set_handler(callback)
            
            print(f"Successfully subscribed to {len(symbols)} symbols")
            return True
            
        except Exception as e:
            print(f"Error subscribing to quotes: {e}")
            return False
    
    def unsubscribe_quote(self, symbols: Union[str, List[str]]) -> bool:
        """取消订阅"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if isinstance(symbols, str):
            symbols = [symbols]
        
        from futu import SubType  # type: ignore
        
        try:
            # 取消订阅
            ret, data = self.quote_ctx.unsubscribe(symbols, [SubType.QUOTE])
            if ret != 0:
                print(f"Failed to unsubscribe: {data}")
                return False
            
            print(f"Successfully unsubscribed from {len(symbols)} symbols")
            return True
            
        except Exception as e:
            print(f"Error unsubscribing from quotes: {e}")
            return False
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = 'limit'
    ) -> Dict[str, Any]:
        """下单"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        # 需要创建交易连接
        if self.trade_ctx is None:
            from futu import OpenSecTradeContext  # type: ignore
            host = self.config.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.get('data_source', {}).get('port', 11111)
            self.trade_ctx = OpenSecTradeContext(host=host, port=port)
        
        from futu import TrdSide, OrderType, TrdMarket  # type: ignore
        
        # 映射买卖方向
        trd_side = TrdSide.BUY if side.lower() == 'buy' else TrdSide.SELL
        
        # 映射订单类型
        order_type_map = {
            'limit': OrderType.NORMAL,  # 限价单
            'market': OrderType.MARKET,  # 市价单
        }
        futu_order_type = order_type_map.get(order_type.lower(), OrderType.NORMAL)
        
        try:
            # 下单
            ret, data = self.trade_ctx.place_order(
                price=price if price else 0.0,
                qty=int(quantity),
                code=symbol,
                trd_side=trd_side,
                order_type=futu_order_type,
                trd_env=self.config.get('trade_env', 1),  # 1=真实环境, 0=仿真环境
            )
            
            if ret != 0:
                raise RuntimeError(f"Failed to place order: {data}")
            
            # 返回订单信息
            return {
                'order_id': str(data['order_id'].iloc[0]) if not data.empty else '',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'status': 'submitted',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error placing order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if self.trade_ctx is None:
            raise RuntimeError("Trade context not initialized")
        
        try:
            # 撤销订单
            ret, data = self.trade_ctx.modify_order(
                modify_order_op=0,  # 0=撤单
                order_id=int(order_id),
                qty=0,
                price=0.0,
                trd_env=self.config.get('trade_env', 1)
            )
            
            if ret != 0:
                print(f"Failed to cancel order: {data}")
                return False
            
            print(f"Successfully cancelled order {order_id}")
            return True
            
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if self.trade_ctx is None:
            raise RuntimeError("Trade context not initialized")
        
        try:
            # 查询订单
            ret, data = self.trade_ctx.order_list_query(
                trd_env=self.config.get('trade_env', 1)
            )
            
            if ret != 0:
                raise RuntimeError(f"Failed to query orders: {data}")
            
            # 查找匹配的订单
            order_data = data[data['order_id'] == int(order_id)]
            
            if order_data.empty:
                return {'order_id': order_id, 'status': 'not_found'}
            
            order = order_data.iloc[0]
            
            return {
                'order_id': str(order['order_id']),
                'symbol': order['code'],
                'side': 'buy' if order['trd_side'] == 'BUY' else 'sell',
                'quantity': order['qty'],
                'price': order['price'],
                'status': order['order_status'],
                'filled_quantity': order.get('dealt_qty', 0),
                'filled_avg_price': order.get('dealt_avg_price', 0),
                'timestamp': str(order['create_time'])
            }
            
        except Exception as e:
            print(f"Error getting order status: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if self.trade_ctx is None:
            from futu import OpenSecTradeContext  # type: ignore
            host = self.config.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.get('data_source', {}).get('port', 11111)
            self.trade_ctx = OpenSecTradeContext(host=host, port=port)
        
        try:
            # 查询账户资产
            ret, data = self.trade_ctx.accinfo_query(
                trd_env=self.config.get('trade_env', 1)
            )
            
            if ret != 0:
                raise RuntimeError(f"Failed to query account info: {data}")
            
            if data.empty:
                return {}
            
            account = data.iloc[0]
            
            return {
                'account_id': str(account.get('acc_id', '')),
                'balance': float(account.get('total_assets', 0)),
                'available_cash': float(account.get('cash', 0)),
                'market_value': float(account.get('market_val', 0)),
                'currency': 'HKD',
                'power': float(account.get('power', 0)),
                'frozen_cash': float(account.get('frozen_cash', 0)),
            }
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            raise
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if self.trade_ctx is None:
            from futu import OpenSecTradeContext  # type: ignore
            host = self.config.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.get('data_source', {}).get('port', 11111)
            self.trade_ctx = OpenSecTradeContext(host=host, port=port)
        
        try:
            # 查询持仓
            ret, data = self.trade_ctx.position_list_query(
                trd_env=self.config.get('trade_env', 1)
            )
            
            if ret != 0:
                raise RuntimeError(f"Failed to query positions: {data}")
            
            if data.empty:
                return []
            
            positions = []
            for _, row in data.iterrows():
                positions.append({
                    'symbol': row['code'],
                    'quantity': float(row['qty']),
                    'available_quantity': float(row.get('can_sell_qty', 0)),
                    'avg_price': float(row['cost_price']),
                    'market_price': float(row.get('last_price', 0)),
                    'profit_loss': float(row.get('pl_val', 0)),
                    'profit_loss_ratio': float(row.get('pl_ratio', 0)),
                    'market_value': float(row.get('market_val', 0)),
                })
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            raise
    
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
        start: str,
        end: str
    ) -> List[date]:
        """获取交易日历"""
        start_date = datetime.strptime(start, '%Y%m%d').date()
        end_date = datetime.strptime(end, '%Y%m%d').date()
        
        trading_days = []
        current = start_date
        
        while current <= end_date:
            # 检查是否为交易日
            if current.weekday() < 5 and current not in self.hk_holidays:
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
        commission_rate = self.config.get('backtest', {}).get(
            'trade_cost', {}
        ).get('commission_rate', 0.0025)
        min_commission = self.config.get('backtest', {}).get(
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
        
        # 从 Futu API 查询实际手数
        if self.is_connected() and self.quote_ctx is not None:
            try:
                ret, data = self.quote_ctx.get_stock_basicinfo(
                    market='HK',
                    stock_code=symbol
                )
                
                if ret == 0 and data is not None and not data.empty:
                    lot_size = int(data.iloc[0]['lot_size'])
                    self.lot_size_cache[symbol] = lot_size
                    return lot_size
                    
            except Exception as e:
                print(f"Warning: Failed to get lot size for {symbol}: {e}")
        
        # 使用默认值
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
        # 使用更严格的浮点数比较，将价格和tick都转换为最小单位的整数
        price_ticks = round(price / tick_size)
        expected_price = price_ticks * tick_size
        return abs(price - expected_price) < tick_size * 0.01  # 1%误差容忍
    
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
    
    def get_market_hours(self) -> List[tuple]:
        """
        获取交易时间段
        
        Returns:
            list[tuple]: 时间段列表,每个元组为(开始时间, 结束时间)
        """
        return [
            (self.MORNING_OPEN.strftime('%H:%M:%S'), self.MORNING_CLOSE.strftime('%H:%M:%S')),
            (self.AFTERNOON_OPEN.strftime('%H:%M:%S'), self.AFTERNOON_CLOSE.strftime('%H:%M:%S'))
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
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        if self.trade_ctx is None:
            from futu import OpenSecTradeContext  # type: ignore
            host = self.config.get('data_source', {}).get('host', '127.0.0.1')
            port = self.config.get('data_source', {}).get('port', 11111)
            self.trade_ctx = OpenSecTradeContext(host=host, port=port)
        
        try:
            # 查询成交记录
            ret, data = self.trade_ctx.deal_list_query(
                trd_env=self.config.get('trade_env', 1)
            )
            
            if ret != 0:
                print(f"Failed to query trade history: {data}")
                return []
            
            if data.empty:
                return []
            
            # 过滤日期范围
            if start:
                start_date = datetime.strptime(start, '%Y%m%d')
                data = data[pd.to_datetime(data['create_time']) >= start_date]
            
            if end:
                end_date = datetime.strptime(end, '%Y%m%d')
                data = data[pd.to_datetime(data['create_time']) <= end_date]
            
            # 转换为字典列表
            trades = []
            for _, row in data.iterrows():
                trades.append({
                    'trade_id': str(row['deal_id']),
                    'order_id': str(row['order_id']),
                    'symbol': row['code'],
                    'side': 'buy' if row['trd_side'] == 'BUY' else 'sell',
                    'quantity': float(row['qty']),
                    'price': float(row['price']),
                    'amount': float(row.get('amt', 0)),
                    'timestamp': str(row['create_time'])
                })
            
            return trades
            
        except Exception as e:
            print(f"Error getting trade history: {e}")
            return []
    
    def get_symbols(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取标的列表"""
        if not self.is_connected():
            raise ConnectionError("Not connected to Futu OpenD")
        
        from futu import Market  # type: ignore
        
        try:
            # 获取港股列表
            ret, data = self.quote_ctx.get_stock_basicinfo(
                market=Market.HK,
                stock_type=category if category else None
            )
            
            if ret != 0:
                print(f"Failed to get symbols: {data}")
                return []
            
            if data.empty:
                return []
            
            # 转换为字典列表
            symbols = []
            for _, row in data.iterrows():
                symbols.append({
                    'symbol': row['code'],
                    'name': row['name'],
                    'category': row.get('stock_type', ''),
                    'exchange': 'HKEX',
                    'lot_size': int(row.get('lot_size', 100))
                })
            
            return symbols
            
        except Exception as e:
            print(f"Error getting symbols: {e}")
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
            data_dir = self.config.get('data_dir', './data/hk_stock')
            os.makedirs(data_dir, exist_ok=True)
            
            # 保存数据
            for symbol in symbols:
                symbol_data = df[df['symbol'] == symbol]
                if not symbol_data.empty:
                    filename = f"{symbol.replace('.', '_')}_{period}_{start}_{end}.csv"
                    filepath = os.path.join(data_dir, filename)
                    symbol_data.to_csv(filepath, index=False)
                    print(f"Saved {symbol} data to {filepath}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading history data: {e}")
            return False
