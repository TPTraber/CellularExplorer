"""
Reaction-diffusion simulation (Gray-Scott model).
Renders with OpenCV. Fully numpy-vectorized, no per-cell Python loops.
Call run(params) or run directly.
"""

import numpy as np
import cv2

# ── Presets (f=feed, k=kill) ──────────────────────────────
PRESETS = {
    "coral":    {"f": 0.0545, "k": 0.062},
    "spots":    {"f": 0.035,  "k": 0.065},
    "stripes":  {"f": 0.060,  "k": 0.062},
    "mitosis":  {"f": 0.0367, "k": 0.0649},
    "worms":    {"f": 0.078,  "k": 0.061},
    "mazes":    {"f": 0.029,  "k": 0.057},
}
PRESET_NAMES = list(PRESETS.keys())

DEFAULT_PARAMS = {
    "grid_width":    300,
    "grid_height":   220,
    "cell_size":     3,
    "du":            0.2097,   # diffusion rate U
    "dv":            0.1050,   # diffusion rate V
    "f":             0.0545,   # feed rate  (coral default)
    "k":             0.062,    # kill rate
    "steps_per_frame": 8,      # simulation steps per rendered frame
    "brush_size":    6,        # seed radius in cells
    "colormap":      3,        # OpenCV colormap index (3=MAGMA-like via BONE, try 2,11,17,21)
    "autoseed_interval": 90,   # frames between automatic re-seeds (0 to disable)
    "autoseed_count":    3,    # number of spots dropped each autoseed
}

# Nice colormaps: COLORMAP_INFERNO=9, COLORMAP_MAGMA (not built-in, use TURBO=21 or HOT=11)
COLORMAPS = [
    cv2.COLORMAP_BONE,
    cv2.COLORMAP_INFERNO,
    cv2.COLORMAP_HOT,
    cv2.COLORMAP_OCEAN,
    cv2.COLORMAP_TURBO,
    cv2.COLORMAP_PLASMA,
]
COLORMAP_NAMES = ["bone", "inferno", "hot", "ocean", "turbo", "plasma"]


# ── Core math ─────────────────────────────────────────────

def laplacian(Z: np.ndarray) -> np.ndarray:
    """5-point stencil laplacian with wrap-around edges."""
    return (
        np.roll(Z,  1, axis=0) +
        np.roll(Z, -1, axis=0) +
        np.roll(Z,  1, axis=1) +
        np.roll(Z, -1, axis=1) -
        4.0 * Z
    )


def step(U: np.ndarray, V: np.ndarray, p: dict) -> tuple:
    du, dv = p["du"], p["dv"]
    f,  k  = p["f"],  p["k"]

    uvv = U * V * V
    U2 = U + du * laplacian(U) - uvv + f * (1.0 - U)
    V2 = V + dv * laplacian(V) + uvv - (f + k) * V

    np.clip(U2, 0.0, 1.0, out=U2)
    np.clip(V2, 0.0, 1.0, out=V2)
    return U2, V2


# ── Init ──────────────────────────────────────────────────

def init_grid(rows: int, cols: int) -> tuple:
    U = np.ones((rows, cols), dtype=np.float32)
    V = np.zeros((rows, cols), dtype=np.float32)
    # Seed a few random squares to kick off the reaction
    rng = np.random.default_rng()
    for _ in range(12):
        r = rng.integers(10, rows - 10)
        c = rng.integers(10, cols - 10)
        s = rng.integers(3, 8)
        U[r:r+s, c:c+s] = 0.5 + rng.random((s, s), dtype=np.float32) * 0.1
        V[r:r+s, c:c+s] = 0.25 + rng.random((s, s), dtype=np.float32) * 0.1
    return U, V


def seed_brush(U, V, cr, cc, brush, rows, cols):
    r0, r1 = max(0, cr - brush), min(rows, cr + brush + 1)
    c0, c1 = max(0, cc - brush), min(cols, cc + brush + 1)
    U[r0:r1, c0:c1] = 0.5
    V[r0:r1, c0:c1] = 0.25


def autoseed(U, V, count, brush, rows, cols, rng):
    for _ in range(count):
        cr = rng.integers(brush, rows - brush)
        cc = rng.integers(brush, cols - brush)
        seed_brush(U, V, cr, cc, brush, rows, cols)


# ── Rendering ─────────────────────────────────────────────

def render(V: np.ndarray, cell_size: int, cmap_idx: int) -> np.ndarray:
    gray = (V * 255).astype(np.uint8)
    colored = cv2.applyColorMap(gray, COLORMAPS[cmap_idx % len(COLORMAPS)])
    if cell_size > 1:
        colored = colored.repeat(cell_size, axis=0).repeat(cell_size, axis=1)
    return colored


# ── Main loop ─────────────────────────────────────────────

def run(params: dict = None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows  = int(p["grid_height"])
    cols  = int(p["grid_width"])
    cs    = int(p["cell_size"])
    brush = int(p["brush_size"])
    spf   = int(p["steps_per_frame"])
    cmap  = int(p["colormap"]) % len(COLORMAPS)

    preset_idx = 0  # starts on coral
    rng = np.random.default_rng()
    U, V = init_grid(rows, cols)

    autoseed_interval = int(p["autoseed_interval"])
    autoseed_count    = int(p["autoseed_count"])
    frame_count = 0

    drawing = False
    mouse_pos = (0, 0)

    win = "Cellular Simulations - Reaction Diffusion"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)

    def on_mouse(event, x, y, flags, _):
        nonlocal drawing, mouse_pos
        mouse_pos = (y // cs, x // cs)
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False

    cv2.setMouseCallback(win, on_mouse)

    print("Controls:")
    print("  Left drag : seed reaction")
    print("  P         : cycle preset  (coral/spots/stripes/mitosis/worms/mazes)")
    print("  C         : cycle colormap")
    print("  R         : reset grid")
    print("  ESC / Q   : quit")

    while True:
        if drawing:
            cr, cc = mouse_pos
            seed_brush(U, V, cr, cc, brush, rows, cols)

        if autoseed_interval > 0 and frame_count % autoseed_interval == 0:
            autoseed(U, V, autoseed_count, brush, rows, cols, rng)

        for _ in range(spf):
            U, V = step(U, V, p)

        frame_count += 1

        frame = render(V, cs, cmap)

        preset_name  = PRESET_NAMES[preset_idx]
        cmap_name    = COLORMAP_NAMES[cmap % len(COLORMAP_NAMES)]
        label = f"preset: {preset_name}   colormap: {cmap_name}   P=preset  C=color  R=reset"
        cv2.putText(frame, label, (8, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imshow(win, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord('q')):
            break
        elif key == ord('r'):
            U, V = init_grid(rows, cols)
        elif key == ord('p'):
            preset_idx = (preset_idx + 1) % len(PRESET_NAMES)
            preset = PRESETS[PRESET_NAMES[preset_idx]]
            p["f"] = preset["f"]
            p["k"] = preset["k"]
            print(f"Preset: {PRESET_NAMES[preset_idx]}  f={p['f']}  k={p['k']}")
        elif key == ord('c'):
            cmap = (cmap + 1) % len(COLORMAPS)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
