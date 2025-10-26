# 多市场配置指南

## 概述

本指南详细说明如何为不同市场配置OSkhQuant系统,包括市场选择、API凭证设置、交易成本配置等。

## 配置文件结构

OSkhQuant使用`.kh`格式的JSON配置文件,基本结构如下:

```json
{
    "market": {
        "type": "市场类型",
        "name": "市场名称"
    },
    "data_source": {
        "provider": "数据提供商",
        "endpoint": "API端点",
        "credentials_encrypted": "加密的API凭证"
    },
    "backtest": {
        "init_capital": 初始资金,
        "start_date": "开始日期",
        "end_date": "结束日期",
        "trade_cost": {
            // 市场特定的交易成本配置
        }
    },
    "risk": {
        // 风控参数
    },
    "strategy": {
        // 策略参数
    }
}
```

## A股市场配置

### 基础配置

```json
{
    "market": {
        "type": "china_a_stock",
        "name": "A股市场"
    },
    "data_source": {
        "provider": "miniQMT",
        "account_id": "您的QMT账号",
        "mini_qmt_path": "C:/国金QMT交易端/userdata_mini"
    },
    "backtest": {
        "init_capital": 1000000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "trade_cost": {
            "commission_rate": 0.0003,
            "min_commission": 5.0,
            "stamp_tax_rate": 0.001,
            "transfer_fee_rate": 0.00002
        }
    },
    "risk": {
        "max_position_pct": 0.95,
        "single_stock_limit": 0.30,
        "stop_loss_pct": 0.10
    }
}
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `market.type` | 必须为`china_a_stock` | - |
| `data_source.provider` | 必须为`miniQMT` | - |
| `data_source.account_id` | QMT账号ID | - |
| `data_source.mini_qmt_path` | MiniQMT数据路径 | - |
| `trade_cost.commission_rate` | 佣金费率 | 0.0003 |
| `trade_cost.min_commission` | 最低佣金 | 5.0 |
| `trade_cost.stamp_tax_rate` | 印花税费率(仅卖出) | 0.001 |
| `trade_cost.transfer_fee_rate` | 过户费费率(仅上海) | 0.00002 |

### 完整示例

参考文件: `config/config_template_a_stock.json`

## 美股市场配置

### 基础配置 (Alpaca)

```json
{
    "market": {
        "type": "us_stock",
        "name": "美股市场"
    },
    "data_source": {
        "provider": "alpaca",
        "endpoint": "https://paper-api.alpaca.markets",
        "credentials_encrypted": "加密后的API密钥"
    },
    "backtest": {
        "init_capital": 100000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "trade_cost": {
            "commission_per_share": 0.0,
            "sec_fee_rate": 0.0000278,
            "finra_taf_rate": 0.000166,
            "min_commission": 0.0
        }
    },
    "risk": {
        "max_position_pct": 1.0,
        "single_stock_limit": 0.50,
        "pdt_check_enabled": true,
        "min_account_value_for_pdt": 25000
    }
}
```

### API凭证加密

由于API密钥敏感,需要加密存储:

```python
from khConfig import KhConfig

config = KhConfig('config.kh')

# 加密API凭证
credentials = {
    'api_key': 'your_alpaca_api_key',
    'api_secret': 'your_alpaca_api_secret'
}

encrypted = config.encrypt_credentials(credentials)

# 保存到配置文件
config.config_dict['data_source']['credentials_encrypted'] = encrypted
config.save()
```

或使用命令行工具:

```bash
python tools/encrypt_credentials.py \
    --market us_stock \
    --api-key YOUR_API_KEY \
    --api-secret YOUR_API_SECRET \
    --config config.kh
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `market.type` | 必须为`us_stock` | - |
| `data_source.provider` | 支持`alpaca`, `yahoo_finance` | `alpaca` |
| `data_source.endpoint` | API端点,实盘/模拟盘不同 | - |
| `trade_cost.commission_per_share` | 每股佣金 | 0.0 |
| `trade_cost.sec_fee_rate` | SEC费率(仅卖出) | 0.0000278 |
| `trade_cost.finra_taf_rate` | FINRA TAF费率(仅卖出) | 0.000166 |
| `risk.pdt_check_enabled` | 是否启用PDT规则检查 | true |
| `risk.min_account_value_for_pdt` | PDT最低账户价值 | 25000 |

