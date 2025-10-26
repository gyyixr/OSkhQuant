# 加密货币交易指南

本指南介绍如何使用 OSkhQuant 进行加密货币量化交易。

---

## 目录

1. [功能概览](#功能概览)
2. [快速开始](#快速开始)
3. [配置说明](#配置说明)
4. [API密钥获取](#api密钥获取)
5. [示例策略](#示例策略)
6. [常见问题](#常见问题)

---

## 功能概览

OSkhQuant 的加密货币适配器 (`CryptoAdapter`) 支持以下功能:

✅ **数据获取**
- 历史K线数据 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w等)
- 实时行情快照
- 支持多个交易对

✅ **交易功能**
- 市价单/限价单
- 订单查询和撤单
- 账户信息查询
- 持仓查询

✅ **市场特性**
- 7x24小时交易
- 支持Binance、CCXT等多个数据源
- 自动数据标准化

---

## 快速开始

### 1. 安装依赖

```bash
# 安装加密货币相关依赖
pip install -r requirements-crypto.txt
```

这将安装:
- `ccxt>=4.0.0` - 统一的加密货币交易所API
- `python-binance>=1.0.0` - Binance官方Python SDK
- `websockets>=11.0.0` - WebSocket支持

### 2. 配置API密钥

复制配置模板:

```bash
cp config/config_template_cryptocurrency.json my_crypto_config.json
```

编辑 `my_crypto_config.json`,填入您的API密钥:

```json
{
    "market": {
        "type": "cryptocurrency",
        "name": "加密货币市场"
    },
    "data_source": {
        "provider": "binance",
        "endpoint": "https://api.binance.com",
        "api_key": "YOUR_BINANCE_API_KEY",
        "api_secret": "YOUR_BINANCE_API_SECRET",
        "testnet": false
    }
}
```

### 3. 测试连接

运行测试工具验证配置:

```bash
python tools/crypto_test.py
```

---

## 配置说明

### 完整配置示例

```json
{
    "market": {
        "type": "cryptocurrency",
        "name": "加密货币市场"
    },
    "data_source": {
        "provider": "binance",
        "endpoint": "https://api.binance.com",
        "api_key": "YOUR_API_KEY",
        "api_secret": "YOUR_API_SECRET",
        "testnet": false
    },
    "system": {
        "run_mode": "backtest",
        "session_id": 0,
        "check_interval": 1
    },
    "account": {
        "account_id": "binance_account",
        "account_type": "SPOT_ACCOUNT"
    },
    "backtest": {
        "start_time": "20240101",
        "end_time": "20241231",
        "init_capital": 10000,
        "benchmark": "CRYPTO.BTC.USDT",
        "trade_cost": {
            "maker_fee_rate": 0.001,
            "taker_fee_rate": 0.001,
            "min_commission": 0.0,
            "slippage": 0.001
        }
    },
    "data": {
        "kline_period": "1h",
        "symbol_list": [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT"
        ]
    },
    "risk": {
        "position_limit": 0.9,
        "order_limit": 10000,
        "loss_limit": 0.15,
        "max_volatility": 0.1,
        "min_notional": 10.0
    }
}
```

### 关键参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `provider` | 数据提供商 (`binance`/`ccxt`) | `binance` |
| `testnet` | 是否使用测试网 | `false` |
| `maker_fee_rate` | Maker手续费率 | 0.001 (0.1%) |
| `taker_fee_rate` | Taker手续费率 | 0.001 (0.1%) |
| `bnb_discount` | BNB抵扣折扣 | 0.75 (25% off) |
| `min_notional` | 最小交易额(USDT) | 10.0 |

---

## API密钥获取

### Binance (币安)

1. 登录 [Binance](https://www.binance.com/)
2. 进入 "API Management" (API管理)
3. 创建新的API密钥
4. 设置权限:
   - ✅ **Enable Reading** (允许读取)
   - ✅ **Enable Spot & Margin Trading** (现货和保证金交易,可选)
   - ❌ **Enable Withdrawals** (不建议开启提现权限)
5. 绑定IP白名单(推荐)
6. 妥善保存API Key和Secret Key

### 测试网络

币安提供测试网供开发使用:

- **测试网地址**: https://testnet.binance.vision/
- **测试网API**: https://testnet.binance.vision/api
- 免费获取测试资金
- 配置中设置 `"testnet": true`

---

## 示例策略

### 双均线策略

参考 `strategies/加密货币双均线策略.py`:

```python
def init(context):
    """策略初始化"""
    context.symbol_list = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    context.fast_period = 5   # 快线周期
    context.slow_period = 20  # 慢线周期
    context.position_pct = 0.3  # 单个标的仓位比例

def handle_bar(context):
    """K线更新时调用"""
    for symbol in context.symbol_list:
        # 获取历史数据
        df = context.get_market_data(
            symbols=[symbol],
            period='1h',
            count=context.slow_period + 10
        )
        
        # 计算双均线
        df['ma_fast'] = df['close'].rolling(context.fast_period).mean()
        df['ma_slow'] = df['close'].rolling(context.slow_period).mean()
        
        # 获取信号
        ma_fast_current = df['ma_fast'].iloc[-1]
        ma_slow_current = df['ma_slow'].iloc[-1]
        ma_fast_previous = df['ma_fast'].iloc[-2]
        ma_slow_previous = df['ma_slow'].iloc[-2]
        
        # 金叉买入
        if ma_fast_previous <= ma_slow_previous and ma_fast_current > ma_slow_current:
            # 买入逻辑
            pass
        
        # 死叉卖出
        elif ma_fast_previous >= ma_slow_previous and ma_fast_current < ma_slow_current:
            # 卖出逻辑
            pass
```

### 运行回测

```python
from adapters.crypto_adapter import CryptoAdapter
import json

# 加载配置
with open('my_crypto_config.json', 'r') as f:
    config = json.load(f)

# 创建适配器
adapter = CryptoAdapter(config)

# 连接
if adapter.connect():
    # 获取历史数据
    df = adapter.get_market_data(
        symbol='BTCUSDT',
        period='1d',
        count=100
    )
    
    print(df.head())
    
    adapter.disconnect()
```

---

## 常见问题

### Q1: 支持哪些交易所?

目前主要支持:
- **Binance (币安)**: 通过 `python-binance`
- **其他交易所**: 通过 `ccxt` (支持100+交易所)

### Q2: 如何切换到其他交易所?

使用CCXT provider:

```json
{
    "data_source": {
        "provider": "ccxt",
        "exchange_id": "okx",  // 或 "huobi", "gate" 等
        "api_key": "YOUR_KEY",
        "api_secret": "YOUR_SECRET"
    }
}
```

### Q3: 手续费如何计算?

- **Maker费率**: 挂单成交,通常较低 (0.1%)
- **Taker费率**: 吃单成交,通常较高 (0.1%)
- **BNB折扣**: 使用BNB支付手续费可享25%折扣

### Q4: 最小交易额限制?

不同交易对有不同的最小交易额(Notional):
- BTC/USDT: 通常 $10
- 小币种: 可能更低

配置中设置 `min_notional` 进行过滤。

### Q5: 如何处理24小时交易?

加密货币7x24小时交易,策略需要考虑:
- 使用时间过滤器避免特定时段交易
- 设置止损避免剧烈波动
- 监控系统稳定性

### Q6: 测试网和正式网的区别?

| 特性 | 测试网 | 正式网 |
|------|--------|--------|
| 资金 | 虚拟资金 | 真实资金 |
| 风险 | 无风险 | 有风险 |
| 数据 | 测试数据 | 真实数据 |
| 建议 | 策略验证 | 实盘交易 |

### Q7: 如何保证API密钥安全?

1. **不要提交到版本控制**: 添加到 `.gitignore`
2. **使用加密存储**: 使用 `khConfig` 的加密功能
3. **设置IP白名单**: 限制API访问来源
4. **最小权限原则**: 只开启必要的API权限
5. **定期更换**: 定期更新API密钥

### Q8: 遇到 API 限流怎么办?

币安等交易所有API调用频率限制:
- 使用 `enableRateLimit=True` (CCXT)
- 减少数据请求频率
- 缓存历史数据
- 使用WebSocket获取实时数据

---

## 风险提示

⚠️ **加密货币交易风险极高,请务必注意**:

1. **市场风险**: 加密货币波动性极大,可能短时间大幅下跌
2. **技术风险**: 策略代码可能存在bug,建议充分测试
3. **API风险**: 网络中断、API故障可能导致交易失败
4. **安全风险**: 妥善保管API密钥,防止账户被盗
5. **资金风险**: 建议使用少量资金测试,切勿孤注一掷

**建议流程**:
1. 先在测试网验证策略
2. 用小额资金实盘测试
3. 逐步增加资金规模
4. 持续监控和优化

---

## 更多资源

- [Binance API文档](https://binance-docs.github.io/apidocs/)
- [CCXT文档](https://docs.ccxt.com/)
- [配置指南](CONFIGURATION_GUIDE.md)
- [多市场策略开发](MULTIMARKET_STRATEGY_GUIDE.md)

---

如有问题,欢迎在GitHub提Issue或加入社区讨论!
