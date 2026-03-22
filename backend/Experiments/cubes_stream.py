"""
Stream wrapper for experiments/cubes.py.
Sets module-level globals from params, yields JPEG frames.
"""

import time
import numpy as np
import cv2

import experiments.cubes as cu

DEFAULT_PARAMS = {
    "gridsize_x":    60,
    "gridsize_y":    60,
    "gridsize_z":    60,
    "screensize":    800,
    "density":       0.1,
}


def stream(sim_id: str, params=None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    gx   = int(p["gridsize_x"])
    gy   = int(p["gridsize_y"])
    gz   = int(p["gridsize_z"])
    scr  = int(p["screensize"])
    dens = float(p["density"])

    cu.gridsize  = (gx, gy, gz)
    cu.screensize = (scr, scr)
    cu.center    = np.array((scr // 2, scr // 2), dtype=np.int32)
    s            = scr // gy // 2
    cu.xv        = np.array((int(s * 3**0.5 / 2), -s // 2), dtype=np.int32)
    cu.yv        = np.array((int(-s * 3**0.5 / 2), -s // 2), dtype=np.int32)
    cu.zv        = np.array((0, s), dtype=np.int32)

    grid = (np.random.rand(gx, gy, gz) < dens).astype(np.uint8)

    try:
        while True:
            grid    = cu.updateGrid(grid)
            display = cu.getDisplayGrid(grid)
            ok, buf = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                yield buf.tobytes()
            time.sleep(1 / 10)
    finally:
        pass
