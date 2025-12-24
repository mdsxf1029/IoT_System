"""
综合服务 - 将订阅和分析服务整合到一个端口
"""
import os
import json
import csv
import threading
import time
import asyncio
from typing import Set
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

from flask import Flask, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import websockets
from config import Config


# ========================
# Path config
# ========================
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "sensor_data.csv")

CSV_FIELDS = ["timestamp", "temperature", "humidity", "pressure", "raw"]

# ========================
# MQTT config
# ========================
BROKER = Config.MQTT_BROKER
PORT = Config.MQTT_PORT
TOPIC = Config.MQTT_TOPIC
USERNAME = Config.MQTT_USERNAME
PASSWORD = Config.MQTT_PASSWORD

# ========================
# Runtime state
# ========================
mqtt_client = None
mqtt_lock = threading.Lock()
user_requested_disconnect = False

mqtt_status = {
    "connected": False,
    "broker": BROKER,
    "port": PORT,
    "topic": TOPIC,
    "error": None
}

# ========================
# WebSocket state
# ========================
ws_loop: asyncio.AbstractEventLoop | None = None
ws_clients: Set[websockets.WebSocketServerProtocol] = set()
ws_lock = threading.Lock()

# ========================
# CSV helpers
# ========================


def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def append_csv(data: dict):
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow({
            "timestamp": data.get("timestamp"),
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
            "pressure": data.get("pressure"),
            "raw": json.dumps(data, ensure_ascii=False)
        })

# ========================
# WebSocket logic
# ========================


async def ws_handler(websocket):
    with ws_lock:
        ws_clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        with ws_lock:
            ws_clients.discard(websocket)


async def broadcast_ws(data: dict):
    message = json.dumps(data, ensure_ascii=False)
    with ws_lock:
        clients = list(ws_clients)

    for ws in clients:
        try:
            await ws.send(message)
        except:
            pass


def start_ws_server():
    def ws_thread():
        global ws_loop
        ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(ws_loop)

        async def start_server():
            # 使用 0.0.0.0 以允许外部连接
            await websockets.serve(ws_handler, "0.0.0.0", Config.WEBSOCKET_PORT)
            print(
                f"WebSocket 运行于 ws://{Config.WEBSOCKET_HOST}:{Config.WEBSOCKET_PORT}")

        ws_loop.run_until_complete(start_server())
        ws_loop.run_forever()

    threading.Thread(target=ws_thread, daemon=True).start()

# ========================
# MQTT callbacks
# ========================


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status["connected"] = True
        print("MQTT 连接成功")
        client.subscribe(TOPIC)
    else:
        mqtt_status["error"] = f"rc={rc}"


def on_disconnect(client, userdata, rc):
    mqtt_status["connected"] = False
    print("MQTT 断开连接")

    if not user_requested_disconnect:
        def reconnect():
            while True:
                try:
                    print("尝试重连 MQTT...")
                    client.reconnect()
                    return
                except:
                    time.sleep(3)
        threading.Thread(target=reconnect, daemon=True).start()


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        append_csv(payload)
        print("收到 MQTT 数据:", payload)

        if ws_loop:
            asyncio.run_coroutine_threadsafe(
                broadcast_ws(payload),
                ws_loop
            )
    except Exception as e:
        print("消息处理失败:", e)

# ========================
# MQTT control
# ========================


def connect_mqtt():
    global mqtt_client, user_requested_disconnect

    with mqtt_lock:
        if mqtt_client:
            return

        user_requested_disconnect = False

        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        client.connect(BROKER, PORT, 60)
        client.loop_start()

        mqtt_client = client


def disconnect_mqtt():
    global mqtt_client, user_requested_disconnect

    with mqtt_lock:
        if mqtt_client:
            user_requested_disconnect = True
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            mqtt_client = None


