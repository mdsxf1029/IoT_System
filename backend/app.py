from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/ping')
def ping():
    return jsonify({"msg": "backend ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)