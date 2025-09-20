"""
网格交易策略实现

实现网格交易的核心逻辑，包括网格计算、订单管理等
"""

import asyncio
from decimal import Decimal, ROUND_DOWN
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time

from edgex_sdk import OrderSide, CancelOrderParams, GetOrderBookDepthParams
from .logger import GridTradingLogger


@dataclass
class GridLevel:
    """网格级别数据类"""
    price: Decimal
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    is_buy_filled: bool = False
    is_sell_filled: bool = False


@dataclass
class OrderInfo:
    """订单信息数据类"""
    order_id: str
    side: str  # 'buy' or 'sell'
    price: Decimal
    size: Decimal
    status: str  # 'OPEN', 'FILLED', 'CANCELED', etc.
    filled_size: Decimal = Decimal('0')


class GridTradingStrategy:
    """网格交易策略类"""
    
    def __init__(self, config, edgex_client, logger: Optional[GridTradingLogger] = None):
        """
        初始化网格交易策略
        
        Args:
            config: 配置对象
            edgex_client: EdgeX 客户端
            logger: 日志记录器
        """
        self.config = config
        self.client = edgex_client
        self.logger = logger or GridTradingLogger()
        
        # 网格相关
        self.grid_levels: List[GridLevel] = []
        self.center_price: Optional[Decimal] = None
        self.contract_id: Optional[str] = None
        self.tick_size: Optional[Decimal] = None
        
        # 状态跟踪
        self.active_orders: Dict[str, OrderInfo] = {}
        self.position_size: Decimal = Decimal('0')
        self.total_profit: Decimal = Decimal('0')
        
        # 价格跟踪
        self.current_bid: Decimal = Decimal('0')
        self.current_ask: Decimal = Decimal('0')
        self.current_mid_price: Decimal = Decimal('0')
        
        # 止损跟踪
        self.initial_position_value: Decimal = Decimal('0')  # 初始持仓价值
        self.entry_price: Optional[Decimal] = None  # 平均开仓价格
        
        # 运行状态
        self.is_running = False
        self.last_price_update = 0
        
    async def initialize(self):
        """初始化策略"""
        try:
            self.logger.info("正在初始化网格交易策略...")
            
            # 获取合约信息
            await self._get_contract_info()
            
            # 获取当前价格作为中心价格
            await self._update_center_price()
            
            # 初始化网格
            self._calculate_grid_levels()
            
            # 获取当前持仓
            await self._update_position()
            
            self.logger.info(f"策略初始化完成 - 交易对: {self.config.trading_pair}, "
                           f"中心价格: {self.center_price}, 网格数量: {self.config.grid_count}")
            
        except Exception as e:
            self.logger.error(f"策略初始化失败: {e}")
            raise
    
    async def _get_contract_info(self):
        """获取合约信息"""
        try:
            metadata = await self.client.get_metadata()
            if not metadata or 'data' not in metadata:
                raise ValueError("无法获取交易所元数据")
            
            contract_list = metadata['data'].get('contractList', [])
            target_contract = None
            
            # 查找目标合约
            for contract in contract_list:
                if contract.get('contractName') == f"{self.config.trading_pair}USD":
                    target_contract = contract
                    break
            
            if not target_contract:
                raise ValueError(f"找不到交易对 {self.config.trading_pair}USD 的合约")
            
            self.contract_id = target_contract['contractId']
            self.tick_size = Decimal(target_contract['tickSize'])
            
            # 验证订单大小是否满足最小要求
            min_order_size = Decimal(target_contract.get('minOrderSize', '0'))
            if self.config.order_size < min_order_size:
                raise ValueError(f"订单大小 {self.config.order_size} 小于最小要求 {min_order_size}")
            
            self.logger.info(f"合约信息获取成功 - ID: {self.contract_id}, "
                           f"最小价格变动: {self.tick_size}")
            
        except Exception as e:
            self.logger.error(f"获取合约信息失败: {e}")
            raise
    
    async def _update_center_price(self):
        """更新中心价格 - 使用订单簿中间价"""
        try:
            # 获取订单簿数据
            depth_params = GetOrderBookDepthParams(contract_id=self.contract_id, limit=15)
            order_book = await self.client.quote.get_order_book_depth(depth_params)
            
            if not order_book or 'data' not in order_book:
                raise ValueError("无法获取订单簿数据")
            
            order_book_data = order_book['data']
            if not order_book_data:
                raise ValueError("订单簿数据为空")
            
            # 获取第一个订单簿条目
            order_book_entry = order_book_data[0]
            
            # 提取买卖盘数据
            bids = order_book_entry.get('bids', [])
            asks = order_book_entry.get('asks', [])
            
            if not bids or not asks:
                raise ValueError("订单簿买卖盘数据不完整")
            
            # 获取最佳买卖价
            self.current_bid = Decimal(bids[0]['price'])
            self.current_ask = Decimal(asks[0]['price'])
            
            # 计算中间价作为中心价格
            self.current_mid_price = (self.current_bid + self.current_ask) / 2
            self.center_price = self.current_mid_price
            
            self.last_price_update = time.time()
            
            self.logger.debug(f"价格更新 - 买价: {self.current_bid}, "
                            f"卖价: {self.current_ask}, 中间价: {self.current_mid_price}")
            
        except Exception as e:
            self.logger.error(f"更新中心价格失败: {e}")
            raise
    
    def _calculate_grid_levels(self):
        """计算网格级别"""
        if not self.center_price:
            raise ValueError("中心价格未设置")
        
        self.grid_levels.clear()
        
        # 计算价格范围
        price_range = self.center_price * self.config.price_range_percent / 100
        
        # 计算网格间距
        grid_spacing = price_range * 2 / self.config.grid_count
        
        # 生成网格级别
        for i in range(self.config.grid_count + 1):
            price = self.center_price - price_range + (i * grid_spacing)
            # 调整到tick_size的整数倍
            price = self._round_to_tick_size(price)
            
            if price > 0:  # 确保价格为正
                self.grid_levels.append(GridLevel(price=price))
        
        # 按价格排序
        self.grid_levels.sort(key=lambda x: x.price)
        
        self.logger.info(f"网格级别计算完成 - 共{len(self.grid_levels)}个级别, "
                        f"价格范围: {self.grid_levels[0].price} - {self.grid_levels[-1].price}")
    
    def _round_to_tick_size(self, price: Decimal) -> Decimal:
        """将价格调整到tick_size的整数倍"""
        if not self.tick_size:
            return price
        
        return (price / self.tick_size).quantize(Decimal('1'), rounding=ROUND_DOWN) * self.tick_size
    
    async def _update_position(self):
        """更新当前持仓"""
        try:
            positions_data = await self.client.get_account_positions()
            if not positions_data or 'data' not in positions_data:
                self.position_size = Decimal('0')
                await self._update_entry_price()  # 更新开仓价格
                return
            
            positions = positions_data.get('data', {}).get('positionList', [])
            current_position = Decimal('0')
            
            for position in positions:
                if position.get('contractId') == self.contract_id:
                    open_size = Decimal(position.get('openSize', '0'))
                    # 如果是负数表示空头持仓，正数表示多头持仓
                    current_position = open_size
                    break
            
            # 检查持仓是否发生变化
            position_changed = self.position_size != current_position
            self.position_size = current_position
            
            # 如果持仓发生变化，更新开仓价格
            if position_changed:
                await self._update_entry_price()
            
            self.logger.debug(f"当前持仓更新: {self.position_size}")
            
        except Exception as e:
            self.logger.error(f"更新持仓失败: {e}")
            # 不抛出异常，使用默认值
            self.position_size = Decimal('0')
    
    async def place_grid_orders(self):
        """放置网格订单"""
        try:
            self.logger.info("开始放置网格订单...")
            
            # 获取当前活跃订单
            await self._update_active_orders()
            
            # 为每个网格级别放置订单
            for i, grid_level in enumerate(self.grid_levels):
                # 跳过中心价格附近的级别，避免立即成交
                if abs(grid_level.price - self.center_price) < self.tick_size * 2:
                    continue
                
                # 放置买单（在当前价格下方）
                if grid_level.price < self.center_price and not grid_level.buy_order_id:
                    await self._place_buy_order(grid_level)
                
                # 放置卖单（在当前价格上方）
                if grid_level.price > self.center_price and not grid_level.sell_order_id:
                    await self._place_sell_order(grid_level)
                
                # 添加延迟避免频率限制
                await asyncio.sleep(0.1)
            
            self.logger.info(f"网格订单放置完成 - 活跃订单数: {len(self.active_orders)}")
            
        except Exception as e:
            self.logger.error(f"放置网格订单失败: {e}")
            raise
    
    async def _place_buy_order(self, grid_level: GridLevel):
        """放置买单"""
        try:
            # 检查持仓限制
            if abs(self.position_size) >= self.config.max_position_size:
                self.logger.debug(f"持仓已达上限，跳过买单 - 当前持仓: {self.position_size}")
                return
            
            order_result = await self.client.create_limit_order(
                contract_id=self.contract_id,
                size=str(self.config.order_size),
                price=str(grid_level.price),
                side=OrderSide.BUY,
                post_only=True
            )
            
            if order_result and 'data' in order_result:
                order_id = order_result['data'].get('orderId')
                if order_id:
                    grid_level.buy_order_id = order_id
                    self.active_orders[order_id] = OrderInfo(
                        order_id=order_id,
                        side='buy',
                        price=grid_level.price,
                        size=self.config.order_size,
                        status='OPEN'
                    )
                    self.logger.debug(f"买单放置成功 - 价格: {grid_level.price}, "
                                    f"数量: {self.config.order_size}, 订单ID: {order_id}")
            
        except Exception as e:
            self.logger.warning(f"放置买单失败 - 价格: {grid_level.price}, 错误: {e}")
    
    async def _place_sell_order(self, grid_level: GridLevel):
        """放置卖单"""
        try:
            # 检查持仓限制
            if abs(self.position_size) >= self.config.max_position_size:
                self.logger.debug(f"持仓已达上限，跳过卖单 - 当前持仓: {self.position_size}")
                return
            
            order_result = await self.client.create_limit_order(
                contract_id=self.contract_id,
                size=str(self.config.order_size),
                price=str(grid_level.price),
                side=OrderSide.SELL,
                post_only=True
            )
            
            if order_result and 'data' in order_result:
                order_id = order_result['data'].get('orderId')
                if order_id:
                    grid_level.sell_order_id = order_id
                    self.active_orders[order_id] = OrderInfo(
                        order_id=order_id,
                        side='sell',
                        price=grid_level.price,
                        size=self.config.order_size,
                        status='OPEN'
                    )
                    self.logger.debug(f"卖单放置成功 - 价格: {grid_level.price}, "
                                    f"数量: {self.config.order_size}, 订单ID: {order_id}")
            
        except Exception as e:
            self.logger.warning(f"放置卖单失败 - 价格: {grid_level.price}, 错误: {e}")
    
    async def _update_active_orders(self):
        """更新活跃订单状态"""
        try:
            if not self.active_orders:
                return
            
            # 获取所有活跃订单的ID
            order_ids = list(self.active_orders.keys())
            
            # 批量查询订单状态
            for order_id in order_ids[:10]:  # 限制批量查询数量
                try:
                    order_result = await self.client.order.get_order_by_id([order_id])
                    if order_result and 'data' in order_result:
                        order_list = order_result['data']
                        if order_list:
                            order_data = order_list[0]
                            order_info = self.active_orders.get(order_id)
                            if order_info:
                                order_info.status = order_data.get('status', 'UNKNOWN')
                                order_info.filled_size = Decimal(order_data.get('cumMatchSize', '0'))
                                
                                # 如果订单已完成或取消，从活跃订单中移除
                                if order_info.status in ['FILLED', 'CANCELED']:
                                    self._handle_order_completion(order_info)
                except Exception as e:
                    self.logger.debug(f"查询订单状态失败 - 订单ID: {order_id}, 错误: {e}")
                
                await asyncio.sleep(0.05)  # 避免频率限制
            
        except Exception as e:
            self.logger.error(f"更新活跃订单状态失败: {e}")
    
    def _handle_order_completion(self, order_info: OrderInfo):
        """处理订单完成"""
        try:
            if order_info.status == 'FILLED':
                self.logger.log_trade(
                    action='FILLED',
                    side=order_info.side,
                    size=str(order_info.size),
                    price=str(order_info.price),
                    order_id=order_info.order_id
                )
                
                # 更新网格级别状态
                for grid_level in self.grid_levels:
                    if grid_level.buy_order_id == order_info.order_id:
                        grid_level.is_buy_filled = True
                        grid_level.buy_order_id = None
                        break
                    elif grid_level.sell_order_id == order_info.order_id:
                        grid_level.is_sell_filled = True
                        grid_level.sell_order_id = None
                        break
            
            # 从活跃订单中移除
            if order_info.order_id in self.active_orders:
                del self.active_orders[order_info.order_id]
            
        except Exception as e:
            self.logger.error(f"处理订单完成失败: {e}")
    
    async def check_and_rebalance(self):
        """检查并重新平衡网格"""
        try:
            # 更新当前价格
            await self._update_center_price()
            
            # 更新持仓
            await self._update_position()
            
            # 检查止损条件
            should_stop = await self._check_stop_loss()
            if should_stop:
                self.logger.warning("触发止损条件，停止网格交易")
                await self.cancel_all_orders()
                await self._close_all_positions()
                return
            
            # 更新订单状态
            await self._update_active_orders()
            
            # 检查是否需要重新放置订单
            await self._rebalance_grid()
            
            # 记录状态
            unrealized_pnl = await self._calculate_unrealized_pnl()
            self.logger.log_grid_status(
                active_orders=len(self.active_orders),
                position_size=str(self.position_size),
                unrealized_pnl=str(unrealized_pnl) if unrealized_pnl else None
            )
            
        except Exception as e:
            self.logger.error(f"检查和重新平衡失败: {e}")
    
    async def _rebalance_grid(self):
        """重新平衡网格"""
        try:
            missing_orders_count = 0
            
            for grid_level in self.grid_levels:
                # 跳过中心价格附近的级别，避免立即成交
                if abs(grid_level.price - self.center_price) < self.tick_size * 2:
                    continue
                
                # 检查买单：价格在中心价格下方且没有活跃买单
                if (grid_level.price < self.center_price and 
                    not grid_level.buy_order_id):
                    
                    # 如果之前已成交，重置标志
                    if grid_level.is_buy_filled:
                        grid_level.is_buy_filled = False
                    
                    await self._place_buy_order(grid_level)
                    missing_orders_count += 1
                    self.logger.debug(f"重新放置买单 - 价格: {grid_level.price}")
                
                # 检查卖单：价格在中心价格上方且没有活跃卖单
                if (grid_level.price > self.center_price and 
                    not grid_level.sell_order_id):
                    
                    # 如果之前已成交，重置标志
                    if grid_level.is_sell_filled:
                        grid_level.is_sell_filled = False
                    
                    await self._place_sell_order(grid_level)
                    missing_orders_count += 1
                    self.logger.debug(f"重新放置卖单 - 价格: {grid_level.price}")
                
                await asyncio.sleep(0.05)  # 避免频率限制
            
            if missing_orders_count > 0:
                self.logger.info(f"重新平衡完成 - 补充了 {missing_orders_count} 个缺失的网格订单")
            
        except Exception as e:
            self.logger.error(f"重新平衡网格失败: {e}")
    
    async def cancel_all_orders(self):
        """取消所有活跃订单"""
        try:
            self.logger.info("正在取消所有活跃订单...")
            
            for order_id in list(self.active_orders.keys()):
                try:
                    cancel_params = CancelOrderParams(order_id=order_id)
                    cancel_result = await self.client.cancel_order(cancel_params)
                    if cancel_result:
                        self.logger.debug(f"订单取消成功 - 订单ID: {order_id}")
                except Exception as e:
                    self.logger.warning(f"取消订单失败 - 订单ID: {order_id}, 错误: {e}")
                
                await asyncio.sleep(0.1)
            
            # 清空活跃订单和网格状态
            self.active_orders.clear()
            for grid_level in self.grid_levels:
                grid_level.buy_order_id = None
                grid_level.sell_order_id = None
                grid_level.is_buy_filled = False
                grid_level.is_sell_filled = False
            
            self.logger.info("所有订单取消完成")
            
        except Exception as e:
            self.logger.error(f"取消所有订单失败: {e}")
    
    async def _check_stop_loss(self) -> bool:
        """检查止损条件"""
        try:
            if self.position_size == 0:
                return False  # 没有持仓，无需止损
            
            if not self.entry_price or not self.current_mid_price:
                return False  # 价格信息不完整
            
            # 计算当前价格相对于开仓价格的变动百分比
            price_change_percent = abs((self.current_mid_price - self.entry_price) / self.entry_price * 100)
            
            # 检查是否达到止损条件
            if price_change_percent >= self.config.stop_loss_percent:
                self.logger.warning(f"触发止损 - 开仓价格: {self.entry_price}, "
                                  f"当前价格: {self.current_mid_price}, "
                                  f"变动: {price_change_percent:.2f}%, "
                                  f"止损阈值: {self.config.stop_loss_percent}%")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查止损条件失败: {e}")
            return False
    
    async def _calculate_unrealized_pnl(self) -> Optional[Decimal]:
        """计算未实现盈亏"""
        try:
            if self.position_size == 0 or not self.entry_price or not self.current_mid_price:
                return Decimal('0')
            
            # 计算未实现盈亏 = 持仓大小 * (当前价格 - 开仓价格)
            unrealized_pnl = self.position_size * (self.current_mid_price - self.entry_price)
            return unrealized_pnl
            
        except Exception as e:
            self.logger.error(f"计算未实现盈亏失败: {e}")
            return None
    
    async def _update_entry_price(self):
        """更新平均开仓价格"""
        try:
            if self.position_size == 0:
                self.entry_price = None
                self.initial_position_value = Decimal('0')
                return
            
            # 获取持仓信息来计算平均开仓价格
            positions_data = await self.client.get_account_positions()
            if not positions_data or 'data' not in positions_data:
                return
            
            positions = positions_data.get('data', {}).get('positionList', [])
            
            for position in positions:
                if position.get('contractId') == self.contract_id:
                    # 尝试从持仓信息中获取平均价格
                    avg_price = position.get('avgPrice')
                    if avg_price:
                        self.entry_price = Decimal(avg_price)
                        self.initial_position_value = abs(self.position_size) * self.entry_price
                        self.logger.debug(f"更新平均开仓价格: {self.entry_price}")
                    break
            
            # 如果无法从API获取，使用当前中间价作为估算
            if not self.entry_price and self.current_mid_price:
                self.entry_price = self.current_mid_price
                self.initial_position_value = abs(self.position_size) * self.entry_price
                self.logger.debug(f"使用当前价格作为开仓价格: {self.entry_price}")
                
        except Exception as e:
            self.logger.error(f"更新平均开仓价格失败: {e}")
    
    async def _close_all_positions(self):
        """平仓所有持仓"""
        try:
            if self.position_size == 0:
                self.logger.info("当前无持仓，无需平仓")
                return
            
            self.logger.info(f"开始平仓 - 当前持仓: {self.position_size}")
            
            # 确定平仓方向
            if self.position_size > 0:
                # 多头持仓，需要卖出平仓
                side = OrderSide.SELL
                close_size = self.position_size
            else:
                # 空头持仓，需要买入平仓
                side = OrderSide.BUY
                close_size = abs(self.position_size)
            
            # 使用市价单快速平仓
            try:
                order_result = await self.client.create_market_order(
                    contract_id=self.contract_id,
                    size=str(close_size),
                    side=side.value
                )
                
                if order_result and 'data' in order_result:
                    order_id = order_result['data'].get('orderId')
                    self.logger.info(f"平仓订单已提交 - 订单ID: {order_id}, "
                                   f"方向: {side.value}, 数量: {close_size}")
                else:
                    self.logger.error("平仓订单提交失败")
                    
            except Exception as e:
                self.logger.error(f"提交平仓订单失败: {e}")
                # 如果市价单失败，尝试使用限价单
                try:
                    # 使用稍微不利的价格确保成交
                    if side == OrderSide.SELL:
                        close_price = self.current_bid * Decimal('0.999')  # 稍低于买价
                    else:
                        close_price = self.current_ask * Decimal('1.001')  # 稍高于卖价
                    
                    close_price = self._round_to_tick_size(close_price)
                    
                    order_result = await self.client.create_limit_order(
                        contract_id=self.contract_id,
                        size=str(close_size),
                        price=str(close_price),
                        side=side,
                        post_only=False
                    )
                    
                    if order_result and 'data' in order_result:
                        order_id = order_result['data'].get('orderId')
                        self.logger.info(f"限价平仓订单已提交 - 订单ID: {order_id}, "
                                       f"价格: {close_price}, 数量: {close_size}")
                    
                except Exception as limit_error:
                    self.logger.error(f"限价平仓订单也失败: {limit_error}")
            
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
    
    def get_strategy_status(self) -> Dict:
        """获取策略状态"""
        return {
            'is_running': self.is_running,
            'center_price': str(self.center_price) if self.center_price else None,
            'current_bid': str(self.current_bid),
            'current_ask': str(self.current_ask),
            'current_mid_price': str(self.current_mid_price),
            'position_size': str(self.position_size),
            'entry_price': str(self.entry_price) if self.entry_price else None,
            'active_orders_count': len(self.active_orders),
            'grid_levels_count': len(self.grid_levels),
            'total_profit': str(self.total_profit),
            'last_price_update': self.last_price_update
        }
