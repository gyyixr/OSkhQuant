# 市场适配器API文档

## 概述

市场适配器是OSkhQuant多市场支持的核心组件,它提供了统一的接口来访问不同市场的数据和交易功能。所有市场适配器都继承自`BaseMarketAdapter`抽象基类,实现了标准化的接口规范。

## 核心架构

```
BaseMarketAdapter (抽象基类)
    ├── ChinaAStockAdapter (A股适配器)
    ├── USStockAdapter (美股适配器)
    ├── HKStockAdapter (港股适配器)
    └── CryptoAdapter (加密货币适配器)
```

## BaseMarketAdapter 接口规范

### 1. 基础接口

#### connect()
```python
def connect(self) -> bool:
    """
    连接到数据源
    
    Returns:
        bool: 连接成功返回True,失败返回False
    
    Raises:
        ConnectionError: 当连接失败时抛出
    """
```

**使用示例:**
```python
from adapters.market_registry import MarketRegistry
from khConfig import KhConfig

config = KhConfig('config.kh')
adapter = MarketRegistry.get_adapter('china_a_stock', config)

if adapter.connect():
    print("连接成功")
else:
    print("连接失败")
```

#### disconnect()
```python
def disconnect(self) -> bool:
    """
    断开与数据源的连接
    
    Returns:
        bool: 断开成功返回True,失败返回False
    """
```

#### is_connected()
```python
def is_connected(self) -> bool:
    """
    检查是否已连接
    
    Returns:
        bool: 已连接返回True,否则返回False
    """
```

#### get_market_type()
```python
def get_market_type(self) -> str:
    """
    获取市场类型
    
    Returns:
        str: 市场类型标识
            - 'china_a_stock': A股市场
            - 'us_stock': 美股市场
            - 'hk_stock': 港股市场
            - 'cryptocurrency': 加密货币市场
    """
```

### 2. 数据接口

#### get_market_data()
```python
def get_market_data(
    self,
    symbols: Union[str, List[str]],
    period: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    fields: Optional[List[str]] = None,
    dividend_type: str = 'none'
) -> pd.DataFrame:
    """
    获取历史行情数据
    
    Parameters:
        symbols: 标的代码或代码列表(标准化格式)
        period: K线周期
            - '1m': 1分钟
            - '5m': 5分钟
            - '15m': 15分钟
            - '30m': 30分钟
            - '1h': 1小时
            - '1d': 日线
            - '1w': 周线
            - '1M': 月线
        start_time: 开始时间,格式'YYYY-MM-DD'或'YYYY-MM-DD HH:MM:SS'
        end_time: 结束时间,格式同上
        fields: 需要的字段列表,None表示全部字段
            - 'open': 开盘价
            - 'high': 最高价
            - 'low': 最低价
            - 'close': 收盘价
            - 'volume': 成交量
            - 'amount': 成交额
        dividend_type: 复权类型(仅适用于股票)
            - 'none': 不复权
            - 'front': 前复权
            - 'back': 后复权
    
    Returns:
        pd.DataFrame: 行情数据,包含以下列:
            - symbol: 标的代码(标准化格式)
            - time: 时间戳(UTC时区)
            - open, high, low, close: OHLC价格
            - volume: 成交量
            - amount: 成交额
    
    Raises:
        ValueError: 参数错误
        DataError: 数据获取失败
    """
```

**使用示例:**
```python
# 获取单个标的日线数据
df = adapter.get_market_data(
    symbols='CN.000001.SZ',
    period='1d',
    start_time='2023-01-01',
    end_time='2023-12-31'
)

# 获取多个标的分钟数据
df = adapter.get_market_data(
    symbols=['US.AAPL', 'US.GOOGL'],
    period='5m',
    start_time='2024-01-01 09:30:00',
    end_time='2024-01-01 16:00:00',
    fields=['close', 'volume']
)
```

#### get_realtime_data()
```python
def get_realtime_data(
    self,
    symbols: Union[str, List[str]],
    fields: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    获取实时行情数据
    
    Parameters:
        symbols: 标的代码或代码列表(标准化格式)
        fields: 需要的字段列表,None表示全部字段
    
    Returns:
        pd.DataFrame: 实时行情数据
    """
```

