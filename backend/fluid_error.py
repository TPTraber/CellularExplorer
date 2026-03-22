"""
2D fluid simulation (Jos Stam stable fluids).
Rendered with a colormap. Call run(params) or run directly.
"""

import numpy as np
import cv2
from scipy.ndimage import map_coordinates, gaussian_filter

DEFAULT_PARAMS = {
    "grid_width":    320,
    "grid_height":   240,
    "cell_size":     3,
    "dt":            0.1,
    "viscosity":     0.0001,
    "diffusion":     0.0001,
    "project_iters": 20,
    "mouse_force":   80.0,
    "dye_amount":    1.0,
    "brush_size":    10,
}


# -- Fluid math ----------------------------------------------------

def diffuse(field, rate, dt):
    sigma = np.sqrt(rate * dt) * max(field.shape)
    if sigma < 0.001:
        return field
    return gaussian_filter(field, sigma=sigma, mode="wrap")


def advect(field, u, v, dt):
    rows, cols = field.shape
    r_idx, c_idx = np.mgrid[0:rows, 0:cols].astype(np.float32)
    src_r = r_idx - v * dt * rows
    src_c = c_idx - u * dt * cols
    return map_coordinates(field, [src_r, src_c], order=1, mode="wrap")


def project(u, v, iters):
    rows, cols = u.shape
    h = 1.0 / max(rows, cols)
    div = -0.5 * h * (
        np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1) +
        np.roll(v, -1, axis=0) - np.roll(v, 1, axis=0)
    )
    p = np.zeros_like(div)
    for _ in range(iters):
        p = (div +
             np.roll(p,  1, axis=1) + np.roll(p, -1, axis=1) +
             np.roll(p,  1, axis=0) + np.roll(p, -1, axis=0)) * 0.25
    u -= 0.5 * (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1)) / h
    v -= 0.5 * (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)) / h
    return u, v


def step(u, v, dye, p):
    dt    = p["dt"]
    visc  = p["viscosity"]
    diff  = p["diffusion"]
    iters = p["project_iters"]

    u = diffuse(u, visc, dt)
    v = diffuse(v, visc, dt)
    u, v = project(u, v, iters)
    u = advect(u, u, v, dt)
    v = advect(v, u, v, dt)
    u, v = project(u, v, iters)

    dye = diffuse(dye, diff, dt)
    dye = advect(dye, u, v, dt)
    np.clip(dye, 0.0, 1.0, out=dye)
    return u, v, dye


# -- Rendering -----------------------------------------------------

def render(dye, u, v, cell_size):
    speed = np.sqrt(u**2 + v**2)
    speed_norm = np.clip(speed / speed.max(), 0.0, 1.0) if speed.max() > 0 else speed
    combined = np.clip(dye * 6 + speed_norm * 0.5, 0.0, 1.0)
    gray = (combined * 255).astype(np.uint8)
    colored = cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
    if cell_size > 1:
        colored = colored.repeat(cell_size, axis=0).repeat(cell_size, axis=1)
    return colored


# -- Mouse state ---------------------------------------------------

_mouse: dict = {}


def set_mouse_state(sim_id, r, c, drawing):
    prev = _mouse.get(sim_id, {})
    _mouse[sim_id] = {
        "r": r, "c": c,
        "pr": prev.get("r", r), "pc": prev.get("c", c),
        "drawing": drawing,
    }


def clear_mouse_state(sim_id):
    _mouse.pop(sim_id, None)


# -- Headless stream -----------------------------------------------

def stream(sim_id, params=None):
    import time
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows  = int(p["grid_height"])
    cols  = int(p["grid_width"])
    cs    = int(p["cell_size"])
    force = float(p["mouse_force"])
    damt  = float(p["dye_amount"])
    brad  = int(p["brush_size"])

    rng = np.random.default_rng()
    u   = np.zeros((rows, cols), dtype=np.float32)
    v   = np.zeros((rows, cols), dtype=np.float32)
    dye = np.zeros((rows, cols), dtype=np.float32)
    frame_count = 0

    try:
        while True:
            # auto-inject: random burst every 30 frames
            if frame_count % 30 == 0:
                cr = int(rng.integers(rows // 4, 3 * rows // 4))
                cc = int(rng.integers(cols // 4, 3 * cols // 4))
                angle = rng.uniform(0, 2 * np.pi)
                u[cr, cc] += np.cos(angle) * force * 2
                v[cr, cc] += np.sin(angle) * force * 2
                dye[cr, cc] = 1.0

            ms = _mouse.get(sim_id)
            if ms and ms["drawing"]:
                cr, cc = ms["r"], ms["c"]
                pr, pc = ms["pr"], ms["pc"]
                dr = int(np.clip(cr - pr, -15, 15))
                dc = int(np.clip(cc - pc, -15, 15))
                u[cr, cc] += dc * force * p["dt"]
                v[cr, cc] += dr * force * p["dt"]
                dye[cr, cc] = min(1.0, dye[cr, cc] + damt)

            u, v, dye = step(u, v, dye, p)

            frame = render(dye, u, v, cs)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ok:
                yield buf.tobytes()

            frame_count += 1
            time.sleep(1 / 60)
    finally:
        clear_mouse_state(sim_id)


# -- Standalone run ------------------------------------------------

def run(params=None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows  = int(p["grid_height"])
    cols  = int(p["grid_width"])
    cs    = int(p["cell_size"])
    force = float(p["mouse_force"])
    damt  = float(p["dye_amount"])

    rng = np.random.default_rng()
    u   = np.zeros((rows, cols), dtype=np.float32)
    v   = np.zeros((rows, cols), dtype=np.float32)
    dye = np.zeros((rows, cols), dtype=np.float32)
    frame_count = 0

    mouse_pos  = None
    mouse_prev = None
    drawing    = False

    win = "Fluid Simulation"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)

    def on_mouse(event, x, y, flags, _):
        nonlocal drawing, mouse_pos, mouse_prev
        cr = int(np.clip(y // cs, 0, rows - 1))
        cc = int(np.clip(x // cs, 0, cols - 1))
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            mouse_prev = (cr, cc)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            mouse_prev = None
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            mouse_pos = (cr, cc)

    cv2.setMouseCallback(win, on_mouse)
    print("Controls: left drag=inject  R=reset  ESC/Q=quit")

    while True:
        if frame_count % 30 == 0:
            cr = int(rng.integers(rows // 4, 3 * rows // 4))
            cc = int(rng.integers(cols // 4, 3 * cols // 4))
            angle = rng.uniform(0, 2 * np.pi)
            u[cr, cc] += np.cos(angle) * force * 2
            v[cr, cc] += np.sin(angle) * force * 2
            dye[cr, cc] = 1.0

        if drawing and mouse_pos and mouse_prev:
            cr, cc = mouse_pos
            pr, pc = mouse_prev
            dr = np.clip(cr - pr, -15, 15)
            dc = np.clip(cc - pc, -15, 15)
            u[cr, cc] += dc * force * p["dt"]
            v[cr, cc] += dr * force * p["dt"]
            dye[cr, cc] = min(1.0, dye[cr, cc] + damt)
            mouse_prev = mouse_pos

        u, v, dye = step(u, v, dye, p)

        frame = render(dye, u, v, cs)
        frame_count += 1
        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            u[:] = 0; v[:] = 0; dye[:] = 0

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
