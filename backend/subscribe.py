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


# -----------------------
# Configuration / paths
# -----------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "sensor_data.csv")

# Defaults (can be overridden by POST /api/subscribe/connect payload or env)
DEFAULT_BROKER = os.environ.get("MQTT_BROKER", "121.43.119.155")
DEFAULT_PORT = int(os.environ.get("MQTT_PORT", 1883))
DEFAULT_TOPIC = os.environ.get("MQTT_TOPIC", "iot/area1/environment")


# -----------------------
# State
# -----------------------
mqtt_client = None
mqtt_lock = threading.Lock()
mqtt_status = {
    "connected": False,
    "broker": None,
    "port": None,
    "topic": None,
    "error": None,
}

# WebSocket server loop and connected clients
ws_loop = None
ws_clients: Set[websockets.WebSocketServerProtocol] = set()
ws_lock = threading.Lock()


# -----------------------
# Helper: CSV persistence
# -----------------------
CSV_FIELDS = ["timestamp", "temperature", "humidity", "pressure", "raw"]

def append_csv(record: dict):
    try:
        exists = os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if not exists:
                writer.writeheader()
            row = {k: record.get(k, "") for k in CSV_FIELDS}
            # keep raw JSON as string
            if "raw" not in row or not row["raw"]:
                row["raw"] = json.dumps(record)
            writer.writerow(row)
    except Exception as e:
        print("CSV 写入失败:", e)


# -----------------------
# MQTT callbacks & control
# -----------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status["connected"] = True
        mqtt_status["error"] = None
        print("MQTT connected")
        # subscribe if topic set
        try:
            topic = mqtt_status.get("topic")
            if topic:
                client.subscribe(topic)
                print("Subscribed to", topic)
        except Exception as e:
            print("subscribe exception:", e)
    else:
        mqtt_status["connected"] = False
        mqtt_status["error"] = f"connect rc={rc}"
        print("MQTT connect failed rc=", rc)


def on_disconnect(client, userdata, rc):
    mqtt_status["connected"] = False
    print("MQTT disconnected rc=", rc)


def valid_sensor_payload(obj: dict) -> bool:
    # Expect keys: timestamp, temperature, humidity, pressure
    try:
        if not isinstance(obj, dict):
            return False
        required = ["timestamp", "temperature", "humidity", "pressure"]
        for k in required:
            if k not in obj:
                return False
        return True
    except Exception:
        return False


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        obj = json.loads(payload)
    except Exception as e:
        print("Invalid MQTT message:", e)
        return

    if not valid_sensor_payload(obj):
        print("Received message missing required fields:", obj)
        return

    # persist
    append_csv(obj)

    # broadcast to websocket clients
    if ws_loop:
        try:
            fut = asyncio.run_coroutine_threadsafe(
                broadcast_event("mqtt_message", obj), ws_loop
            )
            # don't block long; optionally check fut.exception()
        except Exception as e:
            print("Broadcast scheduling failed:", e)


def connect_mqtt(broker=DEFAULT_BROKER, port=DEFAULT_PORT, topic=DEFAULT_TOPIC, username=None, password=None):
    global mqtt_client
    with mqtt_lock:
        if mqtt_client and mqtt_status.get("connected"):
            return True, "already connected"

        try:
            client = mqtt.Client()
            if username:
                client.username_pw_set(username, password or "")
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.on_message = on_message

            client.connect(broker, port, 60)
            client.loop_start()

            mqtt_client = client
            mqtt_status.update({"broker": broker, "port": port, "topic": topic, "error": None})
            # subscribe
            time.sleep(1)
            if topic:
                client.subscribe(topic)
            return True, "connected"
        except Exception as e:
            mqtt_status["error"] = str(e)
            return False, str(e)


def disconnect_mqtt():
    global mqtt_client
    with mqtt_lock:
        if not mqtt_client:
            return True, "not connected"
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            mqtt_client = None
            mqtt_status.update({"connected": False})
            return True, "disconnected"
        except Exception as e:
            mqtt_status["error"] = str(e)
            return False, str(e)


# -----------------------
# WebSocket server
# -----------------------
async def ws_handler(websocket, path):
    # register
    with ws_lock:
        ws_clients.add(websocket)
    try:
        async for _ in websocket:
            # no-op: server is push-only, but keep connection open
            pass
    finally:
        with ws_lock:
            if websocket in ws_clients:
                ws_clients.remove(websocket)


async def broadcast_event(event: str, data: dict):
    payload = json.dumps({"event": event, "data": data})
    to_remove = []
    with ws_lock:
        clients = list(ws_clients)
    for ws in clients:
        try:
            await ws.send(payload)
        except Exception:
            to_remove.append(ws)
    if to_remove:
        with ws_lock:
            for w in to_remove:
                if w in ws_clients:
                    ws_clients.remove(w)


def start_ws_server(host="0.0.0.0", port=8765):
    global ws_loop
    ws_loop = asyncio.new_event_loop()

    async def _run():
        server = await websockets.serve(ws_handler, host, port)
        print(f"WebSocket server started on ws://{host}:{port}")
        await server.wait_closed()

    def _loop():
        asyncio.set_event_loop(ws_loop)
        ws_loop.run_until_complete(_run())

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


# -----------------------
# Flask REST API
# -----------------------
app = Flask(__name__)
CORS(app)


@app.route("/api/subscribe/connect", methods=["POST"])
def api_connect():
    payload = request.get_json() or {}
    broker = payload.get("broker", DEFAULT_BROKER)
    port = int(payload.get("port", DEFAULT_PORT))
    topic = payload.get("topic", DEFAULT_TOPIC)
    username = payload.get("username")
    password = payload.get("password")

    mqtt_status.update({"topic": topic})
    ok, msg = connect_mqtt(broker, port, topic, username, password)
    status_code = 200 if ok else 500
    return jsonify({"ok": ok, "msg": msg, "status": mqtt_status}), status_code


@app.route("/api/subscribe/disconnect", methods=["POST"])
def api_disconnect():
    ok, msg = disconnect_mqtt()
    status_code = 200 if ok else 500
    return jsonify({"ok": ok, "msg": msg, "status": mqtt_status}), status_code


@app.route("/api/subscribe/status", methods=["GET"])
def api_status():
    return jsonify(mqtt_status)


@app.route("/api/subscribe/history", methods=["GET"])
def api_history():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except Exception:
        page = 1
        per_page = 20

    results = []
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # newest last; return descending by file order
                rows = rows[::-1]
                start = (page - 1) * per_page
                end = start + per_page
                for r in rows[start:end]:
                    # parse numeric fields when possible
                    try:
                        r_parsed = {
                            "timestamp": r.get("timestamp"),
                            "temperature": float(r.get("temperature")) if r.get("temperature") else None,
                            "humidity": float(r.get("humidity")) if r.get("humidity") else None,
                            "pressure": float(r.get("pressure")) if r.get("pressure") else None,
                            "raw": r.get("raw"),
                        }
                    except Exception:
                        r_parsed = r
                    results.append(r_parsed)
        except Exception as e:
            return jsonify({"ok": False, "msg": str(e)}), 500

    return jsonify({"ok": True, "page": page, "per_page": per_page, "data": results})


# -----------------------
# Entrypoint
# -----------------------
def ensure_csv_header():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


if __name__ == "__main__":
    ensure_csv_header()
    start_ws_server(host="0.0.0.0", port=8765)
    # Start Flask on a different port (5001)
    app.run(host="0.0.0.0", port=5001, debug=True)
