"""
Physarum polycephalum (slime mold) simulation.
Agents spawn in a circle facing inward, sense trail pheromones, and steer.
Supports 1-3 species with mutual repulsion.
Call stream(sim_id, params) or run() directly.
"""

import math
import time
import numpy as np
import cv2

DEFAULT_PARAMS = {
    "grid_width":         800,
    "grid_height":        800,
    "display_size":       800,
    "n_agents":           10000,
    "n_species":          1,
    "sensor_distance":    3.0,
    "sensor_size":        3,
    "sensor_angle":       45.0,   # degrees
    "turn_speed":         12.0,   # degrees (pi/15 ~ 12)
    "diffusion_speed":    0.3,
    "evaporation_speed":  4.0,
    "deposit_amount":     255.0,
}

SPECIES_COLORS = [
    (255, 255, 255),   # white
    (255, 255,   0),   # yellow
    (255,   0, 255),   # magenta
]


# -- Core functions ------------------------------------------------

def _make_agents(rng, n_agents, n_species, rows, cols):
    agents = np.zeros((n_agents, 4), dtype=np.float32)
    center_y, center_x = rows / 2, cols / 2
    max_radius = min(rows, cols) * 0.2

    r     = max_radius * np.sqrt(rng.random(n_agents))
    theta = rng.random(n_agents) * 2 * math.pi

    agents[:, 0] = center_y + r * np.sin(theta)
    agents[:, 1] = center_x + r * np.cos(theta)
    agents[:, 2] = np.arctan2(center_y - agents[:, 0], center_x - agents[:, 1])
    agents[:, 3] = rng.integers(0, n_species, size=n_agents)
    return agents


def _sense(agents, angles, kernel_sum, sensor_distance, rows, cols):
    pos = agents[:, :2].copy()
    pos[:, 0] = np.clip(pos[:, 0] + np.sin(angles) * sensor_distance, 0, rows - 1)
    pos[:, 1] = np.clip(pos[:, 1] + np.cos(angles) * sensor_distance, 0, cols - 1)
    pos = pos.astype(np.uint32)
    return kernel_sum[pos[:, 0], pos[:, 1]]


def _update_agents(agents, trails, p, rows, cols, rng):
    n_species   = int(p["n_species"])
    sensor_dist = float(p["sensor_distance"])
    sensor_size = int(p["sensor_size"])
    angle_sp    = math.radians(float(p["sensor_angle"]))
    turn_sp     = math.radians(float(p["turn_speed"]))
    n_ag        = len(agents)

    kernel_sums = cv2.blur(trails, (sensor_size, sensor_size))
    if kernel_sums.ndim == 2:
        kernel_sums = kernel_sums.reshape((*kernel_sums.shape, 1))

    total = np.sum(kernel_sums, axis=-1)

    for i in range(n_species):
        species_mask  = agents[:, 3] == i
        agents_masked = agents[species_mask]
        angles_masked = agents_masked[:, 2]

        own        = kernel_sums[..., i]
        kernel_sum = own - (total - own)

        wf = _sense(agents_masked, angles_masked,            kernel_sum, sensor_dist, rows, cols)
        wl = _sense(agents_masked, angles_masked - angle_sp, kernel_sum, sensor_dist, rows, cols)
        wr = _sense(agents_masked, angles_masked + angle_sp, kernel_sum, sensor_dist, rows, cols)

        rand_m  = (wf < wl) & (wf < wr)
        left_m  = (wl > wf) & (wl > wr)
        right_m = (wr > wf) & (wr > wl)

        angles_masked[rand_m]  += (rng.random(np.sum(rand_m))  - 0.5)
        angles_masked[left_m]  -= turn_sp * rng.random(np.sum(left_m))
        angles_masked[right_m] += turn_sp * rng.random(np.sum(right_m))

        agents[species_mask, 2] = angles_masked

    angles = agents[:, 2]
    agents[:, 0] += np.sin(angles)
    agents[:, 1] += np.cos(angles)

    agents_alt = np.zeros_like(agents)
    agents_alt[:, 0] = np.clip(agents[:, 0], 0, rows - 1)
    agents_alt[:, 1] = np.clip(agents[:, 1], 0, cols - 1)
    agents_alt[:, 2] = rng.random(n_ag, dtype=np.float32) * 2 * math.pi
    agents_alt[:, 3] = agents[:, 3]

    in_bounds = (
        (0 <= agents[:, 0]) & (agents[:, 0] <= rows - 1) &
        (0 <= agents[:, 1]) & (agents[:, 1] <= cols - 1)
    ).reshape(-1, 1)
    agents = np.where(in_bounds, agents, agents_alt)

    return agents


