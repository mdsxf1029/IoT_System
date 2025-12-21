import os
import json
import csv
import threading
import time
import asyncio
from typing import Set

from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import websockets

# ========================
# Path config
# ========================
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "sensor_data.csv")

CSV_FIELDS = ["timestamp", "temperature", "humidity", "pressure", "raw"]

# ========================
# MQTT default config
# ========================
BROKER = "121.43.119.155"
PORT = 1883
TOPIC = "iot/area1/environment"
USERNAME = "admin"
PASSWORD = "Aaa123456"

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
ws_loop = None
ws_clients: Set[websockets.WebSocketServerProtocol] = set()
ws_lock = threading.Lock()

# ========================
# CSV helper
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
            "raw": json.dumps(data)
        })

# ========================
# MQTT callbacks
# ========================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status["connected"] = True
        print("MQTT 连接成功")
        client.subscribe(mqtt_status["topic"])
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

        if ws_loop:
            asyncio.run_coroutine_threadsafe(
                broadcast_ws(payload), ws_loop
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
# WebSocket server
# ========================
async def ws_handler(websocket):
    with ws_lock:
        ws_clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        with ws_lock:
            ws_clients.remove(websocket)

async def broadcast_ws(data):
    message = json.dumps(data)
    with ws_lock:
        clients = list(ws_clients)
    for ws in clients:
        try:
            await ws.send(message)
        except:
            pass

def start_ws():
    global ws_loop
    ws_loop = asyncio.new_event_loop()

    async def runner():
        await websockets.serve(ws_handler, "0.0.0.0", 8765)
        print("WebSocket 运行于 ws://127.0.0.1:8765")
        await asyncio.Future()

    def loop():
        asyncio.set_event_loop(ws_loop)
        ws_loop.run_until_complete(runner())

    threading.Thread(target=loop, daemon=True).start()

# ========================
# Flask API
# ========================
app = Flask(__name__)
CORS(app)

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

# ========================
# Main
# ========================
if __name__ == "__main__":
    ensure_csv()
    start_ws()
    app.run(host="127.0.0.1", port=5001, debug=True)
