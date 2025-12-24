#!/bin/bash

# IoT System 服务管理脚本
# 用于启动、停止、重启和查看服务状态

set -e

# 服务配置
PROJECT_DIR="$HOME/IoT_System"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 服务日志文件
SUBSCRIBE_LOG="$BACKEND_DIR/subscribe.log"
PUBLISH_LOG="$BACKEND_DIR/publish.log"
ANALYSIS_LOG="$BACKEND_DIR/analysis.log"
APP_LOG="$BACKEND_DIR/app.log"
FRONTEND_LOG="$FRONTEND_DIR/frontend.log"

# 服务进程名
SUBSCRIBE_PROC="python.*subscribe.py"
PUBLISH_PROC="python.*publish.py"
ANALYSIS_PROC="python.*data_address.py"
APP_PROC="python.*app.py"
FRONTEND_PROC="npm.*run.*dev"

case "$1" in
  start)
    echo "启动 IoT System 服务..."
    
    # 启动后端服务
    cd $BACKEND_DIR
    if ! pgrep -f "$SUBSCRIBE_PROC" > /dev/null; then
        echo "启动订阅服务..."
        nohup python subscribe.py > $SUBSCRIBE_LOG 2>&1 &
        echo $! > subscribe.pid
    else
        echo "订阅服务已在运行"
    fi
    
    if ! pgrep -f "$PUBLISH_PROC" > /dev/null; then
        echo "启动发布服务..."
        nohup python publish.py > $PUBLISH_LOG 2>&1 &
        echo $! > publish.pid
    else
        echo "发布服务已在运行"
    fi
    
    if ! pgrep -f "$ANALYSIS_PROC" > /dev/null; then
        echo "启动数据分析服务..."
        nohup python data_address.py > $ANALYSIS_LOG 2>&1 &
        echo $! > analysis.pid
    else
        echo "数据分析服务已在运行"
    fi
    
    if ! pgrep -f "$APP_PROC" > /dev/null; then
        echo "启动通用后端服务..."
        nohup python app.py > $APP_LOG 2>&1 &
        echo $! > app.pid
    else
        echo "通用后端服务已在运行"
    fi
    
    # 启动前端服务
    cd $FRONTEND_DIR
    if ! pgrep -f "$FRONTEND_PROC" > /dev/null; then
        echo "启动前端服务..."
        nohup npm run dev > $FRONTEND_LOG 2>&1 &
        echo $! > frontend.pid
    else
        echo "前端服务已在运行"
    fi
    
    echo "所有服务启动完成！"
    ;;

  stop)
    echo "停止 IoT System 服务..."
    
    # 停止后端服务
    if pgrep -f "$SUBSCRIBE_PROC" > /dev/null; then
        echo "停止订阅服务..."
        pkill -f "$SUBSCRIBE_PROC"
        rm -f $BACKEND_DIR/subscribe.pid
    else
        echo "订阅服务未运行"
    fi
    
    if pgrep -f "$PUBLISH_PROC" > /dev/null; then
        echo "停止发布服务..."
        pkill -f "$PUBLISH_PROC"
        rm -f $BACKEND_DIR/publish.pid
    else
        echo "发布服务未运行"
    fi
    
    if pgrep -f "$ANALYSIS_PROC" > /dev/null; then
        echo "停止数据分析服务..."
        pkill -f "$ANALYSIS_PROC"
        rm -f $BACKEND_DIR/analysis.pid
    else
        echo "数据分析服务未运行"
    fi
    
    if pgrep -f "$APP_PROC" > /dev/null; then
        echo "停止通用后端服务..."
        pkill -f "$APP_PROC"
        rm -f $BACKEND_DIR/app.pid
    else
        echo "通用后端服务未运行"
    fi
    
    # 停止前端服务
    if pgrep -f "$FRONTEND_PROC" > /dev/null; then
        echo "停止前端服务..."
        pkill -f "$FRONTEND_PROC"
        rm -f $FRONTEND_DIR/frontend.pid
    else
        echo "前端服务未运行"
    fi
    
    echo "所有服务已停止！"
    ;;

  restart)
    echo "重启 IoT System 服务..."
    $0 stop
    sleep 3
    $0 start
    ;;

  status)
    echo "IoT System 服务状态："
    
    if pgrep -f "$SUBSCRIBE_PROC" > /dev/null; then
        echo "✓ 订阅服务: 运行中 (PID: $(pgrep -f "$SUBSCRIBE_PROC"))"
    else
        echo "✗ 订阅服务: 已停止"
    fi
    
    if pgrep -f "$PUBLISH_PROC" > /dev/null; then
        echo "✓ 发布服务: 运行中 (PID: $(pgrep -f "$PUBLISH_PROC"))"
    else
        echo "✗ 发布服务: 已停止"
    fi
    
    if pgrep -f "$ANALYSIS_PROC" > /dev/null; then
        echo "✓ 数据分析服务: 运行中 (PID: $(pgrep -f "$ANALYSIS_PROC"))"
    else
        echo "✗ 数据分析服务: 已停止"
    fi
    
    if pgrep -f "$APP_PROC" > /dev/null; then
        echo "✓ 通用后端服务: 运行中 (PID: $(pgrep -f "$APP_PROC"))"
    else
        echo "✗ 通用后端服务: 已停止"
    fi
    
    if pgrep -f "$FRONTEND_PROC" > /dev/null; then
        echo "✓ 前端服务: 运行中 (PID: $(pgrep -f "$FRONTEND_PROC"))"
    else
        echo "✗ 前端服务: 已停止"
    fi
    ;;

  logs)
    echo "查看服务日志 (按 Ctrl+C 退出)..."
    tail -f $SUBSCRIBE_LOG $PUBLISH_LOG $ANALYSIS_LOG $APP_LOG $FRONTEND_LOG
    ;;

  *)
    echo "用法: $0 {start|stop|restart|status|logs}"
    echo "  start  - 启动所有服务"
    echo "  stop   - 停止所有服务"
    echo "  restart - 重启所有服务"
    echo "  status - 查看服务状态"
    echo "  logs   - 查看服务日志"
    exit 1
    ;;
esac

exit 0