### 模拟盘 vs 实盘

**模拟盘 (Paper Trading):**
```json
{
    "data_source": {
        "endpoint": "https://paper-api.alpaca.markets"
    }
}
```

**实盘 (Live Trading):**
```json
{
    "data_source": {
        "endpoint": "https://api.alpaca.markets"
    }
}
```

### Yahoo Finance备选配置

如果没有Alpaca账号,可以使用Yahoo Finance获取数据(仅回测):

```json
{
    "market": {
        "type": "us_stock",
        "name": "美股市场"
    },
    "data_source": {
        "provider": "yahoo_finance",
        "use_adjusted_close": true
    },
    "backtest": {
        "init_capital": 100000,
        "trade_cost": {
            "commission_per_share": 0.005,
            "sec_fee_rate": 0.0000278,
            "finra_taf_rate": 0.000166
        }
    }
}
```

### 完整示例

参考文件: `config/config_template_us_stock.json`

## 港股市场配置

### 基础配置 (Futu OpenAPI)

```json
{
    "market": {
        "type": "hk_stock",
        "name": "港股市场"
    },
    "data_source": {
        "provider": "futu",
        "host": "127.0.0.1",
        "port": 11111,
        "credentials_encrypted": "加密后的API密钥"
    },
    "backtest": {
        "init_capital": 1000000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "trade_cost": {
            "commission_rate": 0.0025,
            "min_commission": 50.0,
            "stamp_duty_rate": 0.001,
            "trading_levy_rate": 0.000027,
            "trading_fee_rate": 0.00005,
            "settlement_fee_rate": 0.00002
        }
    },
    "risk": {
        "max_position_pct": 0.95,
        "single_stock_limit": 0.40,
        "check_lot_size": true,
        "check_tick_size": true
    }
}
```

### Futu OpenAPI设置

1. **安装FutuOpenD**
   
   下载并安装富途OpenAPI客户端

2. **启动FutuOpenD**
   
   ```bash
   # Windows
   FutuOpenD.exe -cfg_file futu_config.xml
   
   # Mac/Linux
   ./FutuOpenD -cfg_file futu_config.xml
   ```

3. **配置连接**
   
   ```json
   {
       "data_source": {
           "host": "127.0.0.1",
           "port": 11111,
           "credentials_encrypted": "encrypted_credentials"
       }
   }
   ```

### API凭证配置

```python
from khConfig import KhConfig

config = KhConfig('config_hk.kh')

credentials = {
    'api_key': 'your_futu_api_key',
    'api_secret': 'your_futu_api_secret',
    'rsa_key_file': '/path/to/rsa_key.pem'
}

encrypted = config.encrypt_credentials(credentials)
config.config_dict['data_source']['credentials_encrypted'] = encrypted
config.save()
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `market.type` | 必须为`hk_stock` | - |
| `data_source.provider` | 必须为`futu` | - |
| `data_source.host` | FutuOpenD服务地址 | 127.0.0.1 |
| `data_source.port` | FutuOpenD服务端口 | 11111 |
| `trade_cost.commission_rate` | 佣金费率 | 0.0025 |
| `trade_cost.min_commission` | 最低佣金(港币) | 50.0 |
| `trade_cost.stamp_duty_rate` | 印花税 | 0.001 |
| `trade_cost.trading_levy_rate` | 交易征费 | 0.000027 |
| `trade_cost.trading_fee_rate` | 交易费 | 0.00005 |
| `trade_cost.settlement_fee_rate` | 结算费 | 0.00002 |
| `risk.check_lot_size` | 是否检查手数 | true |
| `risk.check_tick_size` | 是否检查价格档位 | true |

### 手数和价格档位

港股特有的交易规则:

```json
{
    "market_specific": {
        "lot_sizes": {
            "00700": 100,
            "09988": 50
        },
        "tick_sizes": [
            {"min_price": 0.01, "max_price": 0.25, "tick": 0.001},
            {"min_price": 0.25, "max_price": 0.50, "tick": 0.005},
            {"min_price": 0.50, "max_price": 10.00, "tick": 0.01},
            {"min_price": 10.00, "max_price": 20.00, "tick": 0.02}
        ]
    }
}
```

### 完整示例

参考文件: `config/config_template_hk_stock.json`

## 加密货币市场配置

### 基础配置 (Binance)

```json
{
    "market": {
        "type": "cryptocurrency",
        "name": "加密货币市场"
    },
    "data_source": {
        "provider": "binance",
        "endpoint": "https://api.binance.com",
        "testnet": false,
        "credentials_encrypted": "加密后的API密钥"
    },
    "backtest": {
        "init_capital": 100000,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "trade_cost": {
            "maker_fee_rate": 0.001,
            "taker_fee_rate": 0.001,
            "bnb_discount": 0.75,
            "has_bnb": false
        }
    },
    "risk": {
        "max_position_pct": 0.90,
        "single_position_limit": 0.30,
        "check_min_notional": true,
        "volatility_limit": 0.15
    }
}
```

### API凭证配置

```python
from khConfig import KhConfig

