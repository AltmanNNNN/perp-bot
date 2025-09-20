# 🔧 配置参数详细指南

## 📋 配置文件结构

您的 `config.json` 文件包含以下配置项：

## 🌐 EdgeX API 配置

### `edgex_base_url`
- **默认值**: `"https://pro.edgex.exchange"`
- **说明**: EdgeX API 基础URL
- **注意**: 生产环境使用，测试网请改为测试URL

### `edgex_ws_url`
- **默认值**: `"wss://quote.edgex.exchange"`
- **说明**: EdgeX WebSocket URL，用于实时数据
- **注意**: 与base_url对应

### `edgex_account_id`
- **当前值**: `"662055685596381613"`
- **说明**: 您的EdgeX账户ID
- **注意**: 请勿泄露给他人

### `edgex_stark_private_key`
- **当前值**: `"02402bfbc4cd47ee01d0e4a41e66fc27a3d08966ff6471fe10046e9e952ae1f4"`
- **说明**: Stark私钥，用于签名交易
- **注意**: 极其重要，请妥善保管

## 💹 交易参数配置

### `trading_pair`
- **当前值**: `"ETH"`
- **说明**: 交易对名称
- **可选值**: `ETH`, `BTC`, `BNB`, `SOL` 等
- **建议**: 选择流动性好的主流币种

### `grid_count`
- **当前值**: `10`
- **说明**: 网格数量
- **范围**: 5-20
- **建议**:
  - 新手: 8-10个
  - 有经验: 10-15个
  - 激进: 15-20个

### `grid_spacing_percent`
- **当前值**: `0.5`
- **说明**: 网格间距百分比
- **范围**: 0.1-2.0
- **建议**:
  - 震荡市场: 0.3-0.5%
  - 趋势市场: 0.8-1.2%
  - 高波动: 1.5-2.0%

### `order_size`
- **当前值**: `0.02`
- **说明**: 每个网格的订单大小
- **最小值**: 
  - ETH: 0.02
  - BTC: 0.001
- **建议**: 根据资金量和风险承受能力调整

### `max_position_size`
- **当前值**: `0.1`
- **说明**: 最大持仓限制
- **建议**:
  - 保守: 0.05-0.1
  - 平衡: 0.1-0.2
  - 激进: 0.2-0.5

## 🛡️ 风险控制配置

### `price_range_percent`
- **当前值**: `5.0`
- **说明**: 网格价格范围（当前价格±5%）
- **建议**:
  - 稳定币种: 3-5%
  - 主流币种: 5-8%
  - 山寨币: 8-15%

### `stop_loss_percent`
- **当前值**: `10.0`
- **说明**: 止损百分比（功能待实现）
- **用途**: 预留参数，未来版本使用

## ⚙️ 运行参数配置

### `check_interval`
- **当前值**: `5`
- **说明**: 检查间隔（秒）
- **范围**: 3-30秒
- **建议**:
  - 高频交易: 3-5秒
  - 正常使用: 5-10秒
  - 稳定优先: 10-30秒

### `max_retries`
- **当前值**: `3`
- **说明**: 最大重试次数
- **建议**: 3-5次，网络不稳定时增加

### `auto_restart`
- **当前值**: `true`
- **说明**: 自动重启开关
- **建议**: 建议开启，增强稳定性

## 📝 日志配置

### `log_level`
- **当前值**: `"INFO"`
- **可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **建议**:
  - 调试: `DEBUG`
  - 正常: `INFO`
  - 生产: `WARNING`

### `log_to_file`
- **当前值**: `true`
- **说明**: 是否记录到文件
- **建议**: 建议开启，便于问题排查

## 🎯 配置模板

### 保守型配置（新手推荐）
```json
{
  "trading_pair": "ETH",
  "grid_count": 8,
  "grid_spacing_percent": 0.8,
  "order_size": 0.02,
  "max_position_size": 0.05,
  "price_range_percent": 3.0,
  "check_interval": 10
}
```

### 平衡型配置（当前设置）
```json
{
  "trading_pair": "ETH",
  "grid_count": 10,
  "grid_spacing_percent": 0.5,
  "order_size": 0.02,
  "max_position_size": 0.1,
  "price_range_percent": 5.0,
  "check_interval": 5
}
```

### 激进型配置（有经验用户）
```json
{
  "trading_pair": "ETH",
  "grid_count": 15,
  "grid_spacing_percent": 0.3,
  "order_size": 0.05,
  "max_position_size": 0.2,
  "price_range_percent": 8.0,
  "check_interval": 3
}
```

## ⚠️ 重要提醒

1. **API密钥安全**: 请妥善保管您的账户ID和私钥
2. **资金管理**: 建议只使用您能承受损失的资金
3. **测试运行**: 首次使用建议小额测试
4. **监控日志**: 定期检查日志文件了解运行状态
5. **风险控制**: 合理设置持仓限制和价格范围

## 🔄 修改配置

修改配置后需要重启机器人：
1. 停止当前运行的机器人（Ctrl+C）
2. 修改 `config.json` 文件
3. 验证配置：`python3 main.py validate -c config.json`
4. 重新启动：`python3 main.py run -c config.json`

---

**需要帮助？** 请查看 `README.md` 或 `QUICK_START.md` 文件获取更多信息。
