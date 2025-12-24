@echo off
chcp 65001 >nul
echo 开始初始化 IoT System 服务器环境...

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查 Node.js 是否已安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js 16+
    pause
    exit /b 1
)

REM 检查 Git 是否已安装
git --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Git，请先安装 Git
    pause
    exit /b 1
)

echo Python、Node.js 和 Git 已安装，继续初始化...

REM 创建项目目录
if not exist "%USERPROFILE%\IoT_System" (
    mkdir "%USERPROFILE%\IoT_System"
    echo 项目目录已创建: %USERPROFILE%\IoT_System
) else (
    echo 项目目录已存在: %USERPROFILE%\IoT_System
)

REM 检查项目是否已存在
cd /d "%USERPROFILE%\IoT_System"
if not exist "backend" (
    echo 项目代码不存在，请克隆项目到 %USERPROFILE%\IoT_System
    echo 示例命令：
    echo cd %USERPROFILE%\IoT_System
    echo git clone ^<your-repo-url^> .
    pause
    exit /b 0
)

REM 安装 Python 依赖
echo 安装 Python 依赖...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo 安装默认依赖包...
    pip install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
)

REM 安装前端依赖
echo 安装前端依赖...
cd ..\frontend
npm install

echo 服务器环境初始化完成！

echo.
echo 接下来的步骤：
echo 1. 配置 GitHub Secrets 以启用自动部署
echo 2. 首次启动服务：
echo    cd %%USERPROFILE%%\IoT_System\backend
echo    start /b python subscribe.py
echo    start /b python publish.py
echo    start /b python data_address.py
echo    start /b python app.py
echo 3. 启动前端服务：
echo    cd %%USERPROFILE%%\IoT_System\frontend
echo    start /b npm run dev
echo.
echo 服务启动后，可通过以下地址访问：
echo - 前端界面: http://^<服务器IP^>:5173
echo - 发布端API: http://^<服务器IP^>:5000
echo - 订阅端API: http://^<服务器IP^>:5001
echo - 数据分析API: http://^<服务器IP^>:5002

pause