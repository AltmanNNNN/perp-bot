# 🚀 快速启动指南

## 📋 准备工作

✅ **已完成的设置**：
- EdgeX Python SDK 已安装
- 配置文件 `config.json` 已创建并设置了您的API密钥
- 机器人功能测试通过

✅ **当前配置**：
- 交易对：ETH/USD
- 网格数量：10个
- 订单大小：0.02 ETH
- 最大持仓：0.1 ETH
- 价格范围：±5%
- 网格间距：0.5%

## 🎯 启动机器人

### 1. 基本启动命令

```bash
cd grid_trading_bot
python3 main.py run -c config.json
```

### 2. 使用启动脚本

```bash
cd grid_trading_bot
./start.sh config.json
```

### 3. 后台运行

```bash
cd grid_trading_bot
nohup python3 main.py run -c config.json > bot.log 2>&1 &
```

## 📊 监控机器人

### 查看实时日志
```bash
tail -f logs/grid_trading_bot_$(date +%Y%m%d).log
```

### 查看账户余额
```bash
python3 main.py balance -c config.json
```

### 检查机器人进程
```bash
ps aux | grep main.py
```

## ⚠️ 重要提醒

### 当前账户状态
- **持仓**：-0.12 ETH (空头持仓)
- **余额**：0 USDC
- **状态**：账户可能需要充值以支持网格交易

### 资金建议
1. **建议充值**：至少100-200 USDC作为保证金
2. **风险控制**：当前持仓-0.12 ETH，已接近最大持仓限制(0.1 ETH)
3. **网格范围**：当前ETH价格约4468 USDC，网格范围4245-4692 USDC

## 🛑 停止机器人

### 优雅停止
在运行的终端中按 `Ctrl+C`

### 强制停止后台进程
```bash
pkill -f "main.py run"
```

## 📈 预期运行效果

机器人启动后将：

1. **放置网格订单**：在4245-4692 USDC范围内放置买卖订单
2. **自动交易**：价格波动时自动成交订单
3. **重新平衡**：订单成交后自动放置新订单
4. **风险控制**：监控持仓大小，防止超过限制

## 🔍 故障排除

### 常见问题

1. **余额不足**
   ```
   解决：充值USDC到账户
   ```

2. **持仓超限**
   ```
   解决：调整max_position_size或平仓部分持仓
   ```

3. **网络连接问题**
   ```
   解决：检查网络连接，机器人会自动重试
   ```

4. **订单被拒绝**
   ```
   解决：检查价格是否合理，账户余额是否充足
   ```

## 📞 获取帮助

如遇问题，请检查：
1. 日志文件：`logs/grid_trading_bot_YYYYMMDD.log`
2. 配置文件：确认参数设置正确
3. 网络状态：确认能正常访问EdgeX API

---

**准备好了吗？运行以下命令启动您的网格交易机器人：**

```bash
cd grid_trading_bot
python3 main.py run -c config.json
```

🎉 **祝您交易愉快！**
