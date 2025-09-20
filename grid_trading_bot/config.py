"""
网格交易机器人配置文件

包含机器人运行所需的所有配置参数
"""

import os
from decimal import Decimal
from typing import Dict, Any, Optional
import json


class GridTradingConfig:
    """网格交易配置类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用环境变量
        """
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
        else:
            self._load_from_env()
    
    def _load_from_file(self, config_file: str):
        """从配置文件加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # EdgeX API 配置
        self.edgex_base_url = config_data.get('edgex_base_url', 'https://pro.edgex.exchange')
        self.edgex_ws_url = config_data.get('edgex_ws_url', 'wss://quote.edgex.exchange')
        self.edgex_account_id = config_data.get('edgex_account_id')
        self.edgex_stark_private_key = config_data.get('edgex_stark_private_key')
        
        # 交易配置
        self.trading_pair = config_data.get('trading_pair', 'ETH')  # 交易对，如 ETH, BTC
        self.grid_count = config_data.get('grid_count', 10)  # 网格数量
        self.grid_spacing_percent = Decimal(str(config_data.get('grid_spacing_percent', 0.5)))  # 网格间距百分比
        self.order_size = Decimal(str(config_data.get('order_size', 0.01)))  # 每个网格的订单大小
        self.max_position_size = Decimal(str(config_data.get('max_position_size', 0.1)))  # 最大持仓大小
        
        # 风险控制
        self.price_range_percent = Decimal(str(config_data.get('price_range_percent', 5.0)))  # 价格范围百分比
        self.stop_loss_percent = Decimal(str(config_data.get('stop_loss_percent', 10.0)))  # 止损百分比
        
        # 机器人运行配置
        self.check_interval = config_data.get('check_interval', 5)  # 检查间隔（秒）
        self.max_retries = config_data.get('max_retries', 3)  # 最大重试次数
        self.auto_restart = config_data.get('auto_restart', True)  # 自动重启
        
        # 日志配置
        self.log_level = config_data.get('log_level', 'INFO')
        self.log_to_file = config_data.get('log_to_file', True)
        
    def _load_from_env(self):
        """从环境变量加载配置"""
        # EdgeX API 配置
        self.edgex_base_url = os.getenv('EDGEX_BASE_URL', 'https://pro.edgex.exchange')
        self.edgex_ws_url = os.getenv('EDGEX_WS_URL', 'wss://quote.edgex.exchange')
        self.edgex_account_id = os.getenv('EDGEX_ACCOUNT_ID')
        self.edgex_stark_private_key = os.getenv('EDGEX_STARK_PRIVATE_KEY')
        
        # 交易配置
        self.trading_pair = os.getenv('TRADING_PAIR', 'ETH')
        self.grid_count = int(os.getenv('GRID_COUNT', '10'))
        self.grid_spacing_percent = Decimal(os.getenv('GRID_SPACING_PERCENT', '0.5'))
        self.order_size = Decimal(os.getenv('ORDER_SIZE', '0.01'))
        self.max_position_size = Decimal(os.getenv('MAX_POSITION_SIZE', '0.1'))
        
        # 风险控制
        self.price_range_percent = Decimal(os.getenv('PRICE_RANGE_PERCENT', '5.0'))
        self.stop_loss_percent = Decimal(os.getenv('STOP_LOSS_PERCENT', '10.0'))
        
        # 机器人运行配置
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '5'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.auto_restart = os.getenv('AUTO_RESTART', 'true').lower() == 'true'
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_to_file = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    
    def validate(self) -> None:
        """验证配置的有效性"""
        if not self.edgex_account_id:
            raise ValueError("EDGEX_ACCOUNT_ID 必须设置")
        
        if not self.edgex_stark_private_key:
            raise ValueError("EDGEX_STARK_PRIVATE_KEY 必须设置")
        
        if self.grid_count <= 0:
            raise ValueError("网格数量必须大于0")
        
        if self.order_size <= 0:
            raise ValueError("订单大小必须大于0")
        
        if self.grid_spacing_percent <= 0:
            raise ValueError("网格间距百分比必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'edgex_base_url': self.edgex_base_url,
            'edgex_ws_url': self.edgex_ws_url,
            'edgex_account_id': self.edgex_account_id,
            'edgex_stark_private_key': self.edgex_stark_private_key,
            'trading_pair': self.trading_pair,
            'grid_count': self.grid_count,
            'grid_spacing_percent': float(self.grid_spacing_percent),
            'order_size': float(self.order_size),
            'max_position_size': float(self.max_position_size),
            'price_range_percent': float(self.price_range_percent),
            'stop_loss_percent': float(self.stop_loss_percent),
            'check_interval': self.check_interval,
            'max_retries': self.max_retries,
            'auto_restart': self.auto_restart,
            'log_level': self.log_level,
            'log_to_file': self.log_to_file
        }
    
    def save_to_file(self, config_file: str):
        """将配置保存到文件"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
