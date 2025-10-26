# 多市场策略开发指南

## 概述

本指南详细介绍如何在OSkhQuant系统中开发跨市场的量化策略,包括策略移植、多市场适配、最佳实践等内容。

## 策略开发基础

### 1. 统一的策略接口

所有市场使用相同的策略基类:

```python
from khStrategy import Strategy

class MyStrategy(Strategy):
    def init(self, ctx):
        """策略初始化"""
        pass
    
    def on_bar(self, ctx, bar):
        """K线数据回调"""
        pass
    
    def on_tick(self, ctx, tick):
        """Tick数据回调(可选)"""
        pass
    
    def on_order(self, ctx, order):
        """订单状态回调(可选)"""
        pass
```

### 2. 市场感知策略

通过`khGetMarket()`获取当前市场类型:

```python
class MarketAwareStrategy(Strategy):
    def init(self, ctx):
        market = khGetMarket(ctx)
        
        if market == 'china_a_stock':
            self.symbols = ['CN.000001.SZ', 'CN.600000.SH']
            self.position_size = 100  # A股最小单位
        elif market == 'us_stock':
            self.symbols = ['US.AAPL', 'US.GOOGL']
            self.position_size = 1  # 美股按股
        elif market == 'hk_stock':
            self.symbols = ['HK.00700', 'HK.09988']
            self.position_size = 100  # 港股按手
        elif market == 'cryptocurrency':
            self.symbols = ['CRYPTO.BTC.USDT', 'CRYPTO.ETH.USDT']
            self.position_size = 0.001  # 加密货币按币
```

## A股策略迁移指南

### 步骤1: 代码标准化

**原始A股策略:**
```python
class OldStrategy(Strategy):
    def init(self, ctx):
        self.stock = '000001.SZ'
    
    def on_bar(self, ctx, bar):
        price = khPrice(ctx, self.stock)
```

**迁移后:**
```python
class NewStrategy(Strategy):
    def init(self, ctx):
        # 使用标准化代码格式
        self.stock = 'CN.000001.SZ'
    
    def on_bar(self, ctx, bar):
        price = khPrice(ctx, self.stock)
```

**自动转换(推荐):**
```python
from adapters.data_normalizer import DataNormalizer

class NewStrategy(Strategy):
    def init(self, ctx):
        market = khGetMarket(ctx)
        # 自动标准化
        self.stock = DataNormalizer.normalize_symbol('000001.SZ', market)
```

### 步骤2: 交易时间处理

**原始策略:**
```python
def on_bar(self, ctx, bar):
    # 假设总是交易时间
    self.trade(ctx)
```

**迁移后:**
```python
def on_bar(self, ctx, bar):
    # 检查交易时间(多市场适配)
    if khIsTradeTime(ctx):
        self.trade(ctx)
```

### 步骤3: 交易单位处理

**A股固定100股:**
```python
def buy_stock(self, ctx, symbol):
    khBuy(ctx, symbol, 100, price)
```

**多市场适配:**
```python
def buy_stock(self, ctx, symbol):
    market = khGetMarket(ctx)
    
    if market == 'hk_stock':
        # 港股需要查询每手股数
        lot_size = khGetLotSize(ctx, symbol)
        quantity = lot_size
    elif market == 'us_stock':
        # 美股按股交易
        quantity = 10
    else:  # china_a_stock
        # A股100股起
        quantity = 100
    
    khBuy(ctx, symbol, quantity, price)
```

### 步骤4: 费用计算更新

**原始策略(硬编码):**
```python
commission = turnover * 0.0003
```

**迁移后(使用适配器):**
```python
from adapters.market_registry import MarketRegistry

adapter = MarketRegistry.get_adapter(market, config)
fees = adapter.calculate_commission(price, quantity, 'buy')
total_cost = fees['total']
```

## 跨市场策略开发

### 1. 通用双均线策略

适用于所有市场的双均线策略:

