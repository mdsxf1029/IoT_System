#!/bin/bash

# IoT System 部署脚本
# 用于在服务器上部署和启动 IoT 系统

set -e  # 遇到错误时退出

echo "开始部署 IoT System..."

# 检查 Python 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查 pip 是否已安装
if ! command -v pip &> /dev/null; then
    echo "错误: 未找到 pip，请先安装 pip"
    exit 1
fi

echo "正在安装 Python 依赖..."
cd backend
pip install -r requirements.txt || {
    echo "正在安装依赖包..."
    pip install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
}
cd ..

# 检查 Node.js 是否已安装
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查 npm 是否已安装
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请先安装 Node.js"
    exit 1
fi

echo "正在安装前端依赖..."
cd frontend
npm install
cd ..

echo "部署完成！"

echo ""
echo "启动服务说明："
echo "1. 启动 MQTT Broker (EMQX) - 确保已在服务器运行"
echo "2. 启动订阅端服务: cd backend && python subscribe.py"
echo "3. 启动发布端服务: cd backend && python publish.py"
echo "4. 启动数据分析服务: cd backend && python data_address.py"
echo "5. 启动前端服务: cd frontend && npm run dev"
echo ""
echo "或者使用以下命令一键启动所有后端服务（需要在不同终端运行）："
echo "nohup python backend/subscribe.py > subscribe.log 2>&1 &"
echo "nohup python backend/publish.py > publish.log 2>&1 &"
echo "nohup python backend/data_address.py > analysis.log 2>&1 &"