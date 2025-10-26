# coding: utf-8
"""
市场注册中心
管理所有市场适配器的注册、查找和切换
"""

from typing import Dict, Type, Optional
from .base_adapter import BaseMarketAdapter


class MarketRegistry:
    """
    市场注册中心
    单例模式,管理所有市场适配器
    """
    
    _instance = None
    _adapters: Dict[str, Type[BaseMarketAdapter]] = {}
    _adapter_instances: Dict[str, BaseMarketAdapter] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, market_type: str, adapter_class: Type[BaseMarketAdapter]):
        """
        注册市场适配器
        
        Args:
            market_type: 市场类型标识,如'china_a_stock', 'us_stock'
            adapter_class: 适配器类(非实例)
        """
        if not issubclass(adapter_class, BaseMarketAdapter):
            raise TypeError(f"{adapter_class}必须继承自BaseMarketAdapter")
        
        cls._adapters[market_type] = adapter_class
        print(f"✓ 已注册市场适配器: {market_type} -> {adapter_class.__name__}")
    
    @classmethod
    def unregister(cls, market_type: str):
        """
        注销市场适配器
        
        Args:
            market_type: 市场类型标识
        """
        if market_type in cls._adapters:
            del cls._adapters[market_type]
            print(f"✓ 已注销市场适配器: {market_type}")
        
        # 同时清理实例
        if market_type in cls._adapter_instances:
            adapter = cls._adapter_instances[market_type]
            if adapter.is_connected():
                adapter.disconnect()
            del cls._adapter_instances[market_type]
    
    @classmethod
    def get_adapter(
        cls,
        market_type: str,
        config: Optional[Dict] = None,
        force_new: bool = False
    ) -> BaseMarketAdapter:
        """
        获取市场适配器实例
        
        Args:
            market_type: 市场类型标识
            config: 配置字典,如果为None则使用已有实例的配置
            force_new: 是否强制创建新实例
            
        Returns:
            BaseMarketAdapter: 适配器实例
            
        Raises:
            ValueError: 如果市场类型未注册
        """
        if market_type not in cls._adapters:
            available = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"未注册的市场类型: {market_type}\n"
                f"可用市场: {available if available else '无'}"
            )
        
        # 如果不强制创建新实例,且已有实例,则返回已有实例
        if not force_new and market_type in cls._adapter_instances:
            return cls._adapter_instances[market_type]
        
        # 创建新实例
        if config is None:
            config = {}
        
        adapter_class = cls._adapters[market_type]
        adapter_instance = adapter_class(config)
        
        # 缓存实例
        cls._adapter_instances[market_type] = adapter_instance
        
        return adapter_instance
    
    @classmethod
    def get_adapter_class(cls, market_type: str) -> Type[BaseMarketAdapter]:
        """
        获取适配器类(非实例)
        
        Args:
            market_type: 市场类型标识
            
        Returns:
            Type[BaseMarketAdapter]: 适配器类
        """
        if market_type not in cls._adapters:
            raise ValueError(f"未注册的市场类型: {market_type}")
        
        return cls._adapters[market_type]
    
    @classmethod
    def list_markets(cls) -> Dict[str, str]:
        """
        列出所有已注册的市场
        
        Returns:
            dict: {market_type: adapter_class_name}
        """
        return {
            market_type: adapter_class.__name__
            for market_type, adapter_class in cls._adapters.items()
        }
    
    @classmethod
    def is_registered(cls, market_type: str) -> bool:
        """
        检查市场是否已注册
        
        Args:
            market_type: 市场类型标识
            
        Returns:
            bool: 是否已注册
        """
        return market_type in cls._adapters
    
    @classmethod
    def clear(cls):
        """
        清空所有注册的适配器
        主要用于测试
        """
        # 断开所有连接
        for adapter in cls._adapter_instances.values():
            if adapter.is_connected():
                adapter.disconnect()
        
        cls._adapters.clear()
        cls._adapter_instances.clear()
        print("✓ 已清空所有市场适配器")
    
    @classmethod
    def switch_market(
        cls,
        from_market: str,
        to_market: str,
        to_config: Optional[Dict] = None
    ) -> BaseMarketAdapter:
        """
        切换市场
        
        Args:
            from_market: 当前市场类型
            to_market: 目标市场类型
            to_config: 目标市场配置
            
        Returns:
            BaseMarketAdapter: 新市场的适配器实例
        """
        # 断开当前市场连接
        if from_market in cls._adapter_instances:
            adapter = cls._adapter_instances[from_market]
            if adapter.is_connected():
                adapter.disconnect()
                print(f"✓ 已断开 {from_market} 连接")
        
        # 获取或创建新市场适配器
        new_adapter = cls.get_adapter(to_market, to_config, force_new=True)
        print(f"✓ 已切换到 {to_market}")
        
        return new_adapter


# 便捷的装饰器,用于自动注册适配器
def register_adapter(market_type: str):
    """
    适配器注册装饰器
    
    Args:
        market_type: 市场类型标识
        
    Example:
        @register_adapter('us_stock')
        class USStockAdapter(BaseMarketAdapter):
            pass
    """
    def decorator(adapter_class: Type[BaseMarketAdapter]):
        MarketRegistry.register(market_type, adapter_class)
        return adapter_class
    return decorator
