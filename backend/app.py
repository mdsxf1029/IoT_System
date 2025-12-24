from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

app = Flask(__name__)
CORS(app)


@app.route('/ping')
def ping():
    return jsonify({"msg": "backend ok"})


if __name__ == '__main__':
    app.run(host=Config.ANALYSIS_SERVICE_HOST, port=3000, debug=True)