#### subscribe_quote()
```python
def subscribe_quote(
    self,
    symbols: Union[str, List[str]],
    callback: Callable
) -> bool:
    """
    订阅实时行情推送
    
    Parameters:
        symbols: 标的代码或代码列表(标准化格式)
        callback: 回调函数,签名为callback(data: dict)
    
    Returns:
        bool: 订阅成功返回True
    """
```

#### unsubscribe_quote()
```python
def unsubscribe_quote(
    self,
    symbols: Union[str, List[str]]
) -> bool:
    """
    取消订阅实时行情
    
    Parameters:
        symbols: 标的代码或代码列表(标准化格式)
    
    Returns:
        bool: 取消成功返回True
    """
```

### 3. 交易接口

#### place_order()
```python
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
    
    Parameters:
        symbol: 标的代码(标准化格式)
        side: 买卖方向
            - 'buy': 买入
            - 'sell': 卖出
        order_type: 订单类型
            - 'market': 市价单
            - 'limit': 限价单
        quantity: 数量
        price: 价格(限价单必填)
        **kwargs: 其他参数(市场特定)
    
    Returns:
        str: 订单ID
    
    Raises:
        OrderError: 下单失败
    """
```

**使用示例:**
```python
# 限价买入
order_id = adapter.place_order(
    symbol='CN.000001.SZ',
    side='buy',
    order_type='limit',
    quantity=100,
    price=10.50
)

# 市价卖出
order_id = adapter.place_order(
    symbol='US.AAPL',
    side='sell',
    order_type='market',
    quantity=10
)
```

#### cancel_order()
```python
def cancel_order(self, order_id: str) -> bool:
    """
    撤单
    
    Parameters:
        order_id: 订单ID
    
    Returns:
        bool: 撤单成功返回True
    """
```

#### get_order_status()
```python
def get_order_status(self, order_id: str) -> dict:
    """
    查询订单状态
    
    Parameters:
        order_id: 订单ID
    
    Returns:
        dict: 订单信息
            {
                'order_id': str,
                'symbol': str,
                'side': str,
                'order_type': str,
                'quantity': float,
                'price': float,
                'filled_quantity': float,
                'filled_price': float,
                'status': str,  # 'pending', 'filled', 'partially_filled', 'cancelled'
                'create_time': datetime,
                'update_time': datetime
            }
    """
```

#### get_account_info()
```python
def get_account_info(self) -> dict:
    """
    获取账户信息
    
    Returns:
        dict: 账户信息
            {
                'account_id': str,
                'total_value': float,      # 总资产
                'available_cash': float,   # 可用资金
                'frozen_cash': float,      # 冻结资金
                'market_value': float,     # 持仓市值
                'profit_loss': float,      # 盈亏
                'profit_loss_ratio': float # 盈亏比例
            }
    """
```

#### get_positions()
```python
def get_positions(self) -> pd.DataFrame:
    """
    获取持仓信息
    
    Returns:
        pd.DataFrame: 持仓数据
            - symbol: 标的代码
            - quantity: 持仓数量
            - available_quantity: 可用数量
            - avg_price: 持仓均价
            - current_price: 当前价
            - market_value: 市值
            - profit_loss: 盈亏
            - profit_loss_ratio: 盈亏比例
    """
```

### 4. 市场特有接口

#### is_trading_time()
```python
def is_trading_time(self, dt: Optional[datetime] = None) -> bool:
    """
    判断是否为交易时间
    
    Parameters:
        dt: 指定时间,None表示当前时间
    
    Returns:
        bool: 是交易时间返回True
    """
```

#### is_trading_day()
```python
def is_trading_day(self, date: Optional[str] = None) -> bool:
    """
    判断是否为交易日
    
    Parameters:
        date: 日期字符串'YYYY-MM-DD',None表示今天
    
    Returns:
        bool: 是交易日返回True
    """
```

#### get_trading_calendar()
```python
def get_trading_calendar(
    self,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    获取交易日历
    
    Parameters:
        start_date: 开始日期'YYYY-MM-DD'
        end_date: 结束日期'YYYY-MM-DD'
    
    Returns:
        List[str]: 交易日列表
    """
```

