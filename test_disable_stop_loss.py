#!/usr/bin/env python3
"""
测试禁用止损功能的示例脚本
Test script for disable stop loss functionality
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from trading_bot import TradingBot, TradingConfig


async def test_disable_stop_loss():
    """测试禁用止损功能"""
    print("🧪 测试禁用止损功能...")
    
    # 创建配置 - 禁用止损
    config_with_stop_loss = TradingConfig(
        ticker="ETH",
        contract_id="test_contract",
        quantity=Decimal('0.1'),
        take_profit=Decimal('0.02'),
        stop_loss=Decimal('0.1'),
        tick_size=Decimal('0.01'),
        direction="buy",
        max_orders=40,
        wait_time=450,
        exchange="edgex",
        grid_step=Decimal('-100'),
        disable_stop_loss=False  # 启用止损
    )
    
    config_without_stop_loss = TradingConfig(
        ticker="ETH",
        contract_id="test_contract",
        quantity=Decimal('0.1'),
        take_profit=Decimal('0.02'),
        stop_loss=Decimal('0.1'),
        tick_size=Decimal('0.01'),
        direction="buy",
        max_orders=40,
        wait_time=450,
        exchange="edgex",
        grid_step=Decimal('-100'),
        disable_stop_loss=True  # 禁用止损
    )
    
    print("📋 配置对比:")
    print(f"  配置1 - 启用止损: disable_stop_loss = {config_with_stop_loss.disable_stop_loss}")
    print(f"  配置2 - 禁用止损: disable_stop_loss = {config_without_stop_loss.disable_stop_loss}")
    
    print("\n✅ 配置测试完成!")
    print("\n💡 使用方法:")
    print("  启用止损 (默认): python runbot.py --exchange edgex --ticker ETH --quantity 0.1 --take-profit 0.02 --stop-loss 0.1")
    print("  禁用止损 (新功能): python runbot.py --exchange edgex --ticker ETH --quantity 0.1 --take-profit 0.02 --stop-loss 0.1 --disable-stop-loss")


if __name__ == "__main__":
    asyncio.run(test_disable_stop_loss())
