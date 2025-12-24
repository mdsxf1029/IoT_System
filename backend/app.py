from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from publish import publish_bp
from data_address import data_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*",
     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

app.register_blueprint(publish_bp)
app.register_blueprint(data_bp)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # 允许所有来源
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.route('/ping')
def ping():
    return jsonify({"msg": "backend ok"})


if __name__ == '__main__':
    app.run(host=Config.PUBLISH_SERVICE_HOST,
            port=Config.PUBLISH_SERVICE_PORT, debug=True, threaded=True)
