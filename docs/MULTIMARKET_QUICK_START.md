# 多市场支持快速开始指南

## 概述

OSkhQuant现已支持多个市场的量化交易,本文档介绍如何快速开始使用多市场功能。

## 核心概念

### 市场适配器 (Market Adapter)

市场适配器是连接不同市场数据源和交易接口的桥梁。每个市场都有独立的适配器实现。

```python
from adapters import MarketRegistry

# 获取A股适配器
adapter = MarketRegistry.get_adapter('china_a_stock', config={
    'userdata_path': 'D:\\miniQMT\\userdata_mini'
})

# 连接
adapter.connect()

# 获取市场信息
market_info = adapter.get_market_info()
print(market_info)
```

### 标准化代码格式

所有标的代码使用统一的标准化格式:`市场前缀.原始代码`

| 市场 | 原始格式 | 标准化格式 | 说明 |
|------|---------|-----------|------|
| A股 | 000001.SZ | CN.000001.SZ | 增加CN前缀 |
| 美股 | AAPL | US.AAPL | 增加US前缀 |
| 港股 | 00700 | HK.00700 | 增加HK前缀 |
| 加密货币 | BTCUSDT | CRYPTO.BTC.USDT | 分离基础币种和计价币种 |

### 代码转换

```python
from adapters import DataNormalizer

# 标准化
standard_symbol = DataNormalizer.normalize_symbol('000001.SZ', 'china_a_stock')
print(standard_symbol)  # CN.000001.SZ

# 反标准化
original_symbol = DataNormalizer.denormalize_symbol('CN.000001.SZ')
print(original_symbol)  # 000001.SZ

# 提取市场类型
market_type = DataNormalizer.extract_market_type('CN.000001.SZ')
print(market_type)  # china_a_stock
```

## 使用示例

### 1. 基础使用

```python
from adapters import ChinaAStockAdapter

# 创建A股适配器
adapter = ChinaAStockAdapter({
    'userdata_path': 'D:\\miniQMT\\userdata_mini'
})

# 连接
if adapter.connect():
    # 获取交易日历
    trading_days = adapter.get_trading_calendar('20240101', '20241231')
    print(f'2024年交易日数量: {len(trading_days)}')
    
    # 计算交易费用
    cost = adapter.calculate_commission(
        price=10.0,
        quantity=100,
        side='buy'
    )
    print(f'交易费用: {cost}')
    
    # 断开连接
    adapter.disconnect()
```

### 2. 市场切换

```python
from adapters import MarketRegistry

# 初始化A股适配器
a_stock_adapter = MarketRegistry.get_adapter('china_a_stock', {
    'userdata_path': 'D:\\miniQMT\\userdata_mini'
})
a_stock_adapter.connect()

# ... 使用A股适配器 ...

# 切换到美股(未来版本)
# us_stock_adapter = MarketRegistry.switch_market(
#     from_market='china_a_stock',
#     to_market='us_stock',
#     to_config={'api_key': 'your_key'}
# )
```

### 3. 查看已注册市场

```python
from adapters import MarketRegistry

# 列出所有已注册的市场
markets = MarketRegistry.list_markets()
for market_type, adapter_name in markets.items():
    print(f'{market_type}: {adapter_name}')

# 输出:
# china_a_stock: ChinaAStockAdapter
```

## 在策略中使用

### 当前策略继续有效

现有A股策略无需修改即可继续使用。系统会自动处理代码标准化:

```python
# 原有策略代码,无需修改
def init(stocks, data):
    g.stock_list = ['000001.SZ', '600000.SH']  # 仍然有效
    
def khHandlebar(data):
    # 内部会自动转换为 CN.000001.SZ, CN.600000.SH
    price = khPrice(data, '000001.SZ', 'close')
    # ... 策略逻辑 ...
```

### 未来多市场策略

```python
# 将来可以在同一策略中使用多个市场
def init(stocks, data):
    g.stock_list = [
        'CN.000001.SZ',      # A股
        'US.AAPL',           # 美股
        'HK.00700',          # 港股
        'CRYPTO.BTC.USDT'    # 加密货币
    ]
    
def khHandlebar(data):
    # 自动识别市场类型
    for symbol in g.stock_list:
        price = khPrice(data, symbol, 'close')
        market_type = khGetMarket(symbol)  # 新增函数
        # 根据不同市场执行不同逻辑
```

