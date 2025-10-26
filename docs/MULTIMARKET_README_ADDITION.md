# 多市场支持功能 - README补充说明

> 本文档内容应添加到主README.md中,介绍新增的多市场支持功能

---

## 🌍 多市场支持 (NEW!)

OSkhQuant现已支持多个市场的量化交易!

### 支持的市场

| 市场 | 状态 | 数据源 | 说明 |
|------|------|--------|------|
| 🇨🇳 A股 | ✅ 已支持 | miniQMT | 沪深股票、ETF |
| 🇺🇸 美股 | 🔄 开发中 | Alpaca, Yahoo Finance | 纳斯达克、纽交所 |
| 🇭🇰 港股 | 📅 计划中 | 富途OpenAPI | 香港联交所 |
| ₿ 加密货币 | 📅 计划中 | Binance, CCXT | BTC, ETH等 |

### 快速开始

#### 1. 使用A股市场 (默认)

```python
from khConfig import KhConfig
from adapters import MarketRegistry

# 加载A股配置
config = KhConfig('config/config_template_a_stock.json')

# 获取适配器
adapter = MarketRegistry.get_adapter('china_a_stock', 
                                     config.get_adapter_config())

# 连接并使用
adapter.connect()
```

#### 2. 标的代码标准化

不同市场使用统一的标准化格式:

```python
# A股
'000001.SZ' → 'CN.000001.SZ'
'600000.SH' → 'CN.600000.SH'

# 美股 (即将支持)
'AAPL' → 'US.AAPL'
'TSLA' → 'US.TSLA'

# 港股 (即将支持)
'00700' → 'HK.00700'

# 加密货币 (即将支持)
'BTCUSDT' → 'CRYPTO.BTC.USDT'
```

#### 3. 配置文件示例

```json
{
    "market": {
        "type": "china_a_stock",
        "name": "A股市场"
    },
    "data_source": {
        "provider": "miniQMT",
        "api_key": "",
        "api_secret": ""
    },
    "backtest": {
        "start_time": "20240101",
        "end_time": "20241231",
        "init_capital": 1000000
    },
    "data": {
        "stock_list": ["000001.SZ", "600000.SH"]
    }
}
```

### 主要特性

✅ **统一接口** - 所有市场使用相同的适配器接口  
✅ **数据标准化** - 代码、时间、字段自动标准化  
✅ **安全加密** - API凭证加密存储  
✅ **向后兼容** - 现有A股策略无需修改  
✅ **易于扩展** - 新增市场只需实现适配器

### 架构设计

```
策略层 (Strategy)
    ↓
框架层 (Framework)
    ↓
适配器层 (Market Adapters)
    ↓
数据源层 (Data Sources)
```

### 核心组件

1. **BaseMarketAdapter** - 市场适配器基类
2. **MarketRegistry** - 市场注册中心
3. **DataNormalizer** - 数据标准化工具
4. **KhConfig** - 多市场配置管理

### 文档

- 📖 [快速开始指南](docs/MULTIMARKET_QUICK_START.md)
- 📊 [实施进展](docs/MULTIMARKET_IMPLEMENTATION_PROGRESS.md)
- 📋 [项目状态](PROJECT_STATUS.md)

### 向后兼容性

✅ **现有策略完全兼容** - 无需任何修改即可继续使用  
✅ **配置格式兼容** - 支持新旧配置格式  
✅ **接口保持不变** - khPrice, khMA等函数正常使用

### 路线图

- **v2.1.0** (计划中) - 美股支持 (Alpaca API)
- **v2.2.0** (计划中) - 港股支持 (富途OpenAPI)
- **v2.3.0** (计划中) - 加密货币支持 (Binance)
- **v2.4.0** (计划中) - 跨市场策略支持

### 示例代码

查看示例配置文件:
- `config/config_template_a_stock.json` - A股配置
- `config/config_template_us_stock.json` - 美股配置
- `config/config_template_hk_stock.json` - 港股配置
- `config/config_template_cryptocurrency.json` - 加密货币配置

---

## 技术细节

### 适配器模式

```python
from adapters import BaseMarketAdapter, register_adapter

@register_adapter('my_market')
class MyMarketAdapter(BaseMarketAdapter):
    def connect(self):
        # 实现连接逻辑
        pass
    
    def get_market_data(self, symbols, period, start, end):
        # 实现数据获取
        pass
    
    # ... 实现其他抽象方法
```

### 数据标准化

```python
from adapters import DataNormalizer

# 标准化
standard = DataNormalizer.normalize_symbol('000001.SZ', 'china_a_stock')
# 结果: 'CN.000001.SZ'

# 反标准化
original = DataNormalizer.denormalize_symbol('CN.000001.SZ')
# 结果: '000001.SZ'

# 提取市场类型
market = DataNormalizer.extract_market_type('CN.000001.SZ')
# 结果: 'china_a_stock'
```

### API凭证加密

```python
from khConfig import KhConfig

config = KhConfig('my_config.json')

# 加密保存
credentials = {'api_key': 'xxx', 'api_secret': 'yyy'}
config.save_encrypted_credentials(credentials)

# 自动解密使用
adapter_config = config.get_adapter_config()
```

---

## 贡献指南

欢迎为多市场支持功能贡献代码!

1. Fork项目
2. 创建特性分支
3. 实现市场适配器
4. 提交Pull Request

详见 [贡献指南](CONTRIBUTING.md)

---

**多市场支持版本**: v2.0.0-alpha  
**基础架构**: ✅ 已完成  
**文档状态**: ✅ 完整
