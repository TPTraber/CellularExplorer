"""
Stream wrapper for experiments/slimemold_multi_species.py.
Sets module-level globals from params, yields JPEG frames.
"""

import time
import math
import numpy as np
import cv2

import experiments.slimemold_multi_species as sm

DEFAULT_PARAMS = {
    "grid_width":        600,
    "grid_height":       600,
    "display_size":      800,
    "n_agents":          10000,
    "n_species":         1,
    "sensor_distance":   3,
    "sensor_size":       3,
    "sensor_angle":      45.0,
    "turn_speed":        12.0,
    "diffusion_speed":   0.3,
    "evaporation_speed": 4,
    "color_0":           "#00ffff",
    "color_1":           "#ff00ff",
    "color_2":           "#0000ff",
}


def _hex_to_bgr(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


def stream(sim_id: str, params=None):
    p    = {**DEFAULT_PARAMS, **(params or {})}
    n_sp = max(1, min(int(p["n_species"]), 3))
    n_ag = int(p["n_agents"])
    gw   = int(p["grid_width"])
    gh   = int(p["grid_height"])
    disp = int(p["display_size"])

    sm.n_agents             = n_ag
    sm.n_species            = n_sp
    sm.gridsize             = (gh, gw, n_sp)
    sm.sensor_distance      = float(p["sensor_distance"])
    sm.sensor_size          = int(p["sensor_size"])
    sm.sensor_angle_spacing = math.radians(float(p["sensor_angle"]))
    sm.turn_speed           = math.radians(float(p["turn_speed"]))
    sm.diffusion_speed      = float(p["diffusion_speed"])
    sm.evaporation_speed    = float(p["evaporation_speed"])
    sm.rng                  = np.random.default_rng()
    sm.trail_color          = [
        _hex_to_bgr(p["color_0"]),
        _hex_to_bgr(p["color_1"]),
        _hex_to_bgr(p["color_2"]),
    ]

    agents = sm.generateAgents()
    trails = np.zeros(sm.gridsize, dtype=np.uint8)

    try:
        while True:
            agents     = sm.updateAgents(agents, trails)
            agents_int = agents.astype(np.uint32)
            trails     = sm.updateTrails(agents_int, trails)
            grid       = sm.getDisplayGrid(agents_int, trails)

            # getDisplayGrid resizes to (800,800); resize further if display_size differs
            if disp != 800:
                grid = cv2.resize(grid, (disp, disp), interpolation=cv2.INTER_LINEAR)

            ok, buf = cv2.imencode('.jpg', grid, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / 30)
    finally:
        pass
