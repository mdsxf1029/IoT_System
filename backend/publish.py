import os
import json
import time
import threading
from flask import Flask, jsonify
import paho.mqtt.client as mqtt
from flask_cors import CORS
stop_event = threading.Event()

# =========================
# Flask
# =========================
app = Flask(__name__)
CORS(app) 
publish_status = {
    "running": False,
    "count": 0,
    "total": 0,
    "error": None
}

publish_thread = None


# =========================
# MQTT 回调
# =========================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT 连接成功")
    else:
        print("MQTT 连接失败，rc =", rc)


def on_disconnect(client, userdata, rc):
    print("MQTT 连接断开，rc =", rc)


# =========================
# 读取 txt 数据
# =========================
def load_txt_data(filename):
    data = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
                for k, v in obj.items():
                    try:
                        data[k] = float(v)
                    except:
                        pass
            except:
                pass
    return data


# =========================
# 发布函数（原逻辑封装）
# =========================
def publish_data():
    global publish_status

    try:
        # ⭐ 清除停止标志
        stop_event.clear()

        # === 计算路径（标准写法）===
        DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

        temperature = load_txt_data(os.path.join(DATA_DIR, "temperature.txt"))
        humidity    = load_txt_data(os.path.join(DATA_DIR, "humidity.txt"))
        pressure    = load_txt_data(os.path.join(DATA_DIR, "pressure.txt"))
        
        timestamps = sorted(
            set(temperature.keys()) &
            set(humidity.keys()) &
            set(pressure.keys())
        )

        publish_status["total"] = len(timestamps)
        publish_status["count"] = 0
        publish_status["running"] = True
        publish_status["error"] = None

        print("可发布数据条数:", len(timestamps))

        # MQTT 参数
        BROKER_IP = "121.43.119.155"
        PORT = 1883
        USERNAME = "admin"
        PASSWORD = "Aaa123456"
        TOPIC = "iot/area1/environment"

        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        print("正在连接 MQTT 服务器...")
        client.connect(BROKER_IP, PORT, 60)

        client.loop_start()
        time.sleep(2)

        print("开始发布数据...")

        for ts in timestamps:
            # ⭐ 检测是否请求停止
            if stop_event.is_set():
                print("发布被手动停止")
                break

            msg = {
                "timestamp": ts,
                "temperature": temperature[ts],
                "humidity": humidity[ts],
                "pressure": pressure[ts],
                "temp_unit": "C",
                "humidity_unit": "RH%",
                "pressure_unit": "hPa"
            }

            result = client.publish(TOPIC, json.dumps(msg), qos=0)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                publish_status["count"] += 1
                print("已发送:", msg)
            else:
                publish_status["error"] = f"消息发送失败, ts={ts}"
                print("发送失败")

            time.sleep(1)

        client.loop_stop()
        client.disconnect()
        print("发布结束，连接已断开")

    except Exception as e:
        publish_status["error"] = str(e)

    publish_status["running"] = False


# =========================
# Flask 接口
# =========================
@app.route("/start", methods=["POST"])
def start():
    global publish_thread

    if publish_status["running"]:
        return jsonify({"msg": "already started"}), 400

    publish_thread = threading.Thread(target=publish_data)
    publish_thread.start()

    return jsonify({"msg": "started"})


@app.route("/status", methods=["GET"])
def status():
    return jsonify(publish_status)

@app.route("/stop", methods=["POST"])
def stop():
    if not publish_status["running"]:
        return jsonify({"msg": "not running"}), 400

    stop_event.set()
    return jsonify({"msg": "stopped"})


# =========================
# 启动 Flask
# =========================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
