"""
网格交易机器人主程序

整合所有组件，实现完整的网格交易机器人功能
"""

import asyncio
import signal
import sys
import traceback
from typing import Optional
import time

from edgex_sdk import Client
from .config import GridTradingConfig
from .logger import GridTradingLogger
from .grid_strategy import GridTradingStrategy


class GridTradingBot:
    """网格交易机器人主类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化网格交易机器人
        
        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        self.config = GridTradingConfig(config_file)
        self.config.validate()
        
        # 初始化日志
        self.logger = GridTradingLogger(
            name="GridTradingBot",
            log_level=self.config.log_level,
            log_to_file=self.config.log_to_file
        )
        
        # 初始化EdgeX客户端
        self.edgex_client = None
        
        # 初始化策略
        self.strategy = None
        
        # 运行状态
        self.is_running = False
        self.should_restart = False
        self.restart_count = 0
        self.max_restart_count = 5
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"接收到信号 {signum}，正在优雅关闭...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self):
        """初始化机器人"""
        try:
            self.logger.info("正在初始化网格交易机器人...")
            self.logger.info(f"配置信息: {self.config.to_dict()}")
            
            # 初始化EdgeX客户端
            self.edgex_client = Client(
                base_url=self.config.edgex_base_url,
                account_id=int(self.config.edgex_account_id),
                stark_private_key=self.config.edgex_stark_private_key
            )
            
            # 测试连接
            server_time = await self.edgex_client.get_server_time()
            self.logger.info(f"EdgeX连接成功 - 服务器时间: {server_time}")
            
            # 初始化策略
            self.strategy = GridTradingStrategy(
                config=self.config,
                edgex_client=self.edgex_client,
                logger=self.logger
            )
            
            await self.strategy.initialize()
            
            self.logger.info("网格交易机器人初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    async def start(self):
        """启动机器人"""
        try:
            self.logger.info("启动网格交易机器人...")
            self.is_running = True
            
            # 放置初始网格订单
            await self.strategy.place_grid_orders()
            
            # 主运行循环
            await self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"机器人运行失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            
            if self.config.auto_restart and self.restart_count < self.max_restart_count:
                self.should_restart = True
            else:
                raise
    
    async def _run_main_loop(self):
        """主运行循环"""
        last_check_time = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查是否到了检查时间
                if current_time - last_check_time >= self.config.check_interval:
                    await self.strategy.check_and_rebalance()
                    last_check_time = current_time
                
                # 短暂休眠
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"主循环运行错误: {e}")
                
                # 根据配置决定是否重试
                retry_count = 0
                while retry_count < self.config.max_retries:
                    try:
                        self.logger.log_error_with_retry(e, retry_count + 1, self.config.max_retries)
                        await asyncio.sleep(5)  # 等待5秒后重试
                        break
                    except Exception as retry_error:
                        retry_count += 1
                        if retry_count >= self.config.max_retries:
                            self.logger.error(f"重试次数已达上限，停止运行: {retry_error}")
                            self.is_running = False
                            break
    
    async def stop(self):
        """停止机器人"""
        try:
            self.logger.info("正在停止网格交易机器人...")
            self.is_running = False
            
            # 取消所有活跃订单
            if self.strategy:
                await self.strategy.cancel_all_orders()
            
            # 关闭EdgeX客户端
            if self.edgex_client:
                await self.edgex_client.close()
            
            self.logger.info("网格交易机器人已停止")
            
        except Exception as e:
            self.logger.error(f"停止机器人时出错: {e}")
    
    async def restart(self):
        """重启机器人"""
        try:
            self.logger.info(f"正在重启机器人 (第{self.restart_count + 1}次)...")
            self.restart_count += 1
            
            # 停止当前运行
            await self.stop()
            
            # 等待一段时间
            await asyncio.sleep(10)
            
            # 重新初始化
            await self.initialize()
            
            # 重新启动
            self.should_restart = False
            await self.start()
            
        except Exception as e:
            self.logger.error(f"重启失败: {e}")
            if self.restart_count < self.max_restart_count:
                self.logger.info(f"将在30秒后再次尝试重启...")
                await asyncio.sleep(30)
                await self.restart()
            else:
                self.logger.critical("重启次数已达上限，机器人停止运行")
                raise
    
    async def get_account_balance(self) -> dict:
        """
        获取账户余额信息
        
        Returns:
            dict: 包含余额信息的字典
        """
        try:
            if not self.edgex_client:
                raise ValueError("EdgeX客户端未初始化")
            
            # 获取账户资产信息
            assets_data = await self.edgex_client.get_account_asset()
            
            if not assets_data or 'data' not in assets_data:
                raise ValueError("无法获取账户资产信息")
            
            data = assets_data['data']
            
            # 解析余额信息
            balance_info = {
                'total_balance': '0',
                'available_balance': '0',
                'frozen_balance': '0',
                'unrealized_pnl': '0',
                'positions': []
            }
            
            # 获取抵押品信息
            collateral_list = data.get('collateralList', [])
            if collateral_list:
                collateral = collateral_list[0]  # 通常只有一个抵押品（USDC）
                balance_info['total_balance'] = collateral.get('totalSize', '0')
                balance_info['available_balance'] = collateral.get('availableSize', '0')
                balance_info['frozen_balance'] = collateral.get('frozenSize', '0')
            
            # 获取持仓信息
            position_list = data.get('positionList', [])
            for position in position_list:
                if position.get('openSize', '0') != '0':  # 只显示有持仓的合约
                    balance_info['positions'].append({
                        'contract_id': position.get('contractId', ''),
                        'contract_name': position.get('contractName', ''),
                        'open_size': position.get('openSize', '0'),
                        'unrealized_pnl': position.get('unrealizedPnl', '0'),
                        'margin': position.get('margin', '0')
                    })
            
            # 计算总未实现盈亏
            total_unrealized_pnl = sum(
                float(pos['unrealized_pnl']) for pos in balance_info['positions']
            )
            balance_info['unrealized_pnl'] = str(total_unrealized_pnl)
            
            return balance_info
            
        except Exception as e:
            self.logger.error(f"获取账户余额失败: {e}")
            raise
    
    def get_status(self) -> dict:
        """
        获取机器人运行状态
        
        Returns:
            dict: 包含机器人状态信息的字典
        """
        status = {
            'is_running': self.is_running,
            'restart_count': self.restart_count,
            'should_restart': self.should_restart,
            'config': self.config.to_dict()
        }
        
        if self.strategy:
            status['strategy'] = self.strategy.get_strategy_status()
        
        return status
    
    async def run(self):
        """运行机器人（包含自动重启逻辑）"""
        try:
            await self.initialize()
            
            while True:
                try:
                    await self.start()
                    
                    # 如果正常退出且不需要重启，则结束
                    if not self.should_restart:
                        break
                    
                    # 需要重启
                    if self.restart_count < self.max_restart_count:
                        await self.restart()
                    else:
                        self.logger.critical("重启次数已达上限，机器人停止运行")
                        break
                        
                except KeyboardInterrupt:
                    self.logger.info("接收到键盘中断信号")
                    break
                except Exception as e:
                    self.logger.error(f"机器人运行出错: {e}")
                    if self.config.auto_restart and self.restart_count < self.max_restart_count:
                        self.should_restart = True
                        await self.restart()
                    else:
                        break
            
        finally:
            await self.stop()


# 独立的余额查询函数
async def get_balance(config_file: Optional[str] = None) -> dict:
    """
    独立的余额查询函数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        dict: 余额信息
    """
    config = GridTradingConfig(config_file)
    config.validate()
    
    client = Client(
        base_url=config.edgex_base_url,
        account_id=int(config.edgex_account_id),
        stark_private_key=config.edgex_stark_private_key
    )
    
    try:
        # 获取账户资产信息
        assets_data = await client.get_account_asset()
        
        if not assets_data or 'data' not in assets_data:
            raise ValueError("无法获取账户资产信息")
        
        data = assets_data['data']
        
        # 解析余额信息
        balance_info = {
            'total_balance': '0',
            'available_balance': '0',
            'frozen_balance': '0',
            'unrealized_pnl': '0',
            'positions': []
        }
        
        # 获取抵押品信息
        collateral_list = data.get('collateralList', [])
        if collateral_list:
            collateral = collateral_list[0]
            balance_info['total_balance'] = collateral.get('totalSize', '0')
            balance_info['available_balance'] = collateral.get('availableSize', '0')
            balance_info['frozen_balance'] = collateral.get('frozenSize', '0')
        
        # 获取持仓信息
        position_list = data.get('positionList', [])
        for position in position_list:
            if position.get('openSize', '0') != '0':
                balance_info['positions'].append({
                    'contract_id': position.get('contractId', ''),
                    'contract_name': position.get('contractName', ''),
                    'open_size': position.get('openSize', '0'),
                    'unrealized_pnl': position.get('unrealizedPnl', '0'),
                    'margin': position.get('margin', '0')
                })
        
        # 计算总未实现盈亏
        total_unrealized_pnl = sum(
            float(pos['unrealized_pnl']) for pos in balance_info['positions']
        )
        balance_info['unrealized_pnl'] = str(total_unrealized_pnl)
        
        return balance_info
        
    finally:
        await client.close()


if __name__ == "__main__":
    # 如果直接运行此文件，启动机器人
    async def main():
        bot = GridTradingBot()
        await bot.run()
    
    asyncio.run(main())
