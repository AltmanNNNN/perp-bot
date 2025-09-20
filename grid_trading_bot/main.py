#!/usr/bin/env python3
"""
网格交易机器人启动脚本

提供命令行接口来启动机器人或查询余额
"""

import asyncio
import argparse
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from grid_trading_bot.bot import GridTradingBot, get_balance
from grid_trading_bot.config import GridTradingConfig


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    EdgeX 网格交易机器人                        ║
║                                                              ║
║  基于 EdgeX Python SDK 实现的网格交易机器人                    ║
║  用于低成本快速刷交易量，支持自动重启和风险控制                   ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def run_bot(config_file: str = None):
    """运行网格交易机器人"""
    try:
        print("🚀 正在启动网格交易机器人...")
        
        bot = GridTradingBot(config_file)
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  接收到中断信号，正在优雅关闭...")
    except Exception as e:
        print(f"❌ 机器人运行失败: {e}")
        sys.exit(1)


async def query_balance(config_file: str = None):
    """查询账户余额"""
    try:
        print("💰 正在查询账户余额...")
        
        balance_info = await get_balance(config_file)
        
        print("\n" + "="*60)
        print("📊 账户余额信息")
        print("="*60)
        print(f"总余额:       {float(balance_info['total_balance']):.4f} USDC")
        print(f"可用余额:     {float(balance_info['available_balance']):.4f} USDC")
        print(f"冻结余额:     {float(balance_info['frozen_balance']):.4f} USDC")
        print(f"未实现盈亏:   {float(balance_info['unrealized_pnl']):.4f} USDC")
        
        if balance_info['positions']:
            print("\n📈 持仓信息:")
            print("-" * 60)
            for position in balance_info['positions']:
                print(f"合约: {position['contract_name']}")
                print(f"  持仓大小: {float(position['open_size']):.6f}")
                print(f"  未实现盈亏: {float(position['unrealized_pnl']):.4f} USDC")
                print(f"  保证金: {float(position['margin']):.4f} USDC")
                print()
        else:
            print("\n📝 当前无持仓")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ 查询余额失败: {e}")
        sys.exit(1)


def create_config_template(output_file: str):
    """创建配置文件模板"""
    try:
        # 读取示例配置
        example_config_path = Path(__file__).parent / "config_example.json"
        if example_config_path.exists():
            with open(example_config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            # 如果示例文件不存在，创建默认配置
            config_data = {
                "edgex_base_url": "https://pro.edgex.exchange",
                "edgex_ws_url": "wss://quote.edgex.exchange",
                "edgex_account_id": "YOUR_ACCOUNT_ID",
                "edgex_stark_private_key": "YOUR_STARK_PRIVATE_KEY",
                "trading_pair": "ETH",
                "grid_count": 10,
                "grid_spacing_percent": 0.5,
                "order_size": 0.01,
                "max_position_size": 0.1,
                "price_range_percent": 5.0,
                "stop_loss_percent": 10.0,
                "check_interval": 5,
                "max_retries": 3,
                "auto_restart": True,
                "log_level": "INFO",
                "log_to_file": True
            }
        
        # 保存配置文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 配置文件模板已创建: {output_file}")
        print("📝 请编辑配置文件，设置您的API密钥和交易参数")
        
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        sys.exit(1)


def validate_config(config_file: str):
    """验证配置文件"""
    try:
        config = GridTradingConfig(config_file)
        config.validate()
        
        print(f"✅ 配置文件验证通过: {config_file}")
        print("\n📋 配置摘要:")
        print(f"  交易对: {config.trading_pair}USD")
        print(f"  网格数量: {config.grid_count}")
        print(f"  网格间距: {config.grid_spacing_percent}%")
        print(f"  订单大小: {config.order_size}")
        print(f"  最大持仓: {config.max_position_size}")
        print(f"  价格范围: ±{config.price_range_percent}%")
        print(f"  检查间隔: {config.check_interval}秒")
        print(f"  自动重启: {'是' if config.auto_restart else '否'}")
        
    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='EdgeX 网格交易机器人',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py run                          # 使用环境变量启动机器人
  python main.py run -c config.json          # 使用配置文件启动机器人
  python main.py balance                      # 查询账户余额
  python main.py balance -c config.json      # 使用配置文件查询余额
  python main.py create-config config.json   # 创建配置文件模板
  python main.py validate -c config.json     # 验证配置文件

环境变量设置:
  export EDGEX_ACCOUNT_ID="your_account_id"
  export EDGEX_STARK_PRIVATE_KEY="your_stark_private_key"
  export TRADING_PAIR="ETH"
  export GRID_COUNT="10"
  export ORDER_SIZE="0.01"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 运行机器人命令
    run_parser = subparsers.add_parser('run', help='启动网格交易机器人')
    run_parser.add_argument('-c', '--config', help='配置文件路径')
    
    # 查询余额命令
    balance_parser = subparsers.add_parser('balance', help='查询账户余额')
    balance_parser.add_argument('-c', '--config', help='配置文件路径')
    
    # 创建配置文件命令
    create_parser = subparsers.add_parser('create-config', help='创建配置文件模板')
    create_parser.add_argument('output', help='输出配置文件路径')
    
    # 验证配置文件命令
    validate_parser = subparsers.add_parser('validate', help='验证配置文件')
    validate_parser.add_argument('-c', '--config', required=True, help='配置文件路径')
    
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        print_banner()
        parser.print_help()
        return
    
    # 执行对应的命令
    if args.command == 'run':
        print_banner()
        asyncio.run(run_bot(args.config))
    
    elif args.command == 'balance':
        asyncio.run(query_balance(args.config))
    
    elif args.command == 'create-config':
        create_config_template(args.output)
    
    elif args.command == 'validate':
        validate_config(args.config)


if __name__ == "__main__":
    main()
