@echo off
chcp 65001 >nul
echo 开始部署 IoT System...

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查 pip 是否已安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 pip，请先安装 pip
    pause
    exit /b 1
)

echo 正在安装 Python 依赖...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
)
cd ..

REM 检查 Node.js 是否已安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

REM 检查 npm 是否已安装
npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 npm，请先安装 Node.js
    pause
    exit /b 1
)

echo 正在安装前端依赖...
cd frontend
npm install
cd ..

echo 部署完成！

echo.
echo 启动服务说明：
echo 1. 启动 MQTT Broker (EMQX) - 确保已在服务器运行
echo 2. 启动订阅端服务: cd backend ^&^& python subscribe.py
echo 3. 启动发布端服务: cd backend ^&^& python publish.py
echo 4. 启动数据分析服务: cd backend ^&^& python data_address.py
echo 5. 启动前端服务: cd frontend ^&^& npm run dev
echo.
echo 或者使用以下命令启动服务：
echo start /b python backend/subscribe.py
echo start /b python backend/publish.py
echo start /b python backend/data_address.py
pause