# 服务器配置文件
import os


class Config:
    # MQTT 配置
    MQTT_BROKER = os.environ.get('MQTT_BROKER', '121.43.119.155')
    MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME', 'admin')
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', 'Aaa123456')
    MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'iot/area1/environment')

    # Flask 服务配置
    PUBLISH_SERVICE_HOST = os.environ.get('PUBLISH_SERVICE_HOST', '0.0.0.0')
    PUBLISH_SERVICE_PORT = int(os.environ.get('PUBLISH_SERVICE_PORT', 5000))

    # WebSocket 配置
    WEBSOCKET_HOST = os.environ.get('WEBSOCKET_HOST', '0.0.0.0')
    WEBSOCKET_PORT = int(os.environ.get('WEBSOCKET_PORT', 8080))

    # 数据目录
    DATA_DIR = os.environ.get('DATA_DIR', '../data')
