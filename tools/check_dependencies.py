#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检测工具
用于检测当前环境是否安装了所选市场所需的依赖包
"""

import sys
import importlib
import json
from typing import Dict, List, Tuple

# 市场依赖映射
MARKET_DEPENDENCIES = {
    'china_a_stock': {
        'required': [
            'pandas',
            'numpy',
            'pytz',
            'holidays',
            'PyQt5',
            'cryptography'
        ],
        'optional': []
    },
    'us_stock': {
        'required': [
            'pandas',
            'numpy',
            'pytz',
            'holidays',
            'PyQt5',
            'cryptography',
            'alpaca_trade_api',
            'yfinance'
        ],
        'optional': []
    },
    'hk_stock': {
        'required': [
            'pandas',
            'numpy',
            'pytz',
            'holidays',
            'PyQt5',
            'cryptography',
            'futu'
        ],
        'optional': []
    },
    'cryptocurrency': {
        'required': [
            'pandas',
            'numpy',
            'pytz',
            'PyQt5',
            'cryptography',
            'binance'
        ],
        'optional': [
            'ccxt'
        ]
    }
}


def check_package(package_name: str) -> Tuple[bool, str]:
    """
    检查单个包是否已安装
    
    Args:
        package_name: 包名
        
    Returns:
        (是否安装, 版本号或错误信息)
    """
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, 'Not installed'


def check_market_dependencies(market_type: str) -> Dict[str, Dict]:
    """
    检查指定市场的依赖
    
    Args:
        market_type: 市场类型
        
    Returns:
        依赖检查结果
    """
    if market_type not in MARKET_DEPENDENCIES:
        return {
            'error': f'Unknown market type: {market_type}',
            'valid_markets': list(MARKET_DEPENDENCIES.keys())
        }
    
    deps = MARKET_DEPENDENCIES[market_type]
    results = {
        'market': market_type,
        'required': {},
        'optional': {},
        'missing_required': [],
        'missing_optional': [],
        'all_satisfied': True
    }
    
    # 检查必需依赖
    for pkg in deps['required']:
        installed, version = check_package(pkg)
        results['required'][pkg] = {
            'installed': installed,
            'version': version
        }
        if not installed:
            results['missing_required'].append(pkg)
            results['all_satisfied'] = False
    
    # 检查可选依赖
    for pkg in deps['optional']:
        installed, version = check_package(pkg)
        results['optional'][pkg] = {
            'installed': installed,
            'version': version
        }
        if not installed:
            results['missing_optional'].append(pkg)
    
    return results


def print_results(results: Dict):
    """打印检查结果"""
    if 'error' in results:
        print(f"\n❌ 错误: {results['error']}")
        print(f"有效的市场类型: {', '.join(results['valid_markets'])}")
        return
    
    print(f"\n{'='*60}")
    print(f"市场类型: {results['market']}")
    print(f"{'='*60}\n")
    
    # 打印必需依赖
    print("必需依赖:")
    print("-" * 60)
    for pkg, info in results['required'].items():
        status = "✅" if info['installed'] else "❌"
        version = info['version'] if info['installed'] else "未安装"
        print(f"  {status} {pkg:20s} {version}")
    
    # 打印可选依赖
    if results['optional']:
        print("\n可选依赖:")
        print("-" * 60)
        for pkg, info in results['optional'].items():
            status = "✅" if info['installed'] else "⚠️"
            version = info['version'] if info['installed'] else "未安装"
            print(f"  {status} {pkg:20s} {version}")
    
    # 打印总结
    print("\n" + "=" * 60)
    if results['all_satisfied']:
        print("✅ 所有必需依赖已满足!")
    else:
        print("❌ 缺少以下必需依赖:")
        for pkg in results['missing_required']:
            print(f"  - {pkg}")
        print(f"\n安装命令:")
        print(f"  pip install {' '.join(results['missing_required'])}")
    
    if results['missing_optional']:
        print("\n⚠️  缺少以下可选依赖:")
        for pkg in results['missing_optional']:
            print(f"  - {pkg}")


def check_all_markets() -> Dict[str, Dict]:
    """检查所有市场的依赖"""
    all_results = {}
    for market in MARKET_DEPENDENCIES.keys():
        all_results[market] = check_market_dependencies(market)
    return all_results


def print_all_results(all_results: Dict[str, Dict]):
    """打印所有市场的检查结果"""
    print("\n" + "=" * 60)
    print("所有市场依赖检查")
    print("=" * 60)
    
    for market, results in all_results.items():
        status = "✅" if results['all_satisfied'] else "❌"
        missing = len(results['missing_required'])
        print(f"\n{status} {market:20s} 缺失: {missing}个必需依赖")
        
        if results['missing_required']:
            print(f"   缺少: {', '.join(results['missing_required'])}")


def load_config_and_check(config_file: str = None) -> Dict:
    """
    从配置文件加载市场类型并检查依赖
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        检查结果
    """
    if not config_file:
        return {'error': 'No config file specified'}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        market_type = config.get('market', {}).get('type', 'china_a_stock')
        return check_market_dependencies(market_type)
    
    except FileNotFoundError:
        return {'error': f'Config file not found: {config_file}'}
    except json.JSONDecodeError:
        return {'error': f'Invalid JSON in config file: {config_file}'}
    except Exception as e:
        return {'error': f'Error loading config: {str(e)}'}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='检查OSkhQuant多市场依赖是否已安装',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查A股市场依赖
  python check_dependencies.py --market china_a_stock
  
  # 检查美股市场依赖
  python check_dependencies.py --market us_stock
  
  # 检查所有市场依赖
  python check_dependencies.py --all
  
  # 从配置文件检查
  python check_dependencies.py --config config.kh
        """
    )
    
    parser.add_argument(
        '--market',
        choices=list(MARKET_DEPENDENCIES.keys()),
        help='要检查的市场类型'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='检查所有市场的依赖'
    )
    parser.add_argument(
        '--config',
        help='从配置文件读取市场类型'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='以JSON格式输出结果'
    )
    
    args = parser.parse_args()
    
    # 确定检查模式
    if args.all:
        results = check_all_markets()
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_all_results(results)
    elif args.config:
        results = load_config_and_check(args.config)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_results(results)
    elif args.market:
        results = check_market_dependencies(args.market)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_results(results)
    else:
        parser.print_help()
        sys.exit(1)
    
    # 返回退出码
    if isinstance(results, dict):
        if 'error' in results:
            sys.exit(1)
        elif not results.get('all_satisfied', True):
            sys.exit(1)
    else:
        # 检查所有市场时,如果任何一个不满足则返回1
        for r in results.values():
            if not r.get('all_satisfied', True):
                sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