config = KhConfig('config_crypto.kh')

credentials = {
    'api_key': 'your_binance_api_key',
    'api_secret': 'your_binance_api_secret'
}

encrypted = config.encrypt_credentials(credentials)
config.config_dict['data_source']['credentials_encrypted'] = encrypted
config.save()
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `market.type` | 必须为`cryptocurrency` | - |
| `data_source.provider` | 支持`binance`, `ccxt` | `binance` |
| `data_source.testnet` | 是否使用测试网 | false |
| `trade_cost.maker_fee_rate` | Maker费率 | 0.001 |
| `trade_cost.taker_fee_rate` | Taker费率 | 0.001 |
| `trade_cost.bnb_discount` | BNB折扣率 | 0.75 |
| `trade_cost.has_bnb` | 是否持有BNB | false |
| `risk.check_min_notional` | 检查最小名义价值 | true |
| `risk.volatility_limit` | 波动率限制 | 0.15 |

### 测试网配置

Binance测试网用于开发和测试:

```json
{
    "data_source": {
        "endpoint": "https://testnet.binance.vision",
        "testnet": true
    }
}
```

测试网API密钥获取: https://testnet.binance.vision/

### CCXT多交易所支持

使用CCXT库支持多个交易所:

```json
{
    "data_source": {
        "provider": "ccxt",
        "exchange": "okx",
        "endpoint": "https://www.okx.com",
        "credentials_encrypted": "encrypted_credentials"
    }
}
```

支持的交易所: binance, okx, huobi, bybit, gate等100+

### 完整示例

参考文件: `config/config_template_crypto.json`

## 高级配置

### 多策略配置

同时运行多个策略:

```json
{
    "strategies": [
        {
            "name": "双均线策略",
            "file": "strategies/dual_ma.py",
            "enabled": true,
            "capital_allocation": 0.5,
            "params": {
                "fast_period": 5,
                "slow_period": 20
            }
        },
        {
            "name": "动量策略",
            "file": "strategies/momentum.py",
            "enabled": true,
            "capital_allocation": 0.5,
            "params": {
                "lookback_period": 20
            }
        }
    ]
}
```

### 数据缓存配置

优化数据获取性能:

```json
{
    "data_cache": {
        "enabled": true,
        "cache_dir": "./cache",
        "ttl_seconds": 3600,
        "max_size_mb": 1000
    }
}
```

### 日志配置

```json
{
    "logging": {
        "level": "INFO",
        "file": "./logs/oskhquant.log",
        "max_size_mb": 50,
        "backup_count": 5,
        "console_output": true
    }
}
```

日志级别:
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 通知配置

交易通知推送:

