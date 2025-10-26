# coding: utf-8
"""
多市场适配器模块
支持A股、美股、港股、加密货币等多个市场的统一数据和交易接口
"""

from .base_adapter import BaseMarketAdapter
from .market_registry import MarketRegistry, register_adapter
from .data_normalizer import DataNormalizer
from .china_a_stock_adapter import ChinaAStockAdapter

__all__ = [
    'BaseMarketAdapter',
    'MarketRegistry',
    'register_adapter',
    'DataNormalizer',
    'ChinaAStockAdapter'
]
