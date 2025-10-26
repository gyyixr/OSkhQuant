# coding: utf-8
"""
多市场适配器模块
支持A股、美股、港股、加密货币等多个市场的统一数据和交易接口
"""

from .base_adapter import BaseMarketAdapter
from .market_registry import MarketRegistry, register_adapter
from .data_normalizer import DataNormalizer
from .china_a_stock_adapter import ChinaAStockAdapter

# 导入其他市场适配器(可选)
try:
    from .us_stock_adapter import USStockAdapter
except ImportError:
    USStockAdapter = None

try:
    from .hk_stock_adapter import HKStockAdapter
except ImportError:
    HKStockAdapter = None

try:
    from .crypto_adapter import CryptoAdapter
except ImportError:
    CryptoAdapter = None

__all__ = [
    'BaseMarketAdapter',
    'MarketRegistry',
    'register_adapter',
    'DataNormalizer',
    'ChinaAStockAdapter',
    'USStockAdapter',
    'HKStockAdapter',
    'CryptoAdapter'
]
