# 多市场交易功能扩展实施进展

## 项目概述

本项目旨在将OSkhQuant量化交易系统从仅支持A股扩展到支持多个市场,包括:
- **A股市场** (中国股票市场)
- **美股市场** (US Stock Market)
- **港股市场** (Hong Kong Stock Market)
- **加密货币市场** (Cryptocurrency Market)

## 已完成工作

### ✅ 阶段1: 架构设计与基础框架 (COMPLETE)

#### 1.1 市场适配器基类 (BaseMarketAdapter)
- **文件**: `adapters/base_adapter.py`
- **功能**: 
  - 定义统一的市场适配器接口规范
  - 包含基础接口(连接、断开、状态检查)
  - 数据接口(获取标的列表、历史数据、实时行情)
  - 交易接口(账户信息、持仓、下单、撤单)
  - 市场特有接口(代码标准化、交易日历、费用计算)
- **关键特性**:
  - 抽象基类,所有市场适配器必须继承并实现
  - 提供默认实现和辅助方法
  - 支持订单验证、最小交易单位、价格档位等

#### 1.2 市场注册中心 (MarketRegistry)
- **文件**: `adapters/market_registry.py`
- **功能**:
  - 单例模式管理所有市场适配器
  - 适配器注册、注销、查找功能
  - 市场切换功能
  - 提供装饰器 `@register_adapter` 用于自动注册
- **使用示例**:
  ```python
  # 注册适配器
  @register_adapter('us_stock')
  class USStockAdapter(BaseMarketAdapter):
      pass
  
  # 获取适配器
  adapter = MarketRegistry.get_adapter('us_stock', config)
  
  # 切换市场
  MarketRegistry.switch_market('china_a_stock', 'us_stock')
  ```

#### 1.3 数据标准化模块 (DataNormalizer)
- **文件**: `adapters/data_normalizer.py`
- **功能**:
  - 标的代码标准化:不同市场的代码格式统一化
    - A股: `000001.SZ` → `CN.000001.SZ`
    - 美股: `AAPL` → `US.AAPL`
    - 港股: `00700` → `HK.00700`
    - 加密货币: `BTCUSDT` → `CRYPTO.BTC.USDT`
  - 时间标准化:处理不同时区的时间转换
  - 数据字段映射:统一不同数据源的字段名称
  - 代码格式验证
- **市场前缀映射**:
  ```python
  MARKET_PREFIXES = {
      'china_a_stock': 'CN',
      'us_stock': 'US',
      'hk_stock': 'HK',
      'cryptocurrency': 'CRYPTO'
  }
  ```

### ✅ 阶段2: A股适配器改造 (IN_PROGRESS)

#### 2.1 A股适配器 (ChinaAStockAdapter)
- **文件**: `adapters/china_a_stock_adapter.py`
- **功能**:
  - 将现有miniQMT功能封装为标准适配器接口
  - 实现A股特定的交易规则(T+1、100股整数倍)
  - 实现A股费用计算(佣金、印花税、过户费)
  - 实现A股交易日历(工作日排除节假日)
- **市场信息**:
  - 市场类型: `china_a_stock`
  - 时区: `Asia/Shanghai` (UTC+8)
  - 货币: CNY
  - 交易时间: 09:30-11:30, 13:00-15:00
  - 最小价格变动: 0.01元
  - 最小交易单位: 100股
  - 涨跌停限制: 10%
  - 交易规则: T+1

#### 2.2 代码标准化实现
- **标准化格式**: 所有A股代码添加 `CN.` 前缀
- **示例**:
  - `000001.SZ` → `CN.000001.SZ` (平安银行)
  - `600000.SH` → `CN.600000.SH` (浦发银行)
- **反标准化**: 调用miniQMT时自动去除前缀

#### 2.3 费用计算
A股交易费用计算已实现:
```python
{
    'commission': 佣金 (万分之三,最低5元),
    'stamp_tax': 印花税 (千分之一,仅卖出),
    'transfer_fee': 过户费 (沪市0.002%),
    'total': 总费用
}
```

## 当前文件结构

```
OSkhQuant/
├── adapters/                          # 新增:市场适配器模块
│   ├── __init__.py                   # 模块初始化
│   ├── base_adapter.py               # 市场适配器基类 (482行)
│   ├── market_registry.py            # 市场注册中心 (211行)
│   ├── data_normalizer.py            # 数据标准化 (356行)
│   └── china_a_stock_adapter.py      # A股适配器 (439行)
├── khConfig.py                        # 配置管理类 (待扩展)
├── khFrame.py                         # 框架核心
├── khTrade.py                         # 交易管理 (待扩展)
├── khRisk.py                          # 风险控制 (待扩展)
├── khQTTools.py                       # 工具集
└── strategies/                        # 策略目录
```

