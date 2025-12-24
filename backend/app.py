from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

app = Flask(__name__)
# 配置CORS以允许跨域请求
CORS(app, resources={r"/*": {"origins": "*",
     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})


@app.route('/ping')
def ping():
    return jsonify({"msg": "backend ok"})


if __name__ == '__main__':
    app.run(host=Config.ANALYSIS_SERVICE_HOST,
            port=Config.ANALYSIS_SERVICE_PORT, debug=True)
