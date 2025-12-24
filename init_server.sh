#!/bin/bash

# IoT System 服务器初始化脚本
# 用于在服务器上安装必要环境和首次部署

set -e  # 遇到错误时退出

echo "开始初始化 IoT System 服务器环境..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  echo "警告: 建议以root用户运行此脚本，或确保当前用户有sudo权限"
fi

# 更新系统包
echo "更新系统包..."
sudo apt update

# 安装 Python 3.10
echo "安装 Python 3.10..."
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# 安装 Node.js 16
echo "安装 Node.js 16..."
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
echo "验证安装..."
python3.10 --version
node --version

# 安装 Git（如果尚未安装）
echo "安装 Git..."
sudo apt install -y git

# 创建项目目录
echo "创建项目目录..."
PROJECT_DIR="$HOME/IoT_System"
mkdir -p $PROJECT_DIR

# 如果目录为空，克隆项目（如果需要）
if [ -z "$(ls -A $PROJECT_DIR)" ]; then
  echo "项目目录为空，请克隆项目代码到 $PROJECT_DIR"
  echo "示例命令："
  echo "cd $PROJECT_DIR"
  echo "git clone <your-repo-url> ."
else
  echo "项目目录已存在，跳过克隆"
fi

# 安装 Python 依赖
echo "安装 Python 依赖..."
cd $PROJECT_DIR/backend
pip3 install -r requirements.txt || {
    echo "requirements.txt 不存在，安装默认依赖..."
    pip3 install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
}

# 安装前端依赖
echo "安装前端依赖..."
cd $PROJECT_DIR/frontend
npm install

echo "服务器环境初始化完成！"

echo ""
echo "接下来的步骤："
echo "1. 配置 GitHub Secrets 以启用自动部署"
echo "2. 首次启动服务："
echo "   cd $PROJECT_DIR/backend"
echo "   nohup python3 subscribe.py > subscribe.log 2>&1 &"
echo "   nohup python3 publish.py > publish.log 2>&1 &"
echo "   nohup python3 data_address.py > analysis.log 2>&1 &"
echo "   nohup python3 app.py > app.log 2>&1 &"
echo "3. 启动前端服务："
echo "   cd $PROJECT_DIR/frontend"
echo "   nohup npm run dev > frontend.log 2>&1 &"
echo ""
echo "服务启动后，可通过以下地址访问："
echo "- 前端界面: http://<服务器IP>:5173"
echo "- 发布端API: http://<服务器IP>:5000"
echo "- 订阅端API: http://<服务器IP>:5001"
echo "- 数据分析API: http://<服务器IP>:5002"