```python
from khStrategy import Strategy

class UniversalDualMA(Strategy):
    """通用双均线策略 - 适用于所有市场"""
    
    def init(self, ctx):
        # 策略参数
        self.fast_period = 5
        self.slow_period = 20
        
        # 根据市场选择标的
        market = khGetMarket(ctx)
        if market == 'us_stock':
            self.symbols = ['US.AAPL']
        elif market == 'hk_stock':
            self.symbols = ['HK.00700']
        elif market == 'cryptocurrency':
            self.symbols = ['CRYPTO.BTC.USDT']
        else:  # china_a_stock
            self.symbols = ['CN.000001.SZ']
        
        # 初始化指标
        for symbol in self.symbols:
            khMA(ctx, symbol, self.fast_period, 'fast_ma')
            khMA(ctx, symbol, self.slow_period, 'slow_ma')
    
    def on_bar(self, ctx, bar):
        # 只在交易时间执行
        if not khIsTradeTime(ctx):
            return
        
        for symbol in self.symbols:
            # 获取均线值
            fast_ma = khGet(ctx, symbol, 'fast_ma')
            slow_ma = khGet(ctx, symbol, 'slow_ma')
            
            if fast_ma is None or slow_ma is None:
                continue
            
            # 交易逻辑
            position = khPosition(ctx, symbol)
            
            if fast_ma > slow_ma and position == 0:
                # 金叉买入
                self.buy(ctx, symbol)
            elif fast_ma < slow_ma and position > 0:
                # 死叉卖出
                self.sell(ctx, symbol)
    
    def buy(self, ctx, symbol):
        """买入逻辑 - 自适应不同市场"""
        market = khGetMarket(ctx)
        price = khPrice(ctx, symbol)
        
        # 根据市场计算买入数量
        if market == 'hk_stock':
            lot_size = khGetLotSize(ctx, symbol)
            quantity = lot_size
        elif market == 'cryptocurrency':
            # 加密货币按金额计算
            cash = khCash(ctx)
            quantity = (cash * 0.3) / price  # 30%仓位
        elif market == 'us_stock':
            quantity = 10  # 美股10股
        else:  # A股
            quantity = 100  # A股100股
        
        khBuy(ctx, symbol, quantity, price)
    
    def sell(self, ctx, symbol):
        """卖出逻辑"""
        position = khPosition(ctx, symbol)
        price = khPrice(ctx, symbol)
        khSell(ctx, symbol, position, price)
```

### 2. 多市场轮动策略

在不同市场间轮动配置资产:

```python
class MultiMarketRotation(Strategy):
    """多市场轮动策略"""
    
    def init(self, ctx):
        # 定义多个市场的标的池
        self.markets = {
            'china_a_stock': ['CN.000001.SZ', 'CN.600000.SH'],
            'us_stock': ['US.AAPL', 'US.GOOGL', 'US.MSFT'],
            'hk_stock': ['HK.00700', 'HK.09988']
        }
        
        # 当前市场
        self.current_market = khGetMarket(ctx)
        
        # 动量周期
        self.momentum_period = 20
    
    def on_bar(self, ctx, bar):
        if not self.should_rebalance(ctx):
            return
        
        # 计算每个市场的收益率
        market_returns = {}
        for market, symbols in self.markets.items():
            returns = self.calculate_market_return(ctx, symbols)
            market_returns[market] = returns
        
        # 选择表现最好的市场
        best_market = max(market_returns, key=market_returns.get)
        
        # 如果最佳市场与当前不同,进行轮动
        if best_market != self.current_market:
            self.rotate_to_market(ctx, best_market)
    
    def calculate_market_return(self, ctx, symbols):
        """计算市场整体收益率"""
        total_return = 0
        for symbol in symbols:
            ret = khReturn(ctx, symbol, self.momentum_period)
            if ret is not None:
                total_return += ret
        return total_return / len(symbols)
    
    def rotate_to_market(self, ctx, target_market):
        """轮动到目标市场"""
        # 清空当前持仓
        self.clear_positions(ctx)
        
        # 买入目标市场
        self.current_market = target_market
        symbols = self.markets[target_market]
        
        for symbol in symbols:
            self.buy_equal_weight(ctx, symbol, len(symbols))
```

### 3. 事件驱动跨市场策略

基于事件在不同市场执行交易:

```python
class CrossMarketEvent(Strategy):
    """跨市场事件驱动策略"""
    
    def init(self, ctx):
        # 监控美股指数
        self.us_index = 'US.SPY'
        # A股对应标的
        self.a_stock = 'CN.000300.SH'  # 沪深300ETF
        
        # 阈值
        self.threshold = 0.02  # 2%波动
    
    def on_bar(self, ctx, bar):
        # 检测美股指数大幅波动
        us_return = khReturn(ctx, self.us_index, 1)
        
        if abs(us_return) > self.threshold:
            # 美股大幅波动,预期A股跟随
            self.trade_a_stock(ctx, us_return)
    
    def trade_a_stock(self, ctx, us_signal):
        """根据美股信号交易A股"""
        if us_signal > 0:
            # 美股上涨,买入A股
            khBuy(ctx, self.a_stock, 100, khPrice(ctx, self.a_stock))
        elif us_signal < 0:
            # 美股下跌,卖出A股
            position = khPosition(ctx, self.a_stock)
            if position > 0:
                khSell(ctx, self.a_stock, position, khPrice(ctx, self.a_stock))
```

