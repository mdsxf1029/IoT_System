import os
import json
import csv
import threading
import time
import asyncio
from typing import Set

from flask import Flask, jsonify, Blueprint
from flask_cors import CORS
import paho.mqtt.client as mqtt
import websockets
from config import Config

subscribe_bp = Blueprint('subscribe', __name__)

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
            try:
                server = await websockets.serve(ws_handler, "0.0.0.0", Config.WEBSOCKET_PORT)
                print(
                    f"WebSocket 运行于 ws://{Config.WEBSOCKET_HOST}:{Config.WEBSOCKET_PORT}")
                await server.wait_closed()
            except OSError as e:
                if e.errno == 10048:  # 端口已被使用
                    print(f"端口 {Config.WEBSOCKET_PORT} 已被占用，无法启动WebSocket服务器")
                    import asyncio
                    await asyncio.sleep(5)  # 等待5秒后退出
                    return  # 不再重试，避免无限递归
                else:
                    print(f"WebSocket服务器启动失败: {e}")

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
# Flask API
# ========================
@subscribe_bp.route("/api/connect", methods=["POST"])
def api_connect():
    connect_mqtt()
    return jsonify({"msg": "connected", "status": mqtt_status})


@subscribe_bp.route("/api/disconnect", methods=["POST"])
def api_disconnect():
    disconnect_mqtt()
    return jsonify({"msg": "disconnected"})


@subscribe_bp.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(mqtt_status)


@subscribe_bp.route("/api/history", methods=["GET"])
def api_history():
    data = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    return jsonify(data[-50:])


if __name__ == '__main__':
    # 启动WebSocket服务器线程
    start_ws_server()
    # 自动开启MQTT订阅
    connect_mqtt()

    print(f"WebSocket服务运行在端口 {Config.WEBSOCKET_PORT}")
    print("MQTT订阅服务已启动")
    print("按 Ctrl+C 停止服务")
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        disconnect_mqtt()
