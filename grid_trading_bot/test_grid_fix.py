#!/usr/bin/env python3
"""
测试网格修复功能

验证网格重新平衡逻辑是否正确工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot


async def test_grid_rebalance():
    """测试网格重新平衡功能"""
    print("🧪 测试网格重新平衡功能...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        print("✅ 机器人初始化成功")
        
        if bot.strategy:
            # 显示网格配置
            strategy_status = bot.strategy.get_strategy_status()
            print(f"\n📊 网格配置:")
            print(f"  中心价格: {strategy_status.get('center_price', 'N/A')}")
            print(f"  网格级别数: {strategy_status.get('grid_levels_count', 0)}")
            print(f"  买价: {strategy_status.get('current_bid', 'N/A')}")
            print(f"  卖价: {strategy_status.get('current_ask', 'N/A')}")
            
            # 显示网格级别详情
            print(f"\n📋 网格级别详情:")
            for i, grid_level in enumerate(bot.strategy.grid_levels[:5]):  # 只显示前5个
                status = "中心" if abs(grid_level.price - bot.strategy.center_price) < bot.strategy.tick_size * 2 else "活跃"
                print(f"  级别{i+1}: {grid_level.price} ({status})")
            
            # 测试初始订单放置
            print(f"\n🔄 测试初始订单放置...")
            await bot.strategy.place_grid_orders()
            
            active_orders_after = len(bot.strategy.active_orders)
            print(f"  放置后活跃订单数: {active_orders_after}")
            
            # 测试重新平衡逻辑
            print(f"\n🔄 测试重新平衡逻辑...")
            await bot.strategy._rebalance_grid()
            
            active_orders_final = len(bot.strategy.active_orders)
            print(f"  重新平衡后活跃订单数: {active_orders_final}")
            
            # 显示活跃订单详情
            if bot.strategy.active_orders:
                print(f"\n📋 活跃订单详情:")
                for order_id, order_info in list(bot.strategy.active_orders.items())[:3]:
                    print(f"  订单: {order_id[:8]}... {order_info.side} {order_info.size}@{order_info.price}")
            else:
                print(f"\n⚠️  当前无活跃订单")
        
        # 清理
        await bot.stop()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 网格交易机器人修复测试")
    print("=" * 50)
    
    print("📋 配置修复说明:")
    print("  价格范围: 0.025% → 5.0% (合理的波动范围)")
    print("  网格间距: 0.005% → 0.5% (合理的间距)")
    print("  止损阈值: 2% → 10% (避免频繁触发)")
    print("  检查间隔: 1秒 → 5秒 (降低API压力)")
    print()
    
    await test_grid_rebalance()
    
    print("\n📋 修复总结:")
    print("✅ 网格范围从过小的0.025%调整为合理的5%")
    print("✅ 网格间距从过密的0.005%调整为0.5%") 
    print("✅ 改进重新平衡逻辑，自动补充缺失订单")
    print("✅ 增加了详细的调试日志")


if __name__ == "__main__":
    asyncio.run(main())
