#!/usr/bin/env python3
"""
网格交易机器人测试脚本

用于测试机器人的各项功能是否正常
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot


async def test_bot_initialization():
    """测试机器人初始化"""
    print("🧪 测试机器人初始化...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        print("✅ 机器人初始化成功")
        
        # 获取状态
        status = bot.get_status()
        print(f"📊 机器人状态: {status}")
        
        # 获取余额
        balance = await bot.get_account_balance()
        print(f"💰 账户余额: {balance}")
        
        # 清理
        await bot.stop()
        
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_strategy_initialization():
    """测试策略初始化"""
    print("\n🧪 测试策略初始化...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        if bot.strategy:
            strategy_status = bot.strategy.get_strategy_status()
            print(f"📈 策略状态: {strategy_status}")
            
            print(f"🎯 中心价格: {strategy_status.get('center_price', 'N/A')}")
            print(f"📊 网格级别数: {strategy_status.get('grid_levels_count', 0)}")
            print(f"💼 持仓大小: {strategy_status.get('position_size', '0')}")
        
        await bot.stop()
        print("✅ 策略测试完成")
        
    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 EdgeX 网格交易机器人功能测试")
    print("=" * 50)
    
    await test_bot_initialization()
    await test_strategy_initialization()
    
    print("\n🎉 所有测试完成！")
    print("现在您可以启动机器人:")
    print("  python3 main.py run -c config.json")


if __name__ == "__main__":
    asyncio.run(main())