## 下一步计划

### 阶段3: 配置系统扩展
- [ ] 扩展 `khConfig.py` 添加多市场配置支持
- [ ] 实现API凭证加密/解密功能
- [ ] 扩展.kh配置文件格式
- [ ] 实现配置验证功能

### 阶段4: 美股适配器实现 (v2.1.0核心功能)
- [ ] 创建USStockAdapter基类
- [ ] 实现AlpacaAdapter (免费API)
- [ ] 实现美股交易时间处理(EST/EDT)
- [ ] 实现美股交易日历
- [ ] 实现美股费用计算(SEC费、FINRA费)
- [ ] 添加YahooFinanceAdapter备选数据源

### 阶段5: 港股适配器实现 (v2.2.0)
- [ ] 创建HKStockAdapter基类
- [ ] 实现FutuAdapter (富途OpenAPI)
- [ ] 实现港股手数处理
- [ ] 实现港股价格档位
- [ ] 实现港股费用计算

### 阶段6: 加密货币适配器 (v2.3.0)
- [ ] 创建CryptoAdapter基类
- [ ] 实现BinanceAdapter
- [ ] 实现CCXTAdapter
- [ ] 实现24/7交易时间处理
- [ ] 实现Maker/Taker费用计算

## 设计亮点

### 1. 适配器模式
- 统一的接口规范,屏蔽不同市场的差异
- 新增市场只需实现BaseMarketAdapter接口
- 策略代码无需修改即可支持多市场

### 2. 数据标准化
- 统一的标的代码格式(市场前缀+原始代码)
- 统一的时间处理(UTC时区转换)
- 统一的数据字段(标准化字段映射)

### 3. 向后兼容
- 现有A股功能完全保留
- ChinaAStockAdapter封装miniQMT逻辑
- 策略无需修改即可继续使用

### 4. 扩展性强
- 装饰器自动注册适配器
- 插件式架构,易于添加新市场
- 配置驱动,灵活切换市场

## 技术栈

- **Python 3.x**
- **pandas**: 数据处理
- **pytz**: 时区处理
- **holidays**: 交易日历
- **miniQMT**: A股数据和交易(现有)
- **alpaca-trade-api**: 美股数据和交易(待集成)
- **futu-api**: 港股数据和交易(待集成)
- **ccxt**: 加密货币统一接口(待集成)

## 预估工作量

| 阶段 | 任务数 | 预估时间 | 状态 |
|------|-------|---------|------|
| 阶段1: 架构设计 | 3 | 已完成 | ✅ COMPLETE |
| 阶段2: A股适配器 | 3 | 已完成 | ✅ COMPLETE |
| 阶段3: 配置系统 | 4 | 待开始 | ⏳ PENDING |
| 阶段4: 美股适配器 | 7 | 待开始 | ⏳ PENDING |
| 阶段5: 港股适配器 | 6 | 待开始 | ⏳ PENDING |
| 阶段6: 加密货币适配器 | 7 | 待开始 | ⏳ PENDING |
| 阶段7-10: 系统集成 | 16 | 待开始 | ⏳ PENDING |
| 阶段11-12: 示例和测试 | 8 | 待开始 | ⏳ PENDING |
| 阶段13-15: 文档和发布 | 10 | 待开始 | ⏳ PENDING |
| **总计** | **64** | **持续进行** | **8%完成** |

## 风险与挑战

### 技术风险
1. **API稳定性**: 不同数据源API可靠性差异大
2. **数据质量**: 免费数据源可能有缺失或错误
3. **时区处理**: 跨时区数据同步复杂

### 解决方案
1. 实现重连机制和降级方案
2. 数据验证和清洗机制
3. 统一使用UTC时区,明确转换规则

## 参考资料

- [设计文档](../design_doc.md): 完整的架构设计和实施规划
- [Alpaca API文档](https://alpaca.markets/docs/): 美股数据源
- [Futu OpenAPI文档](https://openapi.futunn.com/): 港股数据源
- [CCXT文档](https://github.com/ccxt/ccxt): 加密货币统一接口

---

**最后更新**: 2025-10-26
**当前版本**: v2.0.0 (准备中)
**目标版本**: v2.1.0 (美股支持)
