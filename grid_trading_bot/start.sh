#!/bin/bash

# EdgeX 网格交易机器人启动脚本
# 
# 使用方法:
#   ./start.sh                    # 使用环境变量启动
#   ./start.sh config.json        # 使用配置文件启动
#   ./start.sh balance            # 查询余额
#   ./start.sh balance config.json # 使用配置文件查询余额

set -e  # 遇到错误时退出

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未找到，请先安装 Python 3.7+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    print_info "Python 版本: $python_version"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        print_success "Python 版本检查通过"
    else
        print_error "Python 版本过低，需要 3.7 或更高版本"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖包..."
    
    # 检查 EdgeX SDK
    if python3 -c "import edgex_sdk" 2>/dev/null; then
        print_success "EdgeX SDK 已安装"
    else
        print_warning "EdgeX SDK 未找到，正在安装..."
        cd ../edgex-python-sdk
        pip install -e .
        cd "$SCRIPT_DIR"
        print_success "EdgeX SDK 安装完成"
    fi
    
    # 检查其他依赖（跳过，因为所有依赖都在EdgeX SDK中）
    print_success "依赖检查完成"
}

# 检查配置
check_config() {
    local config_file="$1"
    
    if [ -n "$config_file" ] && [ "$config_file" != "balance" ]; then
        if [ ! -f "$config_file" ]; then
            print_error "配置文件不存在: $config_file"
            print_info "创建配置文件模板: python3 main.py create-config $config_file"
            exit 1
        fi
        
        print_info "验证配置文件: $config_file"
        if python3 main.py validate -c "$config_file"; then
            print_success "配置文件验证通过"
        else
            print_error "配置文件验证失败"
            exit 1
        fi
    else
        # 检查环境变量
        if [ -z "$EDGEX_ACCOUNT_ID" ] || [ -z "$EDGEX_STARK_PRIVATE_KEY" ]; then
            print_error "环境变量未设置"
            print_info "请设置以下环境变量:"
            echo "  export EDGEX_ACCOUNT_ID=\"your_account_id\""
            echo "  export EDGEX_STARK_PRIVATE_KEY=\"your_stark_private_key\""
            echo ""
            print_info "或者使用配置文件:"
            echo "  python3 main.py create-config config.json"
            echo "  ./start.sh config.json"
            exit 1
        fi
        print_success "环境变量检查通过"
    fi
}

# 创建日志目录
create_log_dir() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_info "创建日志目录: logs/"
    fi
}

# 主函数
main() {
    local command="$1"
    local config_file="$2"
    
    print_info "EdgeX 网格交易机器人启动脚本"
    print_info "==============================="
    
    # 检查环境
    check_python
    check_dependencies
    create_log_dir
    
    # 根据参数执行不同操作
    case "$command" in
        "balance")
            print_info "查询账户余额..."
            check_config "$config_file"
            if [ -n "$config_file" ]; then
                python3 main.py balance -c "$config_file"
            else
                python3 main.py balance
            fi
            ;;
        "")
            # 默认启动机器人
            print_info "启动网格交易机器人..."
            check_config
            python3 main.py run
            ;;
        *)
            # 使用配置文件启动机器人
            config_file="$command"
            print_info "使用配置文件启动机器人: $config_file"
            check_config "$config_file"
            python3 main.py run -c "$config_file"
            ;;
    esac
}

# 信号处理
trap 'print_warning "接收到中断信号，正在关闭..."; exit 0' INT TERM

# 执行主函数
main "$@"