#### calculate_commission()
```python
def calculate_commission(
    self,
    price: float,
    quantity: float,
    side: str
) -> dict:
    """
    计算交易佣金和费用
    
    Parameters:
        price: 价格
        quantity: 数量
        side: 买卖方向('buy'或'sell')
    
    Returns:
        dict: 费用明细
            {
                'commission': float,    # 佣金
                'stamp_tax': float,     # 印花税(A股)
                'transfer_fee': float,  # 过户费(A股)
                'sec_fee': float,       # SEC费(美股)
                'total': float          # 总费用
            }
    """
```

#### normalize_symbol()
```python
def normalize_symbol(self, symbol: str) -> str:
    """
    标准化标的代码
    
    Parameters:
        symbol: 原始代码
    
    Returns:
        str: 标准化代码
    
    Examples:
        A股: '000001.SZ' -> 'CN.000001.SZ'
        美股: 'AAPL' -> 'US.AAPL'
        港股: '00700' -> 'HK.00700'
        加密货币: 'BTCUSDT' -> 'CRYPTO.BTC.USDT'
    """
```

### 5. 辅助方法

#### validate_symbol()
```python
def validate_symbol(self, symbol: str) -> bool:
    """
    验证标的代码格式是否正确
    
    Parameters:
        symbol: 标的代码
    
    Returns:
        bool: 格式正确返回True
    """
```

#### convert_timezone()
```python
def convert_timezone(
    self,
    dt: datetime,
    to_tz: str = 'UTC'
) -> datetime:
    """
    时区转换
    
    Parameters:
        dt: 时间对象
        to_tz: 目标时区
    
    Returns:
        datetime: 转换后的时间
    """
```

## 市场特定适配器

### ChinaAStockAdapter (A股)

**特有方法:**

```python
def get_stock_list(self, market: str = 'all') -> List[str]:
    """
    获取股票列表
    
    Parameters:
        market: 市场('SZ', 'SH', 'all')
    
    Returns:
        List[str]: 股票代码列表
    """
```

**费用计算:**
- 佣金: 默认万分之三,最低5元
- 印花税: 卖出时千分之一
- 过户费: 上海股票成交金额万分之0.2

### USStockAdapter (美股)

**特有方法:**

```python
def check_pdt_rule(self) -> dict:
    """
    检查PDT规则(Pattern Day Trader)
    
    Returns:
        dict: PDT检查结果
            {
                'is_pdt': bool,
                'day_trade_count': int,
                'account_value': float
            }
    """
```

**费用计算:**
- 佣金: 通常为0(使用Alpaca等平台)
- SEC费: 卖出时成交金额的0.00278%
- FINRA TAF: 卖出时成交金额的0.0166%

### HKStockAdapter (港股)

**特有方法:**

```python
def get_lot_size(self, symbol: str) -> int:
    """
    获取最小交易单位(每手股数)
    
    Parameters:
        symbol: 标的代码
    
    Returns:
        int: 每手股数
    """

def get_tick_size(self, symbol: str, price: float) -> float:
    """
    获取最小价格变动单位
    
    Parameters:
        symbol: 标的代码
        price: 当前价格
    
    Returns:
        float: 最小价格变动单位
    """
```

**费用计算:**
- 佣金: 一般为成交金额的0.25%
- 印花税: 成交金额的0.1%
- 交易征费: 成交金额的0.0027%
- 交易费: 成交金额的0.005%
- 结算费: 成交金额的0.002%

### CryptoAdapter (加密货币)

**特有方法:**

```python
def get_min_quantity(self, symbol: str) -> float:
    """
    获取最小下单量
    
    Parameters:
        symbol: 标的代码
    
    Returns:
        float: 最小下单量
    """

def get_fee_discount(self) -> float:
    """
    获取手续费折扣率
    
    Returns:
        float: 折扣率(持有BNB等平台币可享受折扣)
    """
```

**费用计算:**
- Maker费率: 一般0.1%
- Taker费率: 一般0.1%
- VIP等级折扣: 根据交易量
- 平台币折扣: 持有BNB等可享受75折

## MarketRegistry 使用

### 注册适配器

```python
from adapters.market_registry import MarketRegistry, register_adapter
from adapters.base_adapter import BaseMarketAdapter

@register_adapter('my_market')
class MyMarketAdapter(BaseMarketAdapter):
    # 实现所有抽象方法
    pass
```

