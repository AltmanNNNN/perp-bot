#!/usr/bin/env python3
"""
网格交易机器人使用示例

演示如何使用网格交易机器人的各种功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot, get_balance
from grid_trading_bot.config import GridTradingConfig


async def example_balance_query():
    """示例：查询账户余额"""
    print("=" * 50)
    print("示例1: 查询账户余额")
    print("=" * 50)
    
    try:
        # 方式1: 使用环境变量
        balance_info = await get_balance()
        
        print("账户余额信息:")
        print(f"  总余额: {balance_info['total_balance']} USDC")
        print(f"  可用余额: {balance_info['available_balance']} USDC")
        print(f"  冻结余额: {balance_info['frozen_balance']} USDC")
        print(f"  未实现盈亏: {balance_info['unrealized_pnl']} USDC")
        
        if balance_info['positions']:
            print("持仓信息:")
            for pos in balance_info['positions']:
                print(f"  {pos['contract_name']}: {pos['open_size']} "
                      f"(盈亏: {pos['unrealized_pnl']} USDC)")
        
    except Exception as e:
        print(f"查询余额失败: {e}")


async def example_config_usage():
    """示例：配置文件使用"""
    print("\n" + "=" * 50)
    print("示例2: 配置文件使用")
    print("=" * 50)
    
    # 创建配置对象
    config = GridTradingConfig()
    
    print("当前配置:")
    print(f"  交易对: {config.trading_pair}")
    print(f"  网格数量: {config.grid_count}")
    print(f"  订单大小: {config.order_size}")
    print(f"  网格间距: {config.grid_spacing_percent}%")
    print(f"  价格范围: ±{config.price_range_percent}%")
    print(f"  检查间隔: {config.check_interval}秒")
    print(f"  自动重启: {config.auto_restart}")
    
    # 保存配置到文件
    config.save_to_file("example_config.json")
    print("\n配置已保存到 example_config.json")


async def example_bot_status():
    """示例：获取机器人状态"""
    print("\n" + "=" * 50)
    print("示例3: 机器人状态监控")
    print("=" * 50)
    
    try:
        # 创建机器人实例（不启动）
        bot = GridTradingBot()
        await bot.initialize()
        
        # 获取状态信息
        status = bot.get_status()
        
        print("机器人状态:")
        print(f"  运行状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"  重启次数: {status['restart_count']}")
        print(f"  配置的交易对: {status['config']['trading_pair']}")
        print(f"  配置的网格数量: {status['config']['grid_count']}")
        
        if 'strategy' in status:
            strategy_status = status['strategy']
            print("策略状态:")
            print(f"  中心价格: {strategy_status.get('center_price', 'N/A')}")
            print(f"  持仓大小: {strategy_status.get('position_size', '0')}")
            print(f"  活跃订单数: {strategy_status.get('active_orders_count', 0)}")
            print(f"  网格级别数: {strategy_status.get('grid_levels_count', 0)}")
        
        # 清理资源
        await bot.stop()
        
    except Exception as e:
        print(f"获取机器人状态失败: {e}")


async def example_custom_config():
    """示例：自定义配置"""
    print("\n" + "=" * 50)
    print("示例4: 自定义配置示例")
    print("=" * 50)
    
    # 保守型配置示例
    conservative_config = {
        "trading_pair": "ETH",
        "grid_count": 8,
        "grid_spacing_percent": 0.8,
        "order_size": 0.005,
        "max_position_size": 0.05,
        "price_range_percent": 3.0,
        "check_interval": 10,
        "auto_restart": True,
        "log_level": "INFO"
    }
    
    print("保守型配置 (适合新手):")
    for key, value in conservative_config.items():
        print(f"  {key}: {value}")
    
    # 激进型配置示例
    aggressive_config = {
        "trading_pair": "BTC",
        "grid_count": 15,
        "grid_spacing_percent": 0.3,
        "order_size": 0.02,
        "max_position_size": 0.2,
        "price_range_percent": 8.0,
        "check_interval": 3,
        "auto_restart": True,
        "log_level": "DEBUG"
    }
    
    print("\n激进型配置 (有经验用户):")
    for key, value in aggressive_config.items():
        print(f"  {key}: {value}")


def print_usage_tips():
    """打印使用提示"""
    print("\n" + "=" * 50)
    print("使用提示")
    print("=" * 50)
    
    tips = [
        "1. 首次使用前，请先查询账户余额确认资金充足",
        "2. 建议从小额资金开始测试，熟悉后再增加投入",
        "3. 网格交易适合震荡市场，避免在单边趋势中使用",
        "4. 定期检查日志文件，监控机器人运行状态",
        "5. 设置合理的止损和持仓限制，控制风险",
        "6. 在网络不稳定时，建议启用自动重启功能",
        "7. 根据市场波动调整网格参数，优化收益"
    ]
    
    for tip in tips:
        print(f"  {tip}")


async def main():
    """主函数"""
    print("EdgeX 网格交易机器人使用示例")
    print("=" * 50)
    
    # 检查环境变量
    import os
    if not os.getenv('EDGEX_ACCOUNT_ID') or not os.getenv('EDGEX_STARK_PRIVATE_KEY'):
        print("⚠️  请先设置环境变量:")
        print("export EDGEX_ACCOUNT_ID=\"your_account_id\"")
        print("export EDGEX_STARK_PRIVATE_KEY=\"your_stark_private_key\"")
        print("\n或者创建配置文件:")
        print("python main.py create-config my_config.json")
        return
    
    try:
        # 运行示例
        await example_balance_query()
        await example_config_usage()
        await example_bot_status()
        await example_custom_config()
        
        print_usage_tips()
        
        print("\n" + "=" * 50)
        print("示例运行完成！")
        print("=" * 50)
        
        print("\n快速启动命令:")
        print("  python main.py run                    # 使用环境变量启动")
        print("  python main.py run -c config.json     # 使用配置文件启动")
        print("  python main.py balance                # 查询余额")
        print("  ./start.sh                           # 使用启动脚本")
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