def _update_trails(agents_int, trails, p):
    diffusion_speed = float(p["diffusion_speed"])
    evaporation     = float(p["evaporation_speed"])
    deposit         = float(p["deposit_amount"])
    n_species       = int(p["n_species"])

    diffused = cv2.blur(trails, (3, 3)).astype(np.uint8)
    if diffused.ndim == 2:
        diffused = diffused.reshape((*diffused.shape, 1))

    trails = (1 - diffusion_speed) * trails + diffusion_speed * diffused

    mask = trails >= evaporation
    trails[mask] -= evaporation
    trails[~mask] = 0

    for i in range(n_species):
        sp = agents_int[np.where(agents_int[:, 3] == i)]
        trails[sp[:, 0], sp[:, 1], i] = deposit

    return trails


def _render(agents_int, trails, display_size, n_species):
    h, w = trails.shape[:2]
    grid  = np.zeros((h, w, 3), dtype=np.float32)
    total = np.sum(trails, axis=-1, keepdims=True)
    display_trails = np.maximum(0, 2 * trails - total)

    for i in range(n_species):
        color = np.array(SPECIES_COLORS[i % len(SPECIES_COLORS)], dtype=np.float32) / 255.0
        grid += display_trails[..., i:i+1] * color

    grid = np.clip(grid, 0, 255).astype(np.uint8)

    for i in range(n_species):
        sp = agents_int[agents_int[:, 3] == i]
        if len(sp):
            grid[sp[:, 0], sp[:, 1]] = SPECIES_COLORS[i % len(SPECIES_COLORS)]

    if display_size != h or display_size != w:
        grid = cv2.resize(grid, (display_size, display_size), interpolation=cv2.INTER_LINEAR)
    return grid


# -- Headless stream -----------------------------------------------

def stream(sim_id: str, params=None):
    p    = {**DEFAULT_PARAMS, **(params or {})}
    rows = int(p["grid_height"])
    cols = int(p["grid_width"])
    disp = int(p["display_size"])
    n_ag = int(p["n_agents"])
    n_sp = max(1, min(int(p["n_species"]), len(SPECIES_COLORS)))
    p["n_species"] = n_sp

    rng    = np.random.default_rng()
    agents = _make_agents(rng, n_ag, n_sp, rows, cols)
    trails = np.zeros((rows, cols, n_sp), dtype=np.float32)

    try:
        while True:
            agents     = _update_agents(agents, trails, p, rows, cols, rng)
            agents_int = agents.astype(np.uint32)
            trails     = _update_trails(agents_int, trails, p)
            frame      = _render(agents_int, trails, disp, n_sp)
            ok, buf    = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / 30)
    finally:
        pass


# -- Standalone run ------------------------------------------------

def run(params=None):
    p    = {**DEFAULT_PARAMS, **(params or {})}
    rows = int(p["grid_height"])
    cols = int(p["grid_width"])
    disp = int(p["display_size"])
    n_ag = int(p["n_agents"])
    n_sp = max(1, min(int(p["n_species"]), len(SPECIES_COLORS)))
    p["n_species"] = n_sp

    rng    = np.random.default_rng()
    agents = _make_agents(rng, n_ag, n_sp, rows, cols)
    trails = np.zeros((rows, cols, n_sp), dtype=np.float32)

    win = "Cellular Simulations - Slime Mold"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    print("Controls: R=reset  ESC/Q=quit")

    while True:
        agents     = _update_agents(agents, trails, p, rows, cols, rng)
        agents_int = agents.astype(np.uint32)
        trails     = _update_trails(agents_int, trails, p)
        frame      = _render(agents_int, trails, disp, n_sp)
        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            agents = _make_agents(rng, n_ag, n_sp, rows, cols)
            trails = np.zeros((rows, cols, n_sp), dtype=np.float32)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
