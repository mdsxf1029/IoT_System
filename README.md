# 区域环境数据发布、订阅与分析系统

## 一、项目基本信息

### 1. 项目名称

区域环境数据发布、订阅与分析系统（IoT 环境数据系统）

### 2. 项目成员与分工

| 姓名   | 学号    | 主要分工                                                                    |
| ------ | ------- | --------------------------------------------------------------------------- |
| 谢雨霏 | 2354264 | 数据处理部分:通过订阅方式接收一定的发布数据，进行本地存储，然后进行处理分析 |
| 张诗蔻 | 2353240 | 发布端:从数据文件中读取有关数据，通过MQTT代理发布                           |
| 纪鹏   | 2351869 | 订阅端:订阅有关主题数据，通过MQTT连接接收有关主题数据                       |
| 黄云辉 | 2352364 | MQTT代理/服务端:部署MQTT服务器，实现MQTT代理和服务                          |

## 二、需求说明

### 项目题目

某区域温度/湿度/气压数据发布订阅及分析处理系统

### 项目主要内容

1. 发布端：从数据文件读取有关传感器数据或其它类型数据通过MQTT代理进行发布
2. MQTT代理/服务端：部署MQTT服务器，实现MQTT代理和服务
3. 订阅端：订阅有关主题数据，通过与MQTT代理/服务端连接，接收有关主题数据
4. 数据处理部份：通过订阅方式接收一定的发布数据，进行本地存储，然后进行处理分析
5. 订阅端，发布端和数据处理端需要设计相关图形界面，便于数据发布和订阅，在数据处理以图表方式展示接收数据和分析结果
6. 服务端，代理端和采集发布端可以部署在局域网内不同主机
7. 模拟分析预测数据曲线与历史数据曲线应具备良好的拟合
8. 具体界面展示内容和方式尽量美观合理

## 三、系统设计

### 架构设计

本项目基于 **MQTT 协议** 与 **前后端分离架构**，实现了一个完整的物联网环境数据系统，涵盖：

- 环境数据的**模拟发布**
- 数据的**实时订阅与存储**
- 数据的**统计分析与趋势预测**
- 数据在前端页面的**实时展示与分析可视化**

系统模拟真实物联网场景下温度、湿度、气压等环境数据在不同模块间的流转过程，体现了 MQTT 在 IoT 系统中的核心作用。

### 系统架构图

```
Publisher (Flask API + MQTT Client) 
         ↓ (MQTT messages)
MQTT Broker (EMQX Server)
         ↓ (MQTT messages) 
Subscriber (Flask API + MQTT Client + WebSocket)
         ↓ (Store to CSV)
Data Processor (Flask API + Pandas/Scikit-learn)
         ↓ (Analysis results)
Frontend (Vue.js + WebSocket + REST API)
```

### 技术栈

- **后端**: Python Flask, paho-mqtt, pandas, scikit-learn, websockets
- **前端**: Vue.js 3, Vite, WebSocket, REST API
- **通信协议**: MQTT (EMQX Broker)
- **数据库**: CSV文件存储
- **数据处理**: 线性回归预测、滑动平均平滑处理

## 四、软件说明

### 1. 数据发布端（Backend）

- 从本地 `txt` 文件读取历史环境数据
- 按时间顺序逐条发布 MQTT 消息
- 提供 REST API 控制发布过程：
  - 启动发布
  - 停止发布
  - 查看发布状态

发布的 MQTT 消息格式示例：

```json
{
  "timestamp": "2014-02-13T01:00:00",
  "temperature": 4.0,
  "humidity": 65.0,
  "pressure": 994.0
}
```

### 2. 数据订阅端（Backend）

- 连接 MQTT Broker，订阅指定主题
- 实时接收发布端发送的数据
- 将接收到的数据保存为本地 CSV 文件
- 通过 WebSocket 向前端实时推送数据
- 支持断线重连与异常处理

### 3. 数据分析端（Backend）

- 从 CSV 文件读取订阅到的历史数据
- 计算基础统计指标（最大值、最小值、平均值）
- 对数据进行平滑处理
- 基于线性回归进行趋势拟合与简单预测
- 提供统一 REST API 给前端调用

### 4. 前端界面

- 发布端控制界面：启动/停止发布，查看发布状态
- 订阅端界面：连接/断开MQTT，实时数据显示
- 数据分析界面：图表展示历史数据、平滑处理结果、趋势预测和相关性分析

## 五、项目文件结构说明

```
IoT_System/
├── backend/
│   ├── publish.py          # 数据发布端后端
│   ├── subscribe.py        # 数据订阅端后端（MQTT + WebSocket）
│   ├── data_address.py     # 数据分析后端
│   ├── app.py              # 通用后端服务
│   ├── config.py           # 配置文件
│   └── requirements.txt    # Python依赖
├── data/
│   ├── temperature.txt     # 温度数据文件
│   ├── humidity.txt        # 湿度数据文件
│   ├── pressure.txt        # 气压数据文件
│   └── sensor_data.csv     # 订阅端存入的数据
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Publish.vue          # 发布端前端
│   │   │   ├── Subscribe.vue        # 订阅端前端
│   │   │   └── DataDisplay.vue      # 数据分析前端
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 六、运行环境要求

- Python ≥ 3.10（推荐 3.10–3.12）
- Node.js ≥ 16
- MQTT Broker（本项目使用 EMQX）

### Python 依赖

```bash
pip install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
```

### 前端依赖

```bash
npm install
```

## 七、系统运行步骤

### 1️⃣ 启动 MQTT Broker

使用 EMQX（服务器端已部署）
或使用本地 MQTT Broker。

### 2️⃣ 启动数据发布端

```bash
python backend/publish.py
```

新建终端，启动发布：

```bash
Invoke-RestMethod -Uri "http://127.0.0.1:5000/start" -Method Post
```

### 3️⃣ 启动订阅端后端

```bash
python backend/subscribe.py
```

### 4️⃣ 启动数据分析后端

```bash
python backend/data_address.py
```

### 5️⃣ 启动前端页面

```bash
cd frontend
npm run dev
```

浏览器访问：

```
http://localhost:5173
```

## 八、功能特点

1. **实时数据流**: 通过MQTT协议实现发布-订阅模式的实时数据传输
2. **数据存储**: 订阅数据持久化存储到CSV文件
3. **数据分析**: 提供统计分析、平滑处理和趋势预测功能
4. **实时可视化**: 前端界面实时展示数据和分析结果
5. **响应式界面**: 采用Vue.js构建美观的用户界面
6. **断线重连**: 订阅端支持MQTT断线重连机制
7. **预测分析**: 基于线性回归的简单趋势预测

## 九、项目贡献说明
