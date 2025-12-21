# IoT_System
2025-2026物联网期末项目《区域环境数据发布、订阅与分析系统》

**Regional Environmental Data Publishing, Subscription and Analysis System**

## 一、项目基本信息

### 1. 项目名称

区域环境数据发布、订阅与分析系统（IoT 环境数据系统）

### 2. 项目成员与分工

| 姓名     | 学号         | 主要分工                         |
| ------ | ---------- | ---------------------------- |
| 谢雨霏 | 2354264 | 数据处理部分:通过订阅方式接收一定的发布数据，进行本地存储，然后进行处理分析 |
| 张诗蔻 | 2353240 | 发布端:从数据文件中读取有关数据，通过MQTT代理发布 |
| 纪鹏 | 2351869 | 订阅端:订阅有关主题数据，通过MQTT连接接收有关主题数据  |
| 黄云辉 | 2352364 | MQTT代理/服务端:部署MQTT服务器，实现MQTT代理和服务 |

## 二、项目简介

本项目基于 **MQTT 协议** 与 **前后端分离架构**，实现了一个完整的物联网环境数据系统，涵盖：

* 环境数据的**模拟发布**
* 数据的**实时订阅与存储**
* 数据的**统计分析与趋势预测**
* 数据在前端页面的**实时展示与分析可视化**

系统模拟真实物联网场景下温度、湿度、气压等环境数据在不同模块间的流转过程，体现了 MQTT 在 IoT 系统中的核心作用。

## 三、、系统功能说明

### 1. 数据发布端（Backend）

* 从本地 `txt` 文件读取历史环境数据
* 按时间顺序逐条发布 MQTT 消息
* 提供 REST API 控制发布过程：

  * 启动发布
  * 停止发布
  * 查看发布状态

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

* 连接 MQTT Broker，订阅指定主题
* 实时接收发布端发送的数据
* 将接收到的数据保存为本地 CSV 文件
* 通过 WebSocket 向前端实时推送数据
* 支持断线重连与异常处理

### 3. 数据分析端（Backend）

* 从 CSV 文件读取订阅到的历史数据
* 计算基础统计指标（最大值、最小值、平均值）
* 对数据进行平滑处理
* 基于线性回归进行趋势拟合与简单预测
* 提供统一 REST API 给前端调用

## 四、项目文件结构说明

```
IoT_System/
├── backend/
│   ├── publish.py          # 数据发布端后端
│   ├── subscribe.py        # 数据订阅端后端（MQTT + WebSocket）
│   ├── app.py
│   └── data_address.py              # 数据分析后端
├── data/
│   ├──temperature.txt
│   ├── humidity.txt
│   ├── pressure.txt
│   └── sensor_data.csv              # 订阅端存入的数据
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Publish.vue          # 发布端前端
│   │   │   ├── Subscribe.vue        # 订阅端前端
│   │   │   └── DataDisplay.vue      # 数据分析前端
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
│
└── README.md
```

## 五、运行环境要求

* Python ≥ 3.10（推荐 3.10–3.12）
* Node.js ≥ 16
* MQTT Broker（本项目使用 EMQX）

### Python 依赖

```bash
pip install flask flask-cors paho-mqtt pandas numpy scikit-learn websockets
```

### 前端依赖

```bash
npm install
```

## 六、系统运行步骤

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

---

### 4️⃣ 启动数据分析后端

```bash
python backend/app.py
```

---

### 5️⃣ 启动前端页面

```bash
cd frontend
npm run dev
```

浏览器访问：

```
http://localhost:5173
```

## 七、界面设计说明

* 整体采用简洁卡片式布局
* 使用浅色背景与阴影增强层次感
* 表格与图表均支持自适应窗口大小
* 数据实时刷新，提升系统交互体验
