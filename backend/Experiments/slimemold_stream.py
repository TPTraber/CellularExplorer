"""
Stream wrapper for experiments/slimemold.py.
Sets the module-level globals from params, then runs the sim loop
and yields JPEG frames instead of showing with cv2.imshow.
"""

import time
import math
import numpy as np
import cv2

import experiments.slimemold as sm

DEFAULT_PARAMS = {
    "grid_width":          800,
    "grid_height":         800,
    "display_size":        1000,
    "n_agents":            10000,
    "n_species":           1,
    "sensor_distance":     3,
    "sensor_size":         3,
    "sensor_angle":        45.0,   # degrees
    "turn_speed":          12.0,   # degrees
    "diffusion_speed":     0.3,
    "evaporation_speed":   4,
    "deposit_amount":      255,
}


def stream(sim_id: str, params=None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    n_sp   = max(1, min(int(p["n_species"]), len(sm.trail_color)))
    n_ag   = int(p["n_agents"])
    gw     = int(p["grid_width"])
    gh     = int(p["grid_height"])
    disp   = int(p["display_size"])

    # Set module globals so the original functions use our params
    sm.n_agents            = n_ag
    sm.n_species           = n_sp
    sm.gridsize            = (gh, gw, n_sp)
    sm.sensor_distance     = float(p["sensor_distance"])
    sm.sensor_size         = int(p["sensor_size"])
    sm.sensor_angle_spacing = math.radians(float(p["sensor_angle"]))
    sm.turn_speed          = math.radians(float(p["turn_speed"]))
    sm.diffusion_speed     = float(p["diffusion_speed"])
    sm.evaporation_speed   = float(p["evaporation_speed"])
    sm.rng                 = np.random.default_rng()

    agents = sm.generateAgents()
    trails = np.zeros(sm.gridsize, dtype=np.uint8)

    try:
        while True:
            agents     = sm.updateAgents(agents, trails)
            agents_int = agents.astype(np.uint32)
            trails     = sm.updateTrails(agents_int, trails)
            grid       = sm.getDisplayGrid(agents_int, trails)

            # getDisplayGrid always resizes to (1000,1000); resize to display_size if different
            if disp != 1000:
                grid = cv2.resize(grid, (disp, disp), interpolation=cv2.INTER_LINEAR)

            ok, buf = cv2.imencode('.jpg', grid, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / 30)
    finally:
        pass