## 费用计算示例

### A股费用计算

```python
# 买入100股,价格10元
cost = adapter.calculate_commission(
    price=10.0,
    quantity=100,
    side='buy'
)

# 输出:
# {
#     'commission': 5.0,      # 佣金(最低5元)
#     'stamp_tax': 0.0,       # 印花税(买入不收)
#     'transfer_fee': 0.0,    # 过户费
#     'total': 5.0
# }

# 卖出1000股,价格10元
cost = adapter.calculate_commission(
    price=10.0,
    quantity=1000,
    side='sell'
)

# 输出:
# {
#     'commission': 5.0,      # 佣金(最低5元)
#     'stamp_tax': 10.0,      # 印花税(千分之一)
#     'transfer_fee': 0.0,    # 过户费
#     'total': 15.0
# }
```

## 交易日历

### 判断交易日

```python
from datetime import date

# 检查特定日期是否为交易日
trading_days = adapter.get_trading_calendar('20241001', '20241007')

# 检查是否包含国庆节(非交易日)
oct_1 = date(2024, 10, 1)
is_trading = oct_1 in trading_days
print(f'2024-10-01是交易日: {is_trading}')  # False
```

### 获取交易时间段

```python
# 获取市场交易时间
market_hours = adapter.get_market_hours()
print(market_hours)

# 输出:
# [
#     ("09:30:00", "11:30:00"),  # 上午
#     ("13:00:00", "15:00:00")   # 下午
# ]
```

## 注意事项

### 1. 向后兼容性

- ✅ 现有A股策略完全兼容,无需修改
- ✅ 原有配置文件格式仍然有效
- ✅ miniQMT接口保持不变

### 2. 代码标准化

- 内部使用标准化格式(带市场前缀)
- 调用外部API时自动转换为原始格式
- 策略可以选择使用任一格式

### 3. 市场特性

不同市场有不同的特性,需要注意:

| 特性 | A股 | 美股 | 港股 | 加密货币 |
|------|-----|-----|------|---------|
| 交易时间 | 工作日9:30-15:00 | 工作日9:30-16:00(EST) | 工作日9:30-16:00 | 7×24小时 |
| 最小交易单位 | 100股 | 1股 | 按手数 | 最小下单量 |
| 价格变动 | 0.01元 | 0.01美元 | 分档位 | 精度不同 |
| 涨跌停 | 10% | 无 | 无 | 无 |
| 交易规则 | T+1 | T+0 | T+0 | T+0 |

## 开发路线图

### v2.1.0 - 美股支持 (计划中)
- [ ] Alpaca API集成
- [ ] Yahoo Finance数据源
- [ ] 美股交易时间和日历
- [ ] 美股费用计算

### v2.2.0 - 港股支持 (计划中)
- [ ] 富途OpenAPI集成
- [ ] 港股手数处理
- [ ] 港股价格档位
- [ ] 港股综合费用

### v2.3.0 - 加密货币支持 (计划中)
- [ ] Binance API集成
- [ ] CCXT统一接口
- [ ] 24/7交易支持
- [ ] Maker/Taker费用

## 常见问题

### Q: 现有策略需要修改吗?

A: **不需要**。现有A股策略无需任何修改即可继续使用。系统会自动处理代码格式转换。

### Q: 如何添加新市场?

A: 继承`BaseMarketAdapter`类,实现所有抽象方法,然后使用`@register_adapter`装饰器注册即可。

### Q: 标准化格式是强制的吗?

A: 内部使用标准化格式,但策略代码可以继续使用原始格式。系统会自动转换。

### Q: 性能影响如何?

A: 适配器层增加的开销极小,主要是字符串处理。对回测和实盘性能影响可忽略不计。

## 获取帮助

- 查看[完整设计文档](./design_doc.md)
- 查看[实施进展](./MULTIMARKET_IMPLEMENTATION_PROGRESS.md)
- 提交Issue到项目仓库

---

**文档版本**: v1.0.0  
**最后更新**: 2025-10-26