# ========================
# 数据分析服务
# ========================
class DataProcessor:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        # 系统支持的指标维度
        self.metrics = ["temperature", "humidity", "pressure"]

    def predict_series(self, df, column, points=5):
        """
        对单个时间序列做线性回归拟合与简单预测
        """
        if column not in df.columns:
            return [], []

        y = df[column].values
        if len(y) < 2:
            return [], []

        X = np.arange(len(y)).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)

        fitted = model.predict(X).tolist()
        future_X = np.arange(len(y), len(y) + points).reshape(-1, 1)
        future = model.predict(future_X).tolist()

        return fitted, future

    def process(self):
        # ----------------------------------------------------
        # CSV 文件检查
        # ----------------------------------------------------
        if not os.path.exists(self.csv_path):
            return {"error": "Wait for data... CSV file not found."}

        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            return {"error": f"Read CSV failed: {str(e)}"}

        if df.empty or len(df) < 2:
            return {"error": "Need more data points for analysis."}

        # ----------------------------------------------------
        # 判断实际存在的指标（兼容未订阅情况）
        # ----------------------------------------------------
        available_metrics = [m for m in self.metrics if m in df.columns]
        if not available_metrics:
            return {"error": "No valid sensor data found."}

        # 转换为数值类型
        for m in available_metrics:
            df[m] = pd.to_numeric(df[m], errors="coerce")

        df = df.dropna(subset=available_metrics)

        if df.empty:
            return {"error": "All sensor data is invalid after cleaning."}

        # ----------------------------------------------------
        # 基础统计
        # ----------------------------------------------------
        stats = {}
        for m in available_metrics:
            stats[m] = {
                "max": float(df[m].max()),
                "min": float(df[m].min()),
                "avg": float(df[m].mean().round(2))
            }

        stats["current_count"] = len(df)

        # ----------------------------------------------------
        # 趋势分析（最近 30 个点，滑动平均）
        # ----------------------------------------------------
        plot_df = df.tail(30).copy()

        for m in available_metrics:
            plot_df[f"{m}_smooth"] = plot_df[m].rolling(
                window=5, min_periods=1
            ).mean()

        # ----------------------------------------------------
        # 简单预测（线性回归）
        # ----------------------------------------------------
        analysis_result = {}

        for m in available_metrics:
            fitted, predicted = self.predict_series(plot_df, m)
            analysis_result[m] = {
                "raw": plot_df[m].tolist(),
                "smooth": plot_df[f"{m}_smooth"].tolist(),
                "fitted": fitted,
                "predict": predicted
            }

        # ----------------------------------------------------
        # 相关性分析（至少两个维度才有意义）
        # ----------------------------------------------------
        correlation = {}
        if len(available_metrics) >= 2:
            correlation = (
                df[available_metrics]
                .corr()
                .round(2)
                .to_dict()
            )

        # ----------------------------------------------------
        # 时间格式处理
        # ----------------------------------------------------
        if "timestamp" in plot_df.columns:
            plot_df["timestamp"] = pd.to_datetime(
                plot_df["timestamp"],
                errors="coerce"
            )

            # 转成更短、更适合图表的格式
            plot_df["timestamp_fmt"] = plot_df["timestamp"].dt.strftime(
                "%m-%d %H:%M")
        else:
            plot_df["timestamp_fmt"] = list(range(len(plot_df)))

        # ----------------------------------------------------
        # 返回统一结构，直接给前端
        # ----------------------------------------------------
        return {
            "stats": stats,
            "data": analysis_result,
            "labels": plot_df["timestamp_fmt"].tolist(),
            "correlation": correlation,
            "available_metrics": available_metrics
        }


# ========================
# Flask App
# ========================
app = Flask(__name__)
# 配置CORS以允许跨域请求
CORS(app, resources={r"/*": {"origins": "*",
     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})


# MQTT API endpoints
@app.route("/api/connect", methods=["POST"])
def api_connect():
    connect_mqtt()
    return jsonify({"msg": "connected", "status": mqtt_status})


@app.route("/api/disconnect", methods=["POST"])
def api_disconnect():
    disconnect_mqtt()
    return jsonify({"msg": "disconnected"})


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(mqtt_status)


@app.route("/api/history", methods=["GET"])
def api_history():
    data = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    return jsonify(data[-50:])


# 数据分析 API endpoints
processor = DataProcessor(CSV_PATH)


@app.route("/api/analyze", methods=["GET"])
def analyze_data():
    try:
        result = processor.process()
        return jsonify(result)
    except Exception as e:
        print(f"分析服务错误: {str(e)}")
        return jsonify({"error": f"分析服务错误: {str(e)}"}), 500


if __name__ == "__main__":
    ensure_csv()
    start_ws_server()
    connect_mqtt()
    app.run(host=Config.SUBSCRIBE_SERVICE_HOST,
            port=Config.SUBSCRIBE_SERVICE_PORT, debug=False, use_reloader=False, threaded=True)
