# IoT System 部署指南

## 一、概述

本指南介绍如何将 IoT System 部署到服务器上，系统包括：
- MQTT 数据发布端
- MQTT 数据订阅端
- 数据分析服务
- 前端界面

## 二、服务器环境要求

- 操作系统：Linux 或 Windows
- Python ≥ 3.10
- Node.js ≥ 16
- MQTT Broker（已配置在 121.43.119.155:1883）

## 三、部署方式

### 方式一：手动部署

1. **上传代码到服务器**

   ```bash
   # 通过 git clone 或其他方式上传代码
   git clone <your-repo-url>
   cd IoT_System
   ```

2. **运行部署脚本**

   Linux:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

   Windows:
   ```cmd
   deploy.bat
   ```

3. **配置环境变量（可选）**

   复制 `.env.example` 为 `.env` 并根据需要修改配置：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

4. **启动服务**

   - 启动 MQTT 服务（如果服务器上未运行）
   - 启动后端服务（在不同终端运行）：
     ```bash
     cd backend
     python publish.py    # 发布服务
     python subscribe.py  # 订阅服务
     python data_address.py  # 数据分析服务
     ```
   - 启动前端服务：
     ```bash
     cd frontend
     npm run dev
     ```

### 方式二：Docker 部署

1. **安装 Docker 和 Docker Compose**

2. **启动服务**

   ```bash
   docker-compose up -d
   ```

   这将启动：
   - EMQX MQTT 服务
   - 后端服务
   - 前端服务

## 四、服务端口说明

- 前端访问：`http://<服务器IP>:5173`
- 发布端API：`http://<服务器IP>:5000`
- 订阅端API：`http://<服务器IP>:5001`
- 数据分析API：`http://<服务器IP>:5002`
- WebSocket连接：`ws://<服务器IP>:8765`
- EMQX Dashboard：`http://<服务器IP>:18083`

## 五、配置说明

系统使用 `backend/config.py` 进行统一配置，支持通过环境变量进行覆盖：

- `MQTT_BROKER`: MQTT 服务器地址
- `MQTT_PORT`: MQTT 端口
- `MQTT_USERNAME`: MQTT 用户名
- `MQTT_PASSWORD`: MQTT 密码
- 各服务端口号可在配置文件中修改

## 六、验证部署

1. 访问前端界面：`http://<服务器IP>:5173`
2. 检查各服务是否正常启动
3. 确认能够连接到 MQTT 服务
4. 验证数据发布和订阅功能

## 七、故障排除

- 确保防火墙开放相应端口
- 检查 MQTT 服务是否正常运行
- 查看服务日志以获取错误信息
- 确认环境变量配置正确