```json
{
    "notification": {
        "enabled": true,
        "channels": [
            {
                "type": "email",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your_email@gmail.com",
                "password_encrypted": "encrypted_password",
                "recipients": ["trader@example.com"]
            },
            {
                "type": "webhook",
                "url": "https://your-webhook-url.com",
                "method": "POST"
            }
        ],
        "events": ["order_filled", "stop_loss_triggered", "daily_summary"]
    }
}
```

## 配置验证

### 使用Python验证

```python
from khConfig import KhConfig

config = KhConfig('config.kh')

# 验证市场配置
is_valid, errors = config.validate_market_config()

if is_valid:
    print("配置验证通过")
else:
    print("配置错误:")
    for error in errors:
        print(f"  - {error}")
```

### 使用命令行工具

```bash
python tools/validate_config.py config.kh
```

输出示例:
```
✓ 市场类型: us_stock
✓ 数据源提供商: alpaca
✓ API凭证: 已加密
✓ 交易成本配置: 完整
✓ 风控参数: 有效
✓ 回测参数: 有效

配置验证通过! ✓
```

## 配置迁移

### 从旧版本迁移

如果从单市场版本升级:

```python
from tools.config_migrator import migrate_config

# 自动迁移配置
migrate_config(
    old_config='old_config.kh',
    new_config='new_config.kh',
    market_type='china_a_stock'
)
```

### 批量创建配置

为不同市场创建配置:

```python
from tools.config_generator import ConfigGenerator

generator = ConfigGenerator()

# 生成A股配置
generator.create_config(
    market='china_a_stock',
    output='config_a_stock.kh',
    params={'init_capital': 1000000}
)

# 生成美股配置
generator.create_config(
    market='us_stock',
    output='config_us_stock.kh',
    params={'init_capital': 100000}
)
```

## 常见问题

### Q1: API凭证加密失败

**原因**: 缺少加密密钥或密钥文件损坏

**解决**:
```python
from khConfig import KhConfig

config = KhConfig('config.kh')
config._regenerate_encryption_key()
```

### Q2: 配置文件不生效

**原因**: JSON格式错误或路径错误

**解决**:
1. 使用JSON验证工具检查格式
2. 检查文件路径是否正确
3. 查看日志文件获取详细错误

### Q3: 多市场切换失败

**原因**: 适配器未正确注册

**解决**:
```python
from adapters.market_registry import MarketRegistry

# 查看已注册的市场
print(MarketRegistry.list_markets())

# 手动注册适配器
from adapters.us_stock_adapter import USStockAdapter
MarketRegistry.register('us_stock', USStockAdapter)
```

### Q4: 交易成本计算不准确

**原因**: 费率配置错误

**解决**: 参考对应市场的最新费率标准,更新配置文件

## 配置模板

系统提供以下配置模板:

- `config/config_template_a_stock.json` - A股市场模板
- `config/config_template_us_stock.json` - 美股市场模板  
- `config/config_template_hk_stock.json` - 港股市场模板
- `config/config_template_crypto.json` - 加密货币市场模板

使用模板:

```bash
# 复制模板
cp config/config_template_us_stock.json my_config.kh

# 编辑配置
nano my_config.kh

# 加密API凭证
python tools/encrypt_credentials.py --config my_config.kh

# 验证配置
python tools/validate_config.py my_config.kh
```

## 安全建议

1. **不要直接存储明文API密钥**: 始终使用加密存储
2. **定期轮换API密钥**: 特别是在生产环境
3. **限制API权限**: 只授予必要的权限
4. **使用IP白名单**: 在交易所设置IP限制
5. **备份配置文件**: 定期备份加密密钥和配置
6. **不要提交凭证到版本控制**: 添加到.gitignore

## 参考资料

- [市场适配器API文档](MARKET_ADAPTER_API.md)
- [多市场快速开始](MULTIMARKET_QUICK_START.md)
- [策略开发指南](MULTIMARKET_STRATEGY_GUIDE.md)
- [Alpaca API文档](https://alpaca.markets/docs/)
- [Futu OpenAPI文档](https://openapi.futunn.com/)
- [Binance API文档](https://binance-docs.github.io/apidocs/)
