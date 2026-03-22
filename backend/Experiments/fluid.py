"""
2D fluid simulation (Jos Stam stable fluids).
Rendered with one of 4 colormaps. color_change ping-pongs through them.
Call run(params) or run directly.
"""

import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

DEFAULT_PARAMS = {
    "grid_width":       320,
    "grid_height":      240,
    "cell_size":        3,
    "dt":               0.04,
    "viscosity":        0.000008,
    "diffusion":        0.000001,
    "project_iters":    12,
    "mouse_force":      60.0,
    "dye_amount":       1.2,
    "brush_size":       14,
    "swirl_strength":   0.010,
    "decay":            0.993,
    "source_strength":  0.06,
    "theme":            0,
    "color_change":     0,
    "color_speed":      180,
}

THEMES = [
    cv2.COLORMAP_TURBO,
    cv2.COLORMAP_OCEAN,
    cv2.COLORMAP_HOT,
    cv2.COLORMAP_MAGMA,
    cv2.COLORMAP_VIRIDIS,
]
THEME_NAMES = ["turbo", "ocean", "inferno", "magma", "viridis"]

# Diffusion skip threshold -- default viscosity/diffusion produce sigma ~0.18
# which changes almost nothing; raise threshold to skip those passes entirely.
_DIFF_SKIP_SIGMA = 0.5


# -- Fluid math ----------------------------------------------------

def diffuse(field: np.ndarray, rate: float, dt: float) -> np.ndarray:
    sigma = np.sqrt(rate * dt) * max(field.shape)
    if sigma < _DIFF_SKIP_SIGMA:
        return field
    return gaussian_filter(field, sigma=sigma, mode="wrap")


def advect(field: np.ndarray, u: np.ndarray, v: np.ndarray, dt: float,
           r_idx: np.ndarray, c_idx: np.ndarray) -> np.ndarray:
    """Advect field using cv2.remap (faster than scipy map_coordinates)."""
    rows, cols = field.shape
    src_c = (c_idx - u * dt * cols).astype(np.float32) % cols
    src_r = (r_idx - v * dt * rows).astype(np.float32) % rows
    return cv2.remap(field, src_c, src_r, interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_WRAP)


def project(u: np.ndarray, v: np.ndarray, iters: int):
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


def make_swirl(rows, cols, strength):
    r_idx, c_idx = np.mgrid[0:rows, 0:cols].astype(np.float32)
    cy, cx = rows / 2.0, cols / 2.0
    dy = r_idx - cy
    dx = c_idx - cx
    dist = np.sqrt(dx*dx + dy*dy) + 1e-6
    su = -dy / dist * strength
    sv =  dx / dist * strength
    return su.astype(np.float32), sv.astype(np.float32)


