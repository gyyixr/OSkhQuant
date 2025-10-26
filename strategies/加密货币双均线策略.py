# coding: utf-8
"""
加密货币双均线策略示例
演示如何使用CryptoAdapter进行加密货币量化交易
"""

import pandas as pd
from datetime import datetime


def init(context):
    """
    策略初始化
    
    Args:
        context: 策略上下文
    """
    # 设置交易对
    context.symbol_list = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    # 双均线参数
    context.fast_period = 5  # 快线周期
    context.slow_period = 20  # 慢线周期
    
    # 仓位控制
    context.position_pct = 0.3  # 每个交易对最多30%仓位
    
    print(f"策略初始化完成")
    print(f"交易对: {context.symbol_list}")
    print(f"快线周期: {context.fast_period}, 慢线周期: {context.slow_period}")


def handle_bar(context):
    """
    K线数据更新时调用
    
    Args:
        context: 策略上下文
    """
    # 遍历所有交易对
    for symbol in context.symbol_list:
        # 获取历史数据
        df = context.get_market_data(
            symbols=[symbol],
            period='1h',
            count=context.slow_period + 10
        )
        
        if df.empty or len(df) < context.slow_period:
            continue
        
        # 计算双均线
        df['ma_fast'] = df['close'].rolling(context.fast_period).mean()
        df['ma_slow'] = df['close'].rolling(context.slow_period).mean()
        
        # 获取最新两根K线的均线值
        ma_fast_current = df['ma_fast'].iloc[-1]
        ma_slow_current = df['ma_slow'].iloc[-1]
        ma_fast_previous = df['ma_fast'].iloc[-2]
        ma_slow_previous = df['ma_slow'].iloc[-2]
        
        # 当前价格
        current_price = df['close'].iloc[-1]
        
        # 获取当前持仓
        positions = context.get_positions()
        position = next((p for p in positions if p['symbol'] == symbol), None)
        
        # 金叉信号:快线上穿慢线
        if ma_fast_previous <= ma_slow_previous and ma_fast_current > ma_slow_current:
            # 如果没有持仓,则买入
            if position is None or position.get('volume', 0) <= 0:
                # 计算可用资金
                account = context.get_account_info()
                usdt_balance = next((b for b in account.get('balances', []) if b['asset'] == 'USDT'), None)
                
                if usdt_balance and usdt_balance['free'] > 0:
                    # 使用30%的USDT买入
                    usdt_to_use = usdt_balance['free'] * context.position_pct
                    volume = usdt_to_use / current_price
                    
                    # 下单买入
                    order = context.place_order(
                        symbol=symbol,
                        order_type='market',
                        direction='buy',
                        volume=volume
                    )
                    
                    if order:
                        print(f"✓ 金叉买入: {symbol}, 价格: {current_price:.2f}, 数量: {volume:.6f}")
        
        # 死叉信号:快线下穿慢线
        elif ma_fast_previous >= ma_slow_previous and ma_fast_current < ma_slow_current:
            # 如果有持仓,则卖出
            if position and position.get('volume', 0) > 0:
                volume = position['volume']
                
                # 下单卖出
                order = context.place_order(
                    symbol=symbol,
                    order_type='market',
                    direction='sell',
                    volume=volume
                )
                
                if order:
                    print(f"✓ 死叉卖出: {symbol}, 价格: {current_price:.2f}, 数量: {volume:.6f}")


def on_order_status(context, order):
    """
    订单状态更新时调用
    
    Args:
        context: 策略上下文
        order: 订单信息
    """
    print(f"订单更新: {order['symbol']} {order['direction']} {order['status']}")


def on_error(context, error):
    """
    发生错误时调用
    
    Args:
        context: 策略上下文
        error: 错误信息
    """
    print(f"❌ 策略错误: {error}")


# ==================== 策略说明 ====================
"""
加密货币双均线策略

策略逻辑:
1. 计算快速均线(5小时)和慢速均线(20小时)
2. 金叉(快线上穿慢线)时买入
3. 死叉(快线下穿慢线)时卖出
4. 每个交易对最多使用30%的可用USDT

适用市场:
- 加密货币现货市场
- 支持Binance等主流交易所

风险提示:
1. 加密货币市场波动较大,请谨慎控制仓位
2. 建议先在测试网环境测试策略
3. 注意交易所手续费对收益的影响
4. 加密货币7x24小时交易,注意风险管理

配置要求:
- 在config_template_cryptocurrency.json中配置API密钥
- 设置合适的初始资金和交易对列表
- 建议使用1小时K线周期

回测建议:
- 使用至少3个月的历史数据
- 测试不同的均线参数组合
- 关注夏普比率和最大回撤
"""
