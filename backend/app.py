from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:6060"])

# Default simulation parameters
DEFAULT_PARAMS = {
    "num_agents": 1000,
    "sensor_angle": 45.0,
    "sensor_distance": 9.0,
    "rotation_angle": 45.0,
    "step_size": 1.0,
    "deposit_amount": 5.0,
    "decay_rate": 0.9,
    "diffuse_rate": 0.5,
    "width": 800,
    "height": 600,
}


@app.route("/api/params", methods=["GET"])
def get_params():
    return jsonify(DEFAULT_PARAMS)


@app.route("/api/simulate", methods=["POST"])
def simulate():
    params = request.json or {}
    merged = {**DEFAULT_PARAMS, **params}
    # TODO: integrate with slimemold.py simulation here
    return jsonify({"status": "ok", "params": merged})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=6000, debug=True)
