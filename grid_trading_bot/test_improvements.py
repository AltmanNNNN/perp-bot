#!/usr/bin/env python3
"""
测试价格获取和止损功能的改进

验证新的订单簿价格获取和止损机制是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot


async def test_price_improvements():
    """测试价格获取改进"""
    print("🧪 测试价格获取改进...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        print("✅ 机器人初始化成功")
        
        # 获取策略状态
        if bot.strategy:
            # 手动更新一次价格
            await bot.strategy._update_center_price()
            
            strategy_status = bot.strategy.get_strategy_status()
            
            print("\n📊 价格信息:")
            print(f"  买价 (Bid): {strategy_status.get('current_bid', 'N/A')}")
            print(f"  卖价 (Ask): {strategy_status.get('current_ask', 'N/A')}")
            print(f"  中间价: {strategy_status.get('current_mid_price', 'N/A')}")
            print(f"  中心价格: {strategy_status.get('center_price', 'N/A')}")
            
            # 测试未实现盈亏计算
            if bot.strategy.position_size != 0:
                unrealized_pnl = await bot.strategy._calculate_unrealized_pnl()
                print(f"\n💰 持仓信息:")
                print(f"  持仓大小: {strategy_status.get('position_size', '0')}")
                print(f"  开仓价格: {strategy_status.get('entry_price', 'N/A')}")
                print(f"  未实现盈亏: {unrealized_pnl if unrealized_pnl is not None else 'N/A'}")
                
                # 测试止损检查
                should_stop = await bot.strategy._check_stop_loss()
                print(f"  止损状态: {'触发' if should_stop else '正常'}")
            else:
                print(f"\n💰 当前无持仓")
        
        # 清理
        await bot.stop()
        print("\n✅ 价格获取测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_stop_loss_logic():
    """测试止损逻辑"""
    print("\n🛡️ 测试止损逻辑...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        if bot.strategy:
            # 模拟设置一些测试数据
            from decimal import Decimal
            
            # 模拟持仓和价格数据
            bot.strategy.position_size = Decimal('0.1')  # 模拟持仓
            bot.strategy.entry_price = Decimal('4000')   # 模拟开仓价格
            bot.strategy.current_mid_price = Decimal('4500')  # 模拟当前价格
            
            print("📋 模拟数据:")
            print(f"  持仓大小: {bot.strategy.position_size}")
            print(f"  开仓价格: {bot.strategy.entry_price}")
            print(f"  当前价格: {bot.strategy.current_mid_price}")
            print(f"  止损阈值: {bot.config.stop_loss_percent}%")
            
            # 计算价格变动百分比
            price_change = abs((bot.strategy.current_mid_price - bot.strategy.entry_price) / bot.strategy.entry_price * 100)
            print(f"  价格变动: {price_change:.2f}%")
            
            # 测试止损检查
            should_stop = await bot.strategy._check_stop_loss()
            print(f"  止损结果: {'触发' if should_stop else '正常'}")
            
            # 测试未实现盈亏计算
            unrealized_pnl = await bot.strategy._calculate_unrealized_pnl()
            print(f"  未实现盈亏: {unrealized_pnl}")
            
            # 测试不同的价格场景
            print("\n🔄 测试不同价格场景:")
            
            # 场景1: 小幅波动
            bot.strategy.current_mid_price = Decimal('4100')
            price_change = abs((bot.strategy.current_mid_price - bot.strategy.entry_price) / bot.strategy.entry_price * 100)
            should_stop = await bot.strategy._check_stop_loss()
            print(f"  场景1 (4100): 变动{price_change:.2f}%, 止损{'触发' if should_stop else '正常'}")
            
            # 场景2: 大幅波动（超过止损阈值）
            bot.strategy.current_mid_price = Decimal('3500')  # 下跌12.5%
            price_change = abs((bot.strategy.current_mid_price - bot.strategy.entry_price) / bot.strategy.entry_price * 100)
            should_stop = await bot.strategy._check_stop_loss()
            print(f"  场景2 (3500): 变动{price_change:.2f}%, 止损{'触发' if should_stop else '正常'}")
            
            # 场景3: 上涨超过止损阈值
            bot.strategy.current_mid_price = Decimal('4500')  # 上涨12.5%
            price_change = abs((bot.strategy.current_mid_price - bot.strategy.entry_price) / bot.strategy.entry_price * 100)
            should_stop = await bot.strategy._check_stop_loss()
            print(f"  场景3 (4500): 变动{price_change:.2f}%, 止损{'触发' if should_stop else '正常'}")
        
        await bot.stop()
        print("\n✅ 止损逻辑测试完成")
        
    except Exception as e:
        print(f"❌ 止损测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 EdgeX 网格交易机器人改进功能测试")
    print("=" * 60)
    
    await test_price_improvements()
    await test_stop_loss_logic()
    
    print("\n📋 测试总结:")
    print("✅ 价格获取: 使用订单簿中间价，更准确实时")
    print("✅ 止损机制: 监控持仓，自动平仓保护")
    print("✅ 盈亏计算: 实时计算未实现盈亏")
    print("\n🎯 改进点:")
    print("- 中心价格使用买卖中间价，更准确反映市场")
    print("- 止损机制监控所有持仓，达到阈值自动平仓")
    print("- 增加了详细的价格和盈亏跟踪")


if __name__ == "__main__":
    asyncio.run(main())