## 市场特定策略

### 美股T+0策略

利用美股T+0特性的日内交易:

```python
class USDayTrading(Strategy):
    """美股日内T+0策略"""
    
    def init(self, ctx):
        # 确保是美股市场
        assert khGetMarket(ctx) == 'us_stock', "该策略仅适用于美股"
        
        self.symbol = 'US.AAPL'
        self.entry_time = '09:30:00'
        self.exit_time = '15:50:00'
    
    def on_bar(self, ctx, bar):
        current_time = khCurrentTime(ctx)
        
        # 开盘后入场
        if current_time == self.entry_time:
            self.enter_position(ctx)
        
        # 收盘前平仓
        elif current_time == self.exit_time:
            self.exit_position(ctx)
    
    def enter_position(self, ctx):
        """日内开仓"""
        price = khPrice(ctx, self.symbol)
        khBuy(ctx, self.symbol, 100, price)
    
    def exit_position(self, ctx):
        """日内平仓"""
        position = khPosition(ctx, self.symbol)
        if position > 0:
            price = khPrice(ctx, self.symbol)
            khSell(ctx, self.symbol, position, price)
```

### 港股价格档位策略

利用港股价格档位特性:

```python
class HKTickSizeStrategy(Strategy):
    """港股价格档位策略"""
    
    def init(self, ctx):
        assert khGetMarket(ctx) == 'hk_stock', "该策略仅适用于港股"
        self.symbol = 'HK.00700'
    
    def on_bar(self, ctx, bar):
        price = khPrice(ctx, self.symbol)
        tick_size = khGetTickSize(ctx, self.symbol, price)
        
        # 根据tick_size调整挂单价格
        buy_price = self.adjust_price(price * 0.99, tick_size)
        sell_price = self.adjust_price(price * 1.01, tick_size)
        
        # 网格交易
        position = khPosition(ctx, self.symbol)
        if position == 0:
            lot_size = khGetLotSize(ctx, self.symbol)
            khBuy(ctx, self.symbol, lot_size, buy_price)
        elif price >= sell_price:
            khSell(ctx, self.symbol, position, sell_price)
    
    def adjust_price(self, price, tick_size):
        """调整价格到合法档位"""
        return round(price / tick_size) * tick_size
```

### 加密货币24/7策略

利用加密货币全天候交易:

```python
class Crypto247Strategy(Strategy):
    """加密货币24/7动量策略"""
    
    def init(self, ctx):
        assert khGetMarket(ctx) == 'cryptocurrency', "该策略仅适用于加密货币"
        
        self.symbol = 'CRYPTO.BTC.USDT'
        self.lookback = 24  # 24小时动量
    
    def on_bar(self, ctx, bar):
        # 无需检查交易时间,加密货币24/7交易
        
        # 计算动量
        momentum = khReturn(ctx, self.symbol, self.lookback)
        
        if momentum > 0.05:  # 24小时涨幅>5%
            self.buy(ctx)
        elif momentum < -0.05:  # 24小时跌幅>5%
            self.sell(ctx)
    
    def buy(self, ctx):
        cash = khCash(ctx)
        price = khPrice(ctx, self.symbol)
        
        # 检查最小交易量
        min_qty = khGetMinQuantity(ctx, self.symbol)
        quantity = max((cash * 0.5) / price, min_qty)
        
        khBuy(ctx, self.symbol, quantity, price)
```

## 策略移植检查清单

### 必做项

- [ ] **代码标准化**: 所有symbol使用标准化格式(CN./US./HK./CRYPTO.)
- [ ] **交易时间检查**: 使用`khIsTradeTime()`而非硬编码
- [ ] **市场类型判断**: 使用`khGetMarket()`获取当前市场
- [ ] **数量单位调整**: 根据市场调整交易数量(股/手/币)
- [ ] **费用计算更新**: 使用适配器计算交易成本
- [ ] **时区处理**: 确保时间相关逻辑使用UTC时间

### 建议项

- [ ] **配置参数化**: 将市场特定参数移到配置文件
- [ ] **错误处理**: 添加市场特定的异常处理
- [ ] **日志记录**: 记录市场切换和关键决策
- [ ] **回测验证**: 在目标市场进行充分回测
- [ ] **性能优化**: 针对市场特性优化数据获取
- [ ] **风控适配**: 根据市场特性调整风控参数

