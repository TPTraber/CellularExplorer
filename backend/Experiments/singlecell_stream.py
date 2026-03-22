"""
Stream wrapper for experiments/singleCellAuto.py.
Runs a 1D elementary cellular automaton, scrolling new rows in from the bottom.
"""

import time
import numpy as np
import cv2

import experiments.singleCellAuto as sca

DEFAULT_PARAMS = {
    "rule_number":  110,
    "width":        200,
    "display_rows": 150,
    "cell_size":    4,
    "wrap":         1,
    "fps":          12,
}


def stream(sim_id: str, params=None):
    p           = {**DEFAULT_PARAMS, **(params or {})}
    rule_number = int(p["rule_number"])
    width       = int(p["width"])
    disp_rows   = int(p["display_rows"])
    cell_size   = int(p["cell_size"])
    wrap        = bool(int(p["wrap"]))
    fps         = max(1, int(p["fps"]))

    rule_map = sca.rule_to_map(rule_number)

    row = np.zeros(width, dtype=np.uint8)
    row[width // 2] = 1

    grid = np.zeros((disp_rows, width), dtype=np.uint8)
    grid[0] = row

    try:
        while True:
            row = sca.next_generation(row, rule_map, wrap=wrap)
            grid = np.roll(grid, -1, axis=0)
            grid[-1] = row

            frame = sca.render_grid(grid, cell_size=cell_size)
            ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / fps)
    finally:
        pass
