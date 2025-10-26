# coding: utf-8
"""
数据标准化模块
负责不同市场之间的数据格式标准化
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import pytz
import re


class DataNormalizer:
    """
    数据标准化工具类
    统一不同市场的数据格式
    """
    
    # 市场前缀映射
    MARKET_PREFIXES = {
        'china_a_stock': 'CN',
        'us_stock': 'US',
        'hk_stock': 'HK',
        'cryptocurrency': 'CRYPTO'
    }
    
    # 时区映射
    MARKET_TIMEZONES = {
        'china_a_stock': 'Asia/Shanghai',      # UTC+8
        'us_stock': 'America/New_York',         # EST/EDT
        'hk_stock': 'Asia/Hong_Kong',          # UTC+8
        'cryptocurrency': 'UTC'                 # UTC
    }
    
    # 标准字段映射
    STANDARD_FIELDS = {
        'symbol': 'symbol',
        'timestamp': 'timestamp',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'amount': 'amount',
        'bid_price': 'bid_price',
        'ask_price': 'ask_price'
    }
    
    @classmethod
    def normalize_symbol(cls, symbol: str, market_type: str) -> str:
        """
        标准化标的代码
        
        Args:
            symbol: 原始代码
            market_type: 市场类型
            
        Returns:
            str: 标准化后的代码
            
        Examples:
            normalize_symbol('000001.SZ', 'china_a_stock') -> 'CN.000001.SZ'
            normalize_symbol('AAPL', 'us_stock') -> 'US.AAPL'
            normalize_symbol('00700', 'hk_stock') -> 'HK.00700'
            normalize_symbol('BTCUSDT', 'cryptocurrency') -> 'CRYPTO.BTC.USDT'
        """
        if market_type not in cls.MARKET_PREFIXES:
            raise ValueError(f"不支持的市场类型: {market_type}")
        
        prefix = cls.MARKET_PREFIXES[market_type]
        
        # 如果已经有市场前缀,直接返回
        if symbol.startswith(f"{prefix}."):
            return symbol
        
        # 特殊处理加密货币交易对
        if market_type == 'cryptocurrency':
            # 处理类似 BTCUSDT 的格式
            if 'USDT' in symbol.upper():
                # 分离基础币种和计价币种
                base = symbol.replace('USDT', '').replace('usdt', '')
                quote = 'USDT'
                return f"{prefix}.{base.upper()}.{quote}"
            elif 'BTC' in symbol.upper() and symbol.upper() != 'BTC':
                base = symbol.replace('BTC', '').replace('btc', '')
                quote = 'BTC'
                return f"{prefix}.{base.upper()}.{quote}"
        
        # 添加市场前缀
        return f"{prefix}.{symbol}"
    
    @classmethod
    def denormalize_symbol(cls, symbol: str) -> str:
        """
        反标准化标的代码(去除市场前缀)
        
        Args:
            symbol: 标准化代码
            
        Returns:
            str: 原始代码
            
        Examples:
            denormalize_symbol('CN.000001.SZ') -> '000001.SZ'
            denormalize_symbol('US.AAPL') -> 'AAPL'
            denormalize_symbol('CRYPTO.BTC.USDT') -> 'BTCUSDT'
        """
        # 检查是否包含市场前缀
        for prefix in cls.MARKET_PREFIXES.values():
            if symbol.startswith(f"{prefix}."):
                rest = symbol[len(prefix)+1:]  # 去掉 "PREFIX."
                
                # 特殊处理加密货币
                if prefix == 'CRYPTO' and '.' in rest:
                    parts = rest.split('.')
                    return f"{parts[0]}{parts[1]}"  # BTC.USDT -> BTCUSDT
                
                return rest
        
        # 如果没有前缀,直接返回
        return symbol
    
    @classmethod
    def extract_market_type(cls, symbol: str) -> str:
        """
        从标准化代码中提取市场类型
        
        Args:
            symbol: 标准化代码
            
        Returns:
            str: 市场类型
            
        Raises:
            ValueError: 如果无法识别市场类型
        """
        for market_type, prefix in cls.MARKET_PREFIXES.items():
            if symbol.startswith(f"{prefix}."):
                return market_type
        
        raise ValueError(f"无法从代码 {symbol} 中识别市场类型")
    
    @classmethod
    def normalize_timestamp(
        cls,
        timestamp: Any,
        market_type: str,
        to_utc: bool = True
    ) -> datetime:
        """
        标准化时间戳
        
        Args:
            timestamp: 时间戳(可以是datetime、字符串或数字)
            market_type: 市场类型
            to_utc: 是否转换为UTC时间
            
        Returns:
            datetime: 标准化后的时间对象
        """
        # 转换为datetime对象
        if isinstance(timestamp, str):
            # 尝试多种格式
            for fmt in ['%Y%m%d%H%M%S', '%Y-%m-%d %H:%M:%S', '%Y%m%d']:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"无法解析时间字符串: {timestamp}")
        elif isinstance(timestamp, (int, float)):
            # 时间戳转换
            if timestamp > 1e10:  # 毫秒级
                timestamp = timestamp / 1000
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            raise TypeError(f"不支持的时间类型: {type(timestamp)}")
        
        # 添加时区信息
        if dt.tzinfo is None:
            tz_name = cls.MARKET_TIMEZONES.get(market_type, 'UTC')
            tz = pytz.timezone(tz_name)
            dt = tz.localize(dt)
        
        # 转换为UTC
        if to_utc:
            dt = dt.astimezone(pytz.UTC)
        
        return dt
    
    @classmethod
    def denormalize_timestamp(
        cls,
        timestamp: datetime,
        market_type: str,
        output_format: str = '%Y%m%d%H%M%S'
    ) -> str:
        """
        将UTC时间转换为市场本地时间字符串
        
        Args:
            timestamp: UTC时间对象
            market_type: 市场类型
            output_format: 输出格式
            
        Returns:
            str: 本地时间字符串
        """
        tz_name = cls.MARKET_TIMEZONES.get(market_type, 'UTC')
        tz = pytz.timezone(tz_name)
        
        # 转换为本地时区
        local_dt = timestamp.astimezone(tz)
        
        return local_dt.strftime(output_format)
    
    @classmethod
    def map_fields(
        cls,
        data: Dict[str, Any],
        field_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        根据字段映射转换数据字段
        
        Args:
            data: 原始数据字典
            field_mapping: 字段映射,{原始字段名: 标准字段名}
            
        Returns:
            dict: 标准化后的数据字典
            
        Example:
            原始数据: {'stock_code': '000001', 'price': 10.5}
            映射: {'stock_code': 'symbol', 'price': 'close'}
            结果: {'symbol': '000001', 'close': 10.5}
        """
        normalized = {}
        
        for orig_field, value in data.items():
            # 查找映射
            std_field = field_mapping.get(orig_field, orig_field)
            normalized[std_field] = value
        
        return normalized
    
    @classmethod
    def get_market_field_mapping(cls, market_type: str) -> Dict[str, str]:
        """
        获取特定市场的字段映射
        
        Args:
            market_type: 市场类型
            
        Returns:
            dict: {原始字段: 标准字段}
        """
        # A股字段映射(基于miniQMT)
        if market_type == 'china_a_stock':
            return {
                'stock_code': 'symbol',
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'amount': 'amount',
                'bidPrice': 'bid_price',
                'askPrice': 'ask_price'
            }
        
        # 美股字段映射
        elif market_type == 'us_stock':
            return {
                'symbol': 'symbol',
                'timestamp': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'bid': 'bid_price',
                'ask': 'ask_price'
            }
        
        # 港股字段映射
        elif market_type == 'hk_stock':
            return {
                'code': 'symbol',
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'turnover': 'amount',
                'bid': 'bid_price',
                'ask': 'ask_price'
            }
        
        # 加密货币字段映射
        elif market_type == 'cryptocurrency':
            return {
                'symbol': 'symbol',
                'timestamp': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'quote_volume': 'amount',
                'bid': 'bid_price',
                'ask': 'ask_price'
            }
        
        # 默认返回标准映射
        return cls.STANDARD_FIELDS.copy()
    
    @classmethod
    def validate_symbol_format(cls, symbol: str, market_type: str) -> bool:
        """
        验证标的代码格式是否符合市场规范
        
        Args:
            symbol: 标的代码
            market_type: 市场类型
            
        Returns:
            bool: 是否有效
        """
        # A股格式: 6位数字 + .SH/.SZ
        if market_type == 'china_a_stock':
            pattern = r'^\d{6}\.(SH|SZ)$'
            return bool(re.match(pattern, symbol))
        
        # 美股格式: 1-5个大写字母
        elif market_type == 'us_stock':
            pattern = r'^[A-Z]{1,5}$'
            return bool(re.match(pattern, symbol))
        
        # 港股格式: 5位数字
        elif market_type == 'hk_stock':
            pattern = r'^\d{5}$'
            return bool(re.match(pattern, symbol))
        
        # 加密货币格式: 基础币种+计价币种
        elif market_type == 'cryptocurrency':
            # 简单验证:包含常见计价币种
            return any(quote in symbol.upper() for quote in ['USDT', 'BTC', 'ETH', 'USDC'])
        
        return False