### 获取适配器

```python
from adapters.market_registry import MarketRegistry
from khConfig import KhConfig

config = KhConfig('config.kh')
adapter = MarketRegistry.get_adapter('china_a_stock', config)
```

### 切换市场

```python
# 切换到美股
us_adapter = MarketRegistry.switch_market('us_stock', config)

# 切换到港股
hk_adapter = MarketRegistry.switch_market('hk_stock', config)
```

## DataNormalizer 使用

### 代码标准化

```python
from adapters.data_normalizer import DataNormalizer

# A股代码标准化
std_code = DataNormalizer.normalize_symbol('000001.SZ', 'china_a_stock')
# 返回: 'CN.000001.SZ'

# 美股代码标准化
std_code = DataNormalizer.normalize_symbol('AAPL', 'us_stock')
# 返回: 'US.AAPL'
```

### 时区转换

```python
from datetime import datetime
from adapters.data_normalizer import DataNormalizer

# 转换为UTC
utc_time = DataNormalizer.convert_to_utc(
    datetime(2024, 1, 1, 9, 30, 0),
    'America/New_York'
)

# 转换为本地时区
local_time = DataNormalizer.convert_from_utc(
    utc_time,
    'Asia/Shanghai'
)
```

### 数据字段映射

```python
from adapters.data_normalizer import DataNormalizer

# 标准化DataFrame
df = DataNormalizer.normalize_dataframe(raw_df, 'us_stock')
```

## 错误处理

所有适配器方法都可能抛出以下异常:

- `ConnectionError`: 连接错误
- `AuthenticationError`: 认证失败
- `DataError`: 数据获取失败
- `OrderError`: 下单失败
- `ValueError`: 参数错误
- `NotImplementedError`: 功能未实现

**使用示例:**

```python
from adapters.market_registry import MarketRegistry

try:
    adapter = MarketRegistry.get_adapter('us_stock', config)
    adapter.connect()
    
    df = adapter.get_market_data(
        symbols='US.AAPL',
        period='1d',
        start_time='2023-01-01'
    )
    
except ConnectionError as e:
    print(f"连接失败: {e}")
except DataError as e:
    print(f"数据获取失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
finally:
    if adapter.is_connected():
        adapter.disconnect()
```

## 最佳实践

### 1. 使用上下文管理器

```python
class AdapterContext:
    def __init__(self, market_type, config):
        self.adapter = MarketRegistry.get_adapter(market_type, config)
    
    def __enter__(self):
        self.adapter.connect()
        return self.adapter
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.adapter.disconnect()

# 使用
with AdapterContext('us_stock', config) as adapter:
    df = adapter.get_market_data('US.AAPL', '1d')
```

### 2. 批量数据获取

```python
# 推荐: 一次获取多个标的
df = adapter.get_market_data(
    symbols=['US.AAPL', 'US.GOOGL', 'US.MSFT'],
    period='1d'
)

# 不推荐: 多次循环获取
for symbol in symbols:
    df = adapter.get_market_data(symbol, '1d')  # 效率低
```

### 3. 缓存适配器实例

```python
# MarketRegistry已实现单例缓存
adapter1 = MarketRegistry.get_adapter('us_stock', config)
adapter2 = MarketRegistry.get_adapter('us_stock', config)
# adapter1 和 adapter2 是同一个实例

# 强制创建新实例
adapter3 = MarketRegistry.get_adapter('us_stock', config, force_new=True)
```

### 4. 异步数据获取

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def fetch_data_async(adapter, symbol, period):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        df = await loop.run_in_executor(
            executor,
            adapter.get_market_data,
            symbol,
            period
        )
    return df

# 使用
df = asyncio.run(fetch_data_async(adapter, 'US.AAPL', '1d'))
```

## 参考资料

- [多市场快速开始指南](MULTIMARKET_QUICK_START.md)
- [适配器开发指南](ADAPTER_DEVELOPMENT_GUIDE.md)
- [配置指南](CONFIGURATION_GUIDE.md)
- [策略开发最佳实践](MULTIMARKET_STRATEGY_GUIDE.md)