## 最佳实践

### 1. 使用配置驱动

**不推荐:**
```python
def init(self, ctx):
    if khGetMarket(ctx) == 'us_stock':
        self.fast_period = 5
        self.slow_period = 20
    elif khGetMarket(ctx) == 'china_a_stock':
        self.fast_period = 10
        self.slow_period = 30
```

**推荐:**
```python
def init(self, ctx):
    # 从配置文件读取
    config = ctx.config
    market_params = config.get('market_params', {})
    
    self.fast_period = market_params.get('fast_period', 5)
    self.slow_period = market_params.get('slow_period', 20)
```

配置文件:
```json
{
    "market_params": {
        "us_stock": {
            "fast_period": 5,
            "slow_period": 20
        },
        "china_a_stock": {
            "fast_period": 10,
            "slow_period": 30
        }
    }
}
```

### 2. 抽象市场差异

创建市场参数类:

```python
from dataclasses import dataclass

@dataclass
class MarketParams:
    """市场参数"""
    min_quantity: float
    tick_size: float
    commission_rate: float
    
class MarketParamsFactory:
    """市场参数工厂"""
    
    @staticmethod
    def create(market_type: str):
        params = {
            'china_a_stock': MarketParams(100, 0.01, 0.0003),
            'us_stock': MarketParams(1, 0.01, 0.0),
            'hk_stock': MarketParams(100, 0.001, 0.0025),
            'cryptocurrency': MarketParams(0.001, 0.01, 0.001)
        }
        return params.get(market_type)

# 使用
class Strategy:
    def init(self, ctx):
        market = khGetMarket(ctx)
        self.params = MarketParamsFactory.create(market)
        
    def buy(self, ctx, symbol):
        quantity = self.params.min_quantity
        khBuy(ctx, symbol, quantity, price)
```

### 3. 统一的数据处理

创建数据处理工具类:

```python
class DataHelper:
    """数据处理助手"""
    
    @staticmethod
    def get_standard_bars(ctx, symbol, period, count):
        """获取标准化K线数据"""
        from adapters.data_normalizer import DataNormalizer
        
        # 获取原始数据
        bars = khGetBars(ctx, symbol, period, count)
        
        # 标准化
        market = khGetMarket(ctx)
        bars = DataNormalizer.normalize_dataframe(bars, market)
        
        return bars
    
    @staticmethod
    def calculate_returns(ctx, symbol, period):
        """计算收益率(多市场适配)"""
        bars = DataHelper.get_standard_bars(ctx, symbol, '1d', period + 1)
        
        if len(bars) < 2:
            return None
        
        return (bars['close'].iloc[-1] / bars['close'].iloc[0]) - 1

# 使用
class Strategy:
    def on_bar(self, ctx, bar):
        returns = DataHelper.calculate_returns(ctx, self.symbol, 20)
```

### 4. 模块化策略组件

```python
class SignalGenerator:
    """信号生成器"""
    def generate(self, ctx, symbol):
        pass

class MASignal(SignalGenerator):
    """均线信号"""
    def __init__(self, fast, slow):
        self.fast = fast
        self.slow = slow
    
    def generate(self, ctx, symbol):
        fast_ma = khMA(ctx, symbol, self.fast)
        slow_ma = khMA(ctx, symbol, self.slow)
        
        if fast_ma > slow_ma:
            return 1  # 买入信号
        elif fast_ma < slow_ma:
            return -1  # 卖出信号
        return 0  # 无信号

class PositionManager:
    """仓位管理器"""
    def __init__(self, max_position=0.3):
        self.max_position = max_position
    
    def calculate_quantity(self, ctx, symbol, signal):
        """根据信号计算数量"""
        if signal == 0:
            return 0
        
        cash = khCash(ctx)
        price = khPrice(ctx, symbol)
        market = khGetMarket(ctx)
        
        # 计算目标金额
        target_value = cash * self.max_position
        quantity = target_value / price
        
        # 调整到市场最小单位
        if market == 'china_a_stock':
            quantity = round(quantity / 100) * 100
        elif market == 'hk_stock':
            lot_size = khGetLotSize(ctx, symbol)
            quantity = round(quantity / lot_size) * lot_size
        
        return quantity

# 组合使用
class ModularStrategy(Strategy):
    def init(self, ctx):
        self.signal = MASignal(5, 20)
        self.position_mgr = PositionManager(0.3)
        self.symbol = self.get_symbol(ctx)
    
    def on_bar(self, ctx, bar):
        signal = self.signal.generate(ctx, self.symbol)
        quantity = self.position_mgr.calculate_quantity(ctx, self.symbol, signal)
        
        if signal > 0 and quantity > 0:
            khBuy(ctx, self.symbol, quantity, khPrice(ctx, self.symbol))
        elif signal < 0:
            position = khPosition(ctx, self.symbol)
            if position > 0:
                khSell(ctx, self.symbol, position, khPrice(ctx, self.symbol))
```

