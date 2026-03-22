import json
import os
import time
from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from flask_sock import Sock

app = Flask(__name__)
CORS(app, origins=["http://localhost:6060"])
sock = Sock(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "slimes.json")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

DEFAULT_PARAMS = {
    "slime": {
        "grid_width":         500,
        "grid_height":        500,
        "display_size":       800,
        "n_agents":           30000,
        "n_species":          1,
        "sensor_distance":    9.0,
        "sensor_size":        5,
        "sensor_angle":       45.0,
        "turn_speed":         9.0,
        "diffusion_speed":    0.2,
        "evaporation_speed":  2.0,
        "deposit_amount":     255.0,
    },
    "boids": {
        "num_boids": 200,
        "max_speed": 4.0,
        "min_speed": 1.0,
        "perception_radius": 60.0,
        "separation_radius": 20.0,
        "alignment_weight": 1.0,
        "cohesion_weight": 1.0,
        "separation_weight": 1.5,
        "width": 800,
        "height": 600,
    },
    "cells": {
        "grid_width": 120,
        "grid_height": 90,
        "birth_min": 3,
        "birth_max": 3,
        "survival_min": 2,
        "survival_max": 3,
        "initial_density": 0.3,
    },
    "fluid": {
        "grid_width": 320,
        "grid_height": 240,
        "cell_size": 3,
        "dt": 0.04,
        "viscosity": 0.000008,
        "diffusion": 0.000001,
        "project_iters": 20,
        "mouse_force": 60.0,
        "dye_amount": 1.2,
        "brush_size": 14,
        "swirl_strength": 0.010,
        "decay": 0.993,
        "source_strength": 0.06,
        "theme": 0,
        "color_change": 0,
        "color_speed": 180,
    },
}

VALID_TYPES = set(DEFAULT_PARAMS.keys())


def load_sims():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save_sims(sims):
    with open(DATA_FILE, "w") as f:
        json.dump(sims, f, indent=2)


@app.route("/api/params/defaults", methods=["GET"])
def get_defaults():
    return jsonify(DEFAULT_PARAMS)


@app.route("/api/slimes", methods=["GET"])
def list_sims():
    return jsonify(load_sims())


@app.route("/api/slimes", methods=["POST"])
def create_sim():
    body = request.json or {}
    sim_type = body.get("type", "slime")
    if sim_type not in VALID_TYPES:
        return jsonify({"error": "Invalid type"}), 400
    sims = load_sims()
    defaults = DEFAULT_PARAMS[sim_type]
    sim = {
        "id": str(int(time.time() * 1000)),
        "name": body.get("name", f"New {sim_type.capitalize()}"),
        "author": body.get("author", "Anonymous"),
        "type": sim_type,
        "params": {**defaults, **body.get("params", {})},
        "created_at": int(time.time()),
    }
    sims.append(sim)
    save_sims(sims)
    return jsonify(sim), 201


@app.route("/api/slimes/<sim_id>", methods=["GET"])
def get_sim(sim_id):
    sims = load_sims()
    sim = next((s for s in sims if s["id"] == sim_id), None)
    if not sim:
        return jsonify({"error": "Not found"}), 404
    return jsonify(sim)


@app.route("/api/slimes/<sim_id>", methods=["PUT"])
def update_sim(sim_id):
    body = request.json or {}
    sims = load_sims()
    sim = next((s for s in sims if s["id"] == sim_id), None)
    if not sim:
        return jsonify({"error": "Not found"}), 404
    if "name" in body:
        sim["name"] = body["name"]
    if "author" in body:
        sim["author"] = body["author"]
    if "params" in body:
        defaults = DEFAULT_PARAMS.get(sim.get("type", "slime"), {})
        sim["params"] = {**defaults, **body["params"]}
    if "preview" in body:
        sim["preview"] = body["preview"]
    save_sims(sims)
    return jsonify(sim)


@app.route("/api/simulate", methods=["POST"])
def simulate():
    body = request.json or {}
    sim_type = body.get("type", "slime")
    defaults = DEFAULT_PARAMS.get(sim_type, {})
    merged = {**defaults, **body.get("params", {}), "type": sim_type}
    # TODO: integrate with simulation backends here
    return jsonify({"status": "ok", "params": merged})


@app.route("/api/stream/<sim_id>")
def stream_sim(sim_id):
    sims = load_sims()
    sim = next((s for s in sims if s["id"] == sim_id), None)
    if not sim:
        return jsonify({"error": "Not found"}), 404

    sim_type = sim.get("type", "slime")
    params = sim.get("params", {})

    if sim_type == "fluid":
        from experiments.fluid import stream as fluid_stream
        gen = fluid_stream(sim_id, params)
    elif sim_type == "slime":
        from experiments.slimemold_stream import stream as slime_stream
        gen = slime_stream(sim_id, params)
    elif sim_type == "boids":
        from experiments.boids import stream as boids_stream
        gen = boids_stream(sim_id, params)
    else:
        return jsonify({"error": f"Streaming not yet supported for type: {sim_type}"}), 501

    def mjpeg():
        for frame_bytes in gen:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

    return Response(mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/interact/<sim_id>", methods=["POST"])
def interact(sim_id):
    body = request.json or {}
    sim_type = body.get("type", "fluid")
    if sim_type == "fluid":
        from experiments.fluid import set_mouse_state
        set_mouse_state(
            sim_id,
            int(body.get("r", 0)),
            int(body.get("c", 0)),
            bool(body.get("drawing", False)),
        )
    return jsonify({"ok": True})


@sock.route("/ws/interact/<sim_id>")
def ws_interact(ws, sim_id):
    from experiments.fluid import set_mouse_state, clear_mouse_state
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            body = json.loads(data)
            set_mouse_state(
                sim_id,
                int(body.get("r", 0)),
                int(body.get("c", 0)),
                bool(body.get("drawing", False)),
            )
    finally:
        clear_mouse_state(sim_id)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_spa(path):
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    app.run(port=7070, debug=True, threaded=True)
