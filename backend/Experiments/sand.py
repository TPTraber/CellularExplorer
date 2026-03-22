"""
Falling sand simulation.
Renders with OpenCV. Mouse to place materials, scroll or keys to switch type.
Call run(params) to start, or run directly.
"""

import numpy as np
import cv2
import random

# ── Material IDs ──────────────────────────────────────────
EMPTY  = 0
SAND   = 1
WATER  = 2
STONE  = 3

MATERIAL_NAMES = ["Empty", "Sand", "Water", "Stone"]

# BGR colors
COLORS = np.array([
    [10,  10,  15 ],  # empty
    [42,  190, 230],  # sand  (warm yellow)
    [180, 90,  30 ],  # water (blue)
    [75,  75,  80 ],  # stone (gray)
], dtype=np.uint8)

DEFAULT_PARAMS = {
    "grid_width":    200,
    "grid_height":   150,
    "cell_size":     4,      # pixels per cell
    "sand_slide":    0.6,    # probability of sliding diagonally
    "water_spread":  4,      # how many cells water tries to spread sideways
    "gravity":       1,      # cells dropped per frame (1 = normal)
    "brush_size":    3,      # radius in cells
}


# ── Update rules ──────────────────────────────────────────

def step(grid: np.ndarray, params: dict) -> np.ndarray:
    rows, cols = grid.shape
    new = grid.copy()
    sand_slide  = params["sand_slide"]
    water_spread = int(params["water_spread"])

    # Process bottom-to-top so gravity works in one pass
    for r in range(rows - 2, -1, -1):
        # Shuffle column order each row to remove left/right bias
        col_order = list(range(cols))
        random.shuffle(col_order)
        for c in col_order:
            cell = grid[r, c]

            if cell == SAND:
                _update_sand(grid, new, r, c, rows, cols, sand_slide)

            elif cell == WATER:
                _update_water(grid, new, r, c, rows, cols, water_spread)

    return new


def _update_sand(grid, new, r, c, rows, cols, slide_prob):
    # Fall straight down
    if grid[r + 1, c] == EMPTY:
        new[r + 1, c] = SAND
        if new[r, c] == SAND:
            new[r, c] = EMPTY
        return

    # Slide diagonally
    if random.random() < slide_prob:
        dirs = [-1, 1]
        random.shuffle(dirs)
        for dc in dirs:
            nc = c + dc
            if 0 <= nc < cols and grid[r + 1, nc] == EMPTY:
                new[r + 1, nc] = SAND
                if new[r, c] == SAND:
                    new[r, c] = EMPTY
                return


def _update_water(grid, new, r, c, rows, cols, spread):
    # Fall straight down
    if grid[r + 1, c] == EMPTY:
        new[r + 1, c] = WATER
        if new[r, c] == WATER:
            new[r, c] = EMPTY
        return

    # Slide diagonally down
    dirs = [-1, 1]
    random.shuffle(dirs)
    for dc in dirs:
        nc = c + dc
        if 0 <= nc < cols and grid[r + 1, nc] == EMPTY:
            new[r + 1, nc] = WATER
            if new[r, c] == WATER:
                new[r, c] = EMPTY
            return

    # Spread sideways
    random.shuffle(dirs)
    for dc in dirs:
        for dist in range(1, spread + 1):
            nc = c + dc * dist
            if not (0 <= nc < cols):
                break
            if grid[r, nc] == EMPTY:
                new[r, nc] = WATER
                if new[r, c] == WATER:
                    new[r, c] = EMPTY
                break
            elif grid[r, nc] != WATER:
                break


# ── Rendering ─────────────────────────────────────────────

def render(grid: np.ndarray, cell_size: int) -> np.ndarray:
    img = COLORS[grid]                          # (rows, cols, 3)
    img = img.repeat(cell_size, axis=0).repeat(cell_size, axis=1)
    return img


# ── Main loop ─────────────────────────────────────────────

def run(params: dict = None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    rows   = int(p["grid_height"])
    cols   = int(p["grid_width"])
    cs     = int(p["cell_size"])
    brush  = int(p["brush_size"])

    grid = np.zeros((rows, cols), dtype=np.uint8)

    current_material = SAND
    drawing = False
    mouse_pos = (0, 0)

    win = "Cellular Simulations - Sand"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)

    def on_mouse(event, x, y, flags, _):
        nonlocal drawing, mouse_pos, current_material
        cr, cc = y // cs, x // cs
        mouse_pos = (cr, cc)
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Right click: erase
            r0, r1 = max(0, cr - brush), min(rows, cr + brush + 1)
            c0, c1 = max(0, cc - brush), min(cols, cc + brush + 1)
            grid[r0:r1, c0:c1] = EMPTY
        elif event == cv2.EVENT_MOUSEWHEEL:
            # Scroll to cycle material
            if flags > 0:
                current_material = (current_material % (len(MATERIAL_NAMES) - 1)) + 1
            else:
                current_material = (current_material - 2) % (len(MATERIAL_NAMES) - 1) + 1

    cv2.setMouseCallback(win, on_mouse)

    print("Controls:")
    print("  Left drag  : place material")
    print("  Right click: erase")
    print("  Scroll     : cycle material  (or 1=Sand, 2=Water, 3=Stone)")
    print("  R          : reset grid")
    print("  ESC / Q    : quit")

    while True:
        if drawing:
            cr, cc = mouse_pos
            r0, r1 = max(0, cr - brush), min(rows, cr + brush + 1)
            c0, c1 = max(0, cc - brush), min(cols, cc + brush + 1)
            # Only place on empty cells (don't overwrite stone with water etc.)
            mask = grid[r0:r1, c0:c1] == EMPTY
            grid[r0:r1, c0:c1][mask] = current_material

        grid = step(grid, p)

        frame = render(grid, cs)

        # HUD: current material label
        label = f"[ {MATERIAL_NAMES[current_material]} ]  R=reset  ESC=quit"
        cv2.putText(frame, label, (8, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imshow(win, frame)

        key = cv2.waitKey(16) & 0xFF  # ~60fps cap
        if key in (27, ord('q')):     # ESC or Q
            break
        elif key == ord('r'):
            grid = np.zeros((rows, cols), dtype=np.uint8)
        elif key == ord('1'):
            current_material = SAND
        elif key == ord('2'):
            current_material = WATER
        elif key == ord('3'):
            current_material = STONE

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
