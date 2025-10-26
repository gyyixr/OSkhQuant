#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置向导工具
引导用户完成市场选择和API配置
"""

import json
import os
import sys
from typing import Dict, Optional
from getpass import getpass

# 添加父目录到路径以便导入khConfig
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from khConfig import KhConfig
except ImportError:
    print("警告: 无法导入khConfig模块,将使用基础加密功能")
    KhConfig = None


class ConfigWizard:
    """配置向导"""
    
    MARKET_INFO = {
        'china_a_stock': {
            'name': 'A股市场',
            'provider': 'miniQMT',
            'needs_api_key': False,
            'description': '中国A股市场,使用MiniQMT数据源'
        },
        'us_stock': {
            'name': '美股市场',
            'provider': 'alpaca',
            'needs_api_key': True,
            'description': '美国股票市场,使用Alpaca API'
        },
        'hk_stock': {
            'name': '港股市场',
            'provider': 'futu',
            'needs_api_key': True,
            'description': '香港股票市场,使用富途OpenAPI'
        },
        'cryptocurrency': {
            'name': '加密货币市场',
            'provider': 'binance',
            'needs_api_key': True,
            'description': '加密货币市场,使用币安API'
        }
    }
    
    def __init__(self):
        self.config = {}
    
    def run(self) -> Dict:
        """运行配置向导"""
        print("="* 60)
        print("OSkhQuant 多市场配置向导")
        print("=" * 60)
        print()
        
        # 步骤1: 选择市场
        market_type = self.select_market()
        
        # 步骤2: 配置数据源
        data_source = self.configure_data_source(market_type)
        
        # 步骤3: 配置回测参数
        backtest = self.configure_backtest(market_type)
        
        # 步骤4: 配置风控参数
        risk = self.configure_risk(market_type)
        
        # 组装配置
        self.config = {
            'market': {
                'type': market_type,
                'name': self.MARKET_INFO[market_type]['name']
            },
            'data_source': data_source,
            'backtest': backtest,
            'risk': risk
        }
        
        return self.config
    
    def select_market(self) -> str:
        """选择市场"""
        print("步骤 1/4: 选择市场类型")
        print("-" * 60)
        
        markets = list(self.MARKET_INFO.keys())
        for i, market in enumerate(markets, 1):
            info = self.MARKET_INFO[market]
            print(f"  {i}. {info['name']:15s} - {info['description']}")
        
        print()
        while True:
            try:
                choice = input("请选择市场 (1-4) [1]: ").strip() or "1"
                index = int(choice) - 1
                if 0 <= index < len(markets):
                    selected = markets[index]
                    print(f"\n✓ 已选择: {self.MARKET_INFO[selected]['name']}\n")
                    return selected
                else:
                    print("❌ 无效的选择,请重试")
            except ValueError:
                print("❌ 请输入数字")
    
    def configure_data_source(self, market_type: str) -> Dict:
        """配置数据源"""
        print("步骤 2/4: 配置数据源")
        print("-" * 60)
        
        info = self.MARKET_INFO[market_type]
        config = {
            'provider': info['provider']
        }
        
        # A股市场配置
        if market_type == 'china_a_stock':
            account_id = input("请输入QMT账号ID [可选]: ").strip()
            if account_id:
                config['account_id'] = account_id
            
            mini_qmt_path = input("请输入MiniQMT数据路径 [可选]: ").strip()
            if mini_qmt_path:
                config['mini_qmt_path'] = mini_qmt_path
        
        # 美股市场配置
        elif market_type == 'us_stock':
            print("\n提示: 您需要Alpaca账号和API密钥")
            print("注册地址: https://alpaca.markets\n")
            
            use_paper = input("是否使用模拟盘? (y/n) [y]: ").strip().lower() or 'y'
            if use_paper == 'y':
                config['endpoint'] = 'https://paper-api.alpaca.markets'
            else:
                config['endpoint'] = 'https://api.alpaca.markets'
            
            api_key = input("请输入Alpaca API Key: ").strip()
            api_secret = getpass("请输入Alpaca API Secret: ").strip()
            
            if api_key and api_secret:
                credentials = {
                    'api_key': api_key,
                    'api_secret': api_secret
                }
                config['credentials_encrypted'] = self.encrypt_credentials(credentials)
        
        # 港股市场配置
        elif market_type == 'hk_stock':
            print("\n提示: 您需要富途OpenAPI")
            print("文档: https://openapi.futunn.com\n")
            
            host = input("FutuOpenD 地址 [127.0.0.1]: ").strip() or '127.0.0.1'
            port = input("FutuOpenD 端口 [11111]: ").strip() or '11111'
            
            config['host'] = host
            config['port'] = int(port)
            
            api_key = input("请输入Futu API Key [可选]: ").strip()
            if api_key:
                api_secret = getpass("请输入Futu API Secret: ").strip()
                credentials = {
                    'api_key': api_key,
                    'api_secret': api_secret
                }
                config['credentials_encrypted'] = self.encrypt_credentials(credentials)
        
        # 加密货币市场配置
        elif market_type == 'cryptocurrency':
            print("\n提示: 您需要币安账号和API密钥")
            print("注册地址: https://www.binance.com\n")
            
            use_testnet = input("是否使用测试网? (y/n) [y]: ").strip().lower() or 'y'
            if use_testnet == 'y':
                config['endpoint'] = 'https://testnet.binance.vision'
                config['testnet'] = True
            else:
                config['endpoint'] = 'https://api.binance.com'
                config['testnet'] = False
            
            api_key = input("请输入Binance API Key: ").strip()
            api_secret = getpass("请输入Binance API Secret: ").strip()
            
            if api_key and api_secret:
                credentials = {
                    'api_key': api_key,
                    'api_secret': api_secret
                }
                config['credentials_encrypted'] = self.encrypt_credentials(credentials)
        
        print("\n✓ 数据源配置完成\n")
        return config
    
    def configure_backtest(self, market_type: str) -> Dict:
        """配置回测参数"""
        print("步骤 3/4: 配置回测参数")
        print("-" * 60)
        
        # 初始资金
        if market_type == 'china_a_stock':
            default_capital = '1000000'
        elif market_type in ['us_stock', 'cryptocurrency']:
            default_capital = '100000'
        else:  # hk_stock
            default_capital = '1000000'
        
        init_capital = input(f"初始资金 [{default_capital}]: ").strip() or default_capital
        
        config = {
            'init_capital': float(init_capital),
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }
        
        # 交易成本配置
        print("\n配置交易成本:")
        if market_type == 'china_a_stock':
            commission = input("佣金费率 [0.0003]: ").strip() or '0.0003'
            min_commission = input("最低佣金 [5.0]: ").strip() or '5.0'
            
            config['trade_cost'] = {
                'commission_rate': float(commission),
                'min_commission': float(min_commission),
                'stamp_tax_rate': 0.001,
                'transfer_fee_rate': 0.00002
            }
        
        elif market_type == 'us_stock':
            commission = input("每股佣金 [0.0]: ").strip() or '0.0'
            
            config['trade_cost'] = {
                'commission_per_share': float(commission),
                'sec_fee_rate': 0.0000278,
                'finra_taf_rate': 0.000166,
                'min_commission': 0.0
            }
        
        elif market_type == 'hk_stock':
            commission = input("佣金费率 [0.0025]: ").strip() or '0.0025'
            min_commission = input("最低佣金 [50.0]: ").strip() or '50.0'
            
            config['trade_cost'] = {
                'commission_rate': float(commission),
                'min_commission': float(min_commission),
                'stamp_duty_rate': 0.001,
                'trading_levy_rate': 0.000027,
                'trading_fee_rate': 0.00005,
                'settlement_fee_rate': 0.00002
            }
        
        elif market_type == 'cryptocurrency':
            has_bnb = input("是否持有BNB享受折扣? (y/n) [n]: ").strip().lower() or 'n'
            
            config['trade_cost'] = {
                'maker_fee_rate': 0.001,
                'taker_fee_rate': 0.001,
                'bnb_discount': 0.75,
                'has_bnb': has_bnb == 'y'
            }
        
        print("\n✓ 回测参数配置完成\n")
        return config
    
    def configure_risk(self, market_type: str) -> Dict:
        """配置风控参数"""
        print("步骤 4/4: 配置风控参数")
        print("-" * 60)
        
        max_position = input("最大仓位比例 [0.95]: ").strip() or '0.95'
        single_stock = input("单股最大仓位 [0.30]: ").strip() or '0.30'
        
        config = {
            'max_position_pct': float(max_position),
            'single_stock_limit': float(single_stock)
        }
        
        # 市场特定风控
        if market_type == 'us_stock':
            pdt_check = input("启用PDT规则检查? (y/n) [y]: ").strip().lower() or 'y'
            config['pdt_check_enabled'] = pdt_check == 'y'
            config['min_account_value_for_pdt'] = 25000
        
        elif market_type == 'hk_stock':
            config['check_lot_size'] = True
            config['check_tick_size'] = True
        
        elif market_type == 'cryptocurrency':
            volatility = input("波动率限制 [0.15]: ").strip() or '0.15'
            config['check_min_notional'] = True
            config['volatility_limit'] = float(volatility)
        
        print("\n✓ 风控参数配置完成\n")
        return config
    
    def encrypt_credentials(self, credentials: Dict) -> str:
        """加密API凭证"""
        if KhConfig is not None:
            try:
                # 使用khConfig的加密功能
                from cryptography.fernet import Fernet
                import base64
                
                # 生成临时密钥
                key = Fernet.generate_key()
                fernet = Fernet(key)
                encrypted = fernet.encrypt(json.dumps(credentials).encode())
                
                # 注意: 实际使用时应该使用khConfig的密钥管理
                return base64.b64encode(encrypted).decode()
            except Exception as e:
                print(f"⚠️  加密失败: {e}")
                print("凭证将以明文存储,请手动加密!")
                return json.dumps(credentials)
        else:
            print("⚠️  无法加密凭证,将以明文存储")
            print("请在实际使用前手动加密!")
            return json.dumps(credentials)
    
    def save_config(self, filename: str):
        """保存配置到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"\n✓ 配置已保存到: {filename}")
            return True
        except Exception as e:
            print(f"\n❌ 保存配置失败: {e}")
            return False
    
    def print_summary(self):
        """打印配置摘要"""
        print("\n" + "=" * 60)
        print("配置摘要")
        print("=" * 60)
        print(f"\n市场类型: {self.config['market']['name']}")
        print(f"数据提供商: {self.config['data_source']['provider']}")
        print(f"初始资金: {self.config['backtest']['init_capital']:,.2f}")
        print(f"最大仓位: {self.config['risk']['max_position_pct']:.1%}")
        print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='OSkhQuant配置向导',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='config.kh',
        help='输出配置文件路径 (默认: config.kh)'
    )
    
    parser.add_argument(
        '--template',
        '-t',
        choices=['a_stock', 'us_stock', 'hk_stock', 'crypto'],
        help='使用配置模板'
    )
    
    args = parser.parse_args()
    
    # 使用模板
    if args.template:
        template_map = {
            'a_stock': 'config/config_template_a_stock.json',
            'us_stock': 'config/config_template_us_stock.json',
            'hk_stock': 'config/config_template_hk_stock.json',
            'crypto': 'config/config_template_crypto.json'
        }
        
        template_file = template_map.get(args.template)
        if template_file and os.path.exists(template_file):
            import shutil
            shutil.copy(template_file, args.output)
            print(f"✓ 已从模板创建配置: {args.output}")
            print(f"  模板: {template_file}")
            print("\n请编辑配置文件并填写您的API凭证")
            return 0
        else:
            print(f"❌ 模板文件不存在: {template_file}")
            return 1
    
    # 交互式向导
    wizard = ConfigWizard()
    
    try:
        # 运行向导
        wizard.run()
        
        # 显示摘要
        wizard.print_summary()
        
        # 保存配置
        if wizard.save_config(args.output):
            print("\n配置完成! 您可以使用以下命令验证配置:")
            print(f"  python tools/check_dependencies.py --config {args.output}")
            return 0
        else:
            return 1
    
    except KeyboardInterrupt:
        print("\n\n配置已取消")
        return 1
    except Exception as e:
        print(f"\n❌ 配置过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