def make_sources(rows, cols, n=5, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    margin = rows // 6
    rs = rng.integers(margin, rows - margin, size=n)
    cs = rng.integers(cols // 6, cols - cols // 6, size=n)
    return list(zip(rs.tolist(), cs.tolist()))


def precompute_source_kernels(sources, radius, rows, cols):
    """Precompute gaussian kernels for each source point once at startup."""
    kernels = []
    for (sr, sc) in sources:
        r0, r1 = max(0, sr - radius), min(rows, sr + radius + 1)
        c0, c1 = max(0, sc - radius), min(cols, sc + radius + 1)
        rr, cc = np.ogrid[r0:r1, c0:c1]
        k = np.exp(-((rr-sr)**2 + (cc-sc)**2) / (2*(radius*0.6)**2)).astype(np.float32)
        kernels.append((r0, r1, c0, c1, k))
    return kernels


def apply_sources(dye, source_kernels, strength):
    for (r0, r1, c0, c1, k) in source_kernels:
        dye[r0:r1, c0:c1] = np.minimum(1.0, dye[r0:r1, c0:c1] + k * strength)


def step(u, v, dye, swirl_u, swirl_v, source_kernels, p, r_idx, c_idx):
    dt    = p["dt"]
    visc  = p["viscosity"]
    diff  = p["diffusion"]
    iters = p["project_iters"]

    u = u + swirl_u
    v = v + swirl_v
    u = diffuse(u, visc, dt)
    v = diffuse(v, visc, dt)
    u, v = project(u, v, iters)
    u = advect(u, u, v, dt, r_idx, c_idx)
    v = advect(v, u, v, dt, r_idx, c_idx)

    dye = diffuse(dye, diff, dt)
    dye = advect(dye, u, v, dt, r_idx, c_idx)
    dye *= p["decay"]
    apply_sources(dye, source_kernels, p["source_strength"])
    np.clip(dye, 0.0, 1.0, out=dye)
    return u, v, dye


# -- Rendering -----------------------------------------------------

def render(dye: np.ndarray, cell_size: int, theme_idx: int) -> np.ndarray:
    smooth = cv2.GaussianBlur(dye, (0, 0), sigmaX=1.4)
    soft   = np.power(np.clip(smooth, 0.0, 1.0), 0.6).astype(np.float32)
    gray   = (soft * 255).astype(np.uint8)
    colored = cv2.applyColorMap(gray, THEMES[theme_idx % len(THEMES)])
    if cell_size > 1:
        h, w = colored.shape[:2]
        colored = cv2.resize(colored, (w * cell_size, h * cell_size),
                             interpolation=cv2.INTER_CUBIC)
    return colored


# -- Brush ---------------------------------------------------------

def gaussian_brush(field, cr, cc, radius, amount, rows, cols):
    r0, r1 = max(0, cr - radius), min(rows, cr + radius + 1)
    c0, c1 = max(0, cc - radius), min(cols, cc + radius + 1)
    if r0 >= r1 or c0 >= c1:
        return
    rr, cc_ = np.ogrid[r0:r1, c0:c1]
    kernel = np.exp(-((rr-cr)**2 + (cc_-cc)**2) / (2*(radius*0.65)**2)).astype(np.float32)
    field[r0:r1, c0:c1] = np.minimum(1.0, field[r0:r1, c0:c1] + kernel * amount)


# -- Mouse state ---------------------------------------------------

_mouse: dict = {}


def set_mouse_state(sim_id: str, r: int, c: int, drawing: bool):
    prev = _mouse.get(sim_id, {})
    _mouse[sim_id] = {
        "r": r, "c": c,
        "pr": prev.get("r", r), "pc": prev.get("c", c),
        "drawing": drawing,
    }


def clear_mouse_state(sim_id: str):
    _mouse.pop(sim_id, None)


# -- Headless stream -----------------------------------------------

def stream(sim_id: str, params=None):
    import time
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows  = int(p["grid_height"])
    cols  = int(p["grid_width"])
    cs    = int(p["cell_size"])
    force = float(p["mouse_force"])
    damt  = float(p["dye_amount"])
    brad  = int(p["brush_size"])

    theme        = int(p["theme"]) % len(THEMES)
    color_change = bool(p["color_change"])
    color_speed  = max(1, int(p["color_speed"]))
    theme_dir    = 1
    frame_count  = 0

    rng = np.random.default_rng()
    u   = np.zeros((rows, cols), dtype=np.float32)
    v   = np.zeros((rows, cols), dtype=np.float32)
    dye = np.zeros((rows, cols), dtype=np.float32)

    # Precompute coordinate grids and source kernels
    r_idx, c_idx = np.mgrid[0:rows, 0:cols].astype(np.float32)
    swirl_u, swirl_v = make_swirl(rows, cols, float(p["swirl_strength"]))
    sources = make_sources(rows, cols, n=5, rng=rng)
    source_kernels = precompute_source_kernels(sources, radius=16, rows=rows, cols=cols)

    try:
        while True:
            ms = _mouse.get(sim_id)
            if ms and ms["drawing"]:
                cr, cc = ms["r"], ms["c"]
                pr, pc = ms["pr"], ms["pc"]
                dr = int(np.clip(cr - pr, -15, 15))
                dc = int(np.clip(cc - pc, -15, 15))
                r0, r1 = max(0, cr - brad), min(rows, cr + brad + 1)
                c0, c1 = max(0, cc - brad), min(cols, cc + brad + 1)
                if r0 < r1 and c0 < c1:
                    rr, cc_ = np.ogrid[r0:r1, c0:c1]
                    kernel = np.exp(-((rr-cr)**2 + (cc_-cc)**2) /
                                    (2*(brad*0.65)**2)).astype(np.float32)
                    u[r0:r1, c0:c1] += kernel * dc * force * p["dt"]
                    v[r0:r1, c0:c1] += kernel * dr * force * p["dt"]
                gaussian_brush(dye, cr, cc, brad, damt, rows, cols)

            u, v, dye = step(u, v, dye, swirl_u, swirl_v, source_kernels, p, r_idx, c_idx)

            if color_change and frame_count > 0 and frame_count % color_speed == 0:
                theme += theme_dir
                if theme >= len(THEMES) - 1:
                    theme_dir = -1
                elif theme <= 0:
                    theme_dir = 1

            frame = render(dye, cs, theme)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                yield buf.tobytes()

            frame_count += 1
            time.sleep(1 / 30)
    finally:
        clear_mouse_state(sim_id)


# -- Standalone run ------------------------------------------------

def run(params: dict = None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows  = int(p["grid_height"])
    cols  = int(p["grid_width"])
    cs    = int(p["cell_size"])
    force = float(p["mouse_force"])
    damt  = float(p["dye_amount"])
    brad  = int(p["brush_size"])

    theme        = int(p["theme"]) % len(THEMES)
    color_change = bool(p["color_change"])
    color_speed  = max(1, int(p["color_speed"]))
    theme_dir    = 1
    frame_count  = 0

    rng = np.random.default_rng()
    u   = np.zeros((rows, cols), dtype=np.float32)
    v   = np.zeros((rows, cols), dtype=np.float32)
    dye = np.zeros((rows, cols), dtype=np.float32)

    r_idx, c_idx = np.mgrid[0:rows, 0:cols].astype(np.float32)
    swirl_u, swirl_v = make_swirl(rows, cols, float(p["swirl_strength"]))
    sources = make_sources(rows, cols, n=5, rng=rng)
    source_kernels = precompute_source_kernels(sources, radius=16, rows=rows, cols=cols)

    mouse_pos  = None
    mouse_prev = None
    drawing    = False

    win = "Cellular Simulations - Fluid"
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
        if drawing and mouse_pos and mouse_prev:
            cr, cc = mouse_pos
            pr, pc = mouse_prev
            dr = np.clip(cr - pr, -15, 15)
            dc = np.clip(cc - pc, -15, 15)
            r0, r1 = max(0, cr - brad), min(rows, cr + brad + 1)
            c0, c1 = max(0, cc - brad), min(cols, cc + brad + 1)
            if r0 < r1 and c0 < c1:
                rr, cc_ = np.ogrid[r0:r1, c0:c1]
                kernel = np.exp(-((rr-cr)**2 + (cc_-cc)**2) /
                                (2*(brad*0.65)**2)).astype(np.float32)
                u[r0:r1, c0:c1] += kernel * dc * force * p["dt"]
                v[r0:r1, c0:c1] += kernel * dr * force * p["dt"]
            gaussian_brush(dye, cr, cc, brad, damt, rows, cols)
            mouse_prev = mouse_pos

        u, v, dye = step(u, v, dye, swirl_u, swirl_v, source_kernels, p, r_idx, c_idx)

        if color_change and frame_count > 0 and frame_count % color_speed == 0:
            theme += theme_dir
            if theme >= len(THEMES) - 1:
                theme_dir = -1
            elif theme <= 0:
                theme_dir = 1

        frame = render(dye, cs, theme)
        frame_count += 1
        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            u[:] = 0; v[:] = 0; dye[:] = 0
            sources = make_sources(rows, cols, n=5, rng=rng)
            source_kernels = precompute_source_kernels(sources, radius=16, rows=rows, cols=cols)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