## 测试与验证

### 单元测试

```python
import unittest
from unittest.mock import Mock

class TestMultiMarketStrategy(unittest.TestCase):
    def test_a_stock_quantity(self):
        strategy = UniversalDualMA()
        ctx = Mock()
        ctx.market_type = 'china_a_stock'
        
        quantity = strategy.calculate_quantity(ctx, 'CN.000001.SZ', 10.0)
        self.assertEqual(quantity % 100, 0)  # A股100股整数倍
    
    def test_us_stock_quantity(self):
        strategy = UniversalDualMA()
        ctx = Mock()
        ctx.market_type = 'us_stock'
        
        quantity = strategy.calculate_quantity(ctx, 'US.AAPL', 150.0)
        self.assertGreater(quantity, 0)  # 美股任意数量
```

### 回测验证

```python
def backtest_all_markets():
    """在所有市场回测策略"""
    markets = ['china_a_stock', 'us_stock', 'hk_stock', 'cryptocurrency']
    results = {}
    
    for market in markets:
        config = load_config(f'config_{market}.kh')
        result = run_backtest(UniversalDualMA, config)
        results[market] = result
        
        print(f"\n{market} 回测结果:")
        print(f"  总收益: {result['total_return']:.2%}")
        print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {result['max_drawdown']:.2%}")
    
    return results
```

## 常见问题

### Q1: 如何处理不同市场的时区?

**A**: 系统自动处理时区转换,策略中使用UTC时间:

```python
from datetime import datetime
import pytz

def on_bar(self, ctx, bar):
    # 获取UTC时间
    utc_time = khCurrentTime(ctx)
    
    # 转换为本地时区
    local_tz = pytz.timezone('Asia/Shanghai')
    local_time = utc_time.astimezone(local_tz)
```

### Q2: 跨市场策略如何切换配置?

**A**: 使用多个配置文件或配置参数:

```python
# 方法1: 多个配置文件
config_a = KhConfig('config_a_stock.kh')
config_us = KhConfig('config_us_stock.kh')

# 方法2: 单个配置,动态切换
config.switch_market('us_stock')
```

### Q3: 如何在策略中获取多个市场的数据?

**A**: 使用MarketRegistry:

```python
from adapters.market_registry import MarketRegistry

class CrossMarketData(Strategy):
    def init(self, ctx):
        # 获取A股适配器
        self.a_adapter = MarketRegistry.get_adapter('china_a_stock', config)
        # 获取美股适配器
        self.us_adapter = MarketRegistry.get_adapter('us_stock', config)
    
    def on_bar(self, ctx, bar):
        # 获取A股数据
        a_data = self.a_adapter.get_market_data('CN.000001.SZ', '1d')
        # 获取美股数据
        us_data = self.us_adapter.get_market_data('US.AAPL', '1d')
```

### Q4: 如何优化多市场策略的性能?

**A**: 使用数据缓存和批量获取:

```python
def init(self, ctx):
    # 批量获取多个标的数据
    symbols = ['US.AAPL', 'US.GOOGL', 'US.MSFT']
    self.data = adapter.get_market_data(
        symbols=symbols,
        period='1d',
        start_time='2023-01-01'
    )  # 一次性获取,避免多次调用
```

## 参考资料

- [市场适配器API文档](MARKET_ADAPTER_API.md)
- [配置指南](CONFIGURATION_GUIDE.md)
- [多市场快速开始](MULTIMARKET_QUICK_START.md)
- [示例策略代码](../examples/)

## 示例策略列表

系统提供以下示例策略供参考:

1. **examples/us_stock_dual_ma.py** - 美股双均线策略
2. **examples/hk_stock_grid.py** - 港股网格策略
3. **examples/crypto_momentum.py** - 加密货币动量策略
4. **examples/cross_market_rotation.py** - 跨市场轮动策略
5. **examples/event_driven_cross_market.py** - 事件驱动跨市场策略

每个示例都包含详细注释和最佳实践演示。
