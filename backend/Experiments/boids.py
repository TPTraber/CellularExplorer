"""
Boids flocking simulation (Reynolds rules: cohesion, alignment, separation).
Numpy/cv2 based so it can stream via Flask.
Call stream(sim_id, params) or run() directly.
"""

import math
import time
import numpy as np
import cv2

DEFAULT_PARAMS = {
    "num_boids":         200,
    "max_speed":         4.0,
    "min_speed":         1.0,
    "perception_radius": 60.0,
    "separation_radius": 20.0,
    "alignment_weight":  1.0,
    "cohesion_weight":   1.0,
    "separation_weight": 1.5,
    "width":             800,
    "height":            600,
}


def _init_boids(n, width, height, rng):
    pos    = (rng.random((n, 2)) * np.array([width, height])).astype(np.float32)
    angles = rng.random(n) * 2 * math.pi
    vel    = np.stack([np.cos(angles), np.sin(angles)], axis=1).astype(np.float32) * 2.0
    return pos, vel


def _step(pos, vel, p, width, height):
    max_speed = float(p["max_speed"])
    min_speed = float(p["min_speed"])
    perc_r    = float(p["perception_radius"])
    sep_r     = float(p["separation_radius"])
    aw        = float(p["alignment_weight"])
    cw        = float(p["cohesion_weight"])
    sw        = float(p["separation_weight"])

    # Pairwise distances (n, n)
    dx   = pos[:, 0:1] - pos[:, 0]   # pos[i,0] - pos[j,0]
    dy   = pos[:, 1:2] - pos[:, 1]
    dist = np.sqrt(dx * dx + dy * dy) + 1e-6

    perc_mask = (dist < perc_r) & (dist > 1e-5)
    sep_mask  = (dist < sep_r)  & (dist > 1e-5)

    perc_count = perc_mask.sum(axis=1, keepdims=True).clip(min=1).astype(np.float32)
    sep_count  = sep_mask.sum(axis=1, keepdims=True).clip(min=1).astype(np.float32)

    # Alignment: match average velocity of neighbors
    align_x = (vel[:, 0] * perc_mask).sum(axis=1, keepdims=True) / perc_count
    align_y = (vel[:, 1] * perc_mask).sum(axis=1, keepdims=True) / perc_count
    align   = np.concatenate([align_x, align_y], axis=1)

    # Cohesion: steer toward average position of neighbors
    coh_x   = (pos[:, 0] * perc_mask).sum(axis=1, keepdims=True) / perc_count
    coh_y   = (pos[:, 1] * perc_mask).sum(axis=1, keepdims=True) / perc_count
    cohesion = np.concatenate([coh_x, coh_y], axis=1) - pos

    # Separation: steer away from close neighbors
    sep_x      = (dx * sep_mask).sum(axis=1, keepdims=True) / sep_count
    sep_y      = (dy * sep_mask).sum(axis=1, keepdims=True) / sep_count
    separation = np.concatenate([sep_x, sep_y], axis=1)

    vel = vel + align * aw * 0.05 + cohesion * cw * 0.005 + separation * sw * 0.05

    # Clamp speed
    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    vel   = np.where(speed > max_speed, vel / speed * max_speed, vel)
    vel   = np.where(speed < min_speed, vel / speed * min_speed, vel)

    pos = (pos + vel) % np.array([width, height], dtype=np.float32)
    return pos, vel


def _render(frame, pos, vel):
    frame = (frame * 0.82).astype(np.uint8)
    angles = np.arctan2(vel[:, 1], vel[:, 0])
    size = 7
    for i in range(len(pos)):
        x, y = float(pos[i, 0]), float(pos[i, 1])
        a = float(angles[i])
        tip   = (int(x + math.cos(a) * size),         int(y + math.sin(a) * size))
        left  = (int(x + math.cos(a + 2.5) * size * 0.55), int(y + math.sin(a + 2.5) * size * 0.55))
        right = (int(x + math.cos(a - 2.5) * size * 0.55), int(y + math.sin(a - 2.5) * size * 0.55))
        cv2.fillPoly(frame, [np.array([tip, left, right], dtype=np.int32)], (210, 210, 210))
    return frame


# -- Headless stream -----------------------------------------------

def stream(sim_id: str, params=None):
    p      = {**DEFAULT_PARAMS, **(params or {})}
    width  = int(p["width"])
    height = int(p["height"])
    n      = int(p["num_boids"])

    rng       = np.random.default_rng()
    pos, vel  = _init_boids(n, width, height, rng)
    frame     = np.zeros((height, width, 3), dtype=np.uint8)

    try:
        while True:
            pos, vel = _step(pos, vel, p, width, height)
            frame    = _render(frame, pos, vel)
            ok, buf  = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / 30)
    finally:
        pass


# -- Standalone run ------------------------------------------------

def run(params=None):
    p      = {**DEFAULT_PARAMS, **(params or {})}
    width  = int(p["width"])
    height = int(p["height"])
    n      = int(p["num_boids"])

    rng      = np.random.default_rng()
    pos, vel = _init_boids(n, width, height, rng)
    frame    = np.zeros((height, width, 3), dtype=np.uint8)

    win = "Cellular Simulations - Boids"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    print("Controls: R=reset  ESC/Q=quit")

    while True:
        pos, vel = _step(pos, vel, p, width, height)
        frame    = _render(frame, pos, vel)
        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            pos, vel = _init_boids(n, width, height, rng)
            frame[:] = 0

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
