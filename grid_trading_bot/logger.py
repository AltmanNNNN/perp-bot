"""
网格交易机器人日志模块

提供统一的日志记录功能
"""

import os
import logging
import sys
from datetime import datetime
from typing import Optional


class GridTradingLogger:
    """网格交易机器人日志记录器"""
    
    def __init__(self, name: str = "GridTradingBot", log_level: str = "INFO", 
                 log_to_file: bool = True, log_dir: str = "logs"):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_level: 日志级别
            log_to_file: 是否记录到文件
            log_dir: 日志文件目录
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_to_file:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            today = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"grid_trading_bot_{today}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, extra_data: Optional[dict] = None):
        """记录信息级别日志"""
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.info(message)
    
    def warning(self, message: str, extra_data: Optional[dict] = None):
        """记录警告级别日志"""
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.warning(message)
    
    def error(self, message: str, extra_data: Optional[dict] = None):
        """记录错误级别日志"""
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.error(message)
    
    def debug(self, message: str, extra_data: Optional[dict] = None):
        """记录调试级别日志"""
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.debug(message)
    
    def critical(self, message: str, extra_data: Optional[dict] = None):
        """记录严重错误级别日志"""
        if extra_data:
            message = f"{message} - {extra_data}"
        self.logger.critical(message)
    
    def log_trade(self, action: str, side: str, size: str, price: str, 
                  order_id: Optional[str] = None):
        """记录交易日志"""
        trade_info = {
            'action': action,
            'side': side,
            'size': size,
            'price': price,
            'order_id': order_id,
            'timestamp': datetime.now().isoformat()
        }
        self.info(f"交易操作: {action}", trade_info)
    
    def log_grid_status(self, active_orders: int, position_size: str, 
                       unrealized_pnl: Optional[str] = None):
        """记录网格状态日志"""
        status_info = {
            'active_orders': active_orders,
            'position_size': position_size,
            'unrealized_pnl': unrealized_pnl,
            'timestamp': datetime.now().isoformat()
        }
        self.info("网格状态更新", status_info)
    
    def log_error_with_retry(self, error: Exception, retry_count: int, max_retries: int):
        """记录错误和重试信息"""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'retry_count': retry_count,
            'max_retries': max_retries
        }
        self.warning(f"操作失败，正在重试 ({retry_count}/{max_retries})", error_info)
