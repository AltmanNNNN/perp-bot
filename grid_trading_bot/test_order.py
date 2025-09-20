#!/usr/bin/env python3
"""
测试订单放置功能

快速测试机器人是否能正常放置网格订单
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot


async def test_order_placement():
    """测试订单放置功能"""
    print("🧪 测试网格订单放置...")
    
    try:
        bot = GridTradingBot("config.json")
        await bot.initialize()
        
        print("✅ 机器人初始化成功")
        
        # 获取策略状态
        if bot.strategy:
            strategy_status = bot.strategy.get_strategy_status()
            print(f"📈 中心价格: {strategy_status.get('center_price', 'N/A')}")
            print(f"📊 网格级别数: {strategy_status.get('grid_levels_count', 0)}")
            
            # 测试放置一个网格订单（不会实际执行，只是测试到API调用）
            print("\n🔄 开始测试订单放置...")
            
            # 只运行5秒钟来测试订单放置
            bot.is_running = True
            await bot.strategy.place_grid_orders()
            
            # 检查活跃订单数
            active_orders = len(bot.strategy.active_orders)
            print(f"📋 已放置订单数: {active_orders}")
            
            if active_orders > 0:
                print("✅ 订单放置成功！")
                print("订单列表:")
                for order_id, order_info in list(bot.strategy.active_orders.items())[:3]:  # 只显示前3个
                    print(f"  - 订单ID: {order_id[:8]}... 方向: {order_info.side} 价格: {order_info.price} 数量: {order_info.size}")
            else:
                print("⚠️  未放置任何订单，可能是持仓限制或价格范围问题")
        
        # 清理
        await bot.stop()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🚀 EdgeX 网格交易机器人订单测试")
    print("=" * 50)
    
    await test_order_placement()
    
    print("\n📋 测试结果:")
    print("如果看到 '订单放置成功'，说明修复生效")
    print("如果仍有错误，请检查日志文件")


if __name__ == "__main__":
    asyncio.run(main())
