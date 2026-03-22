import numpy as np
import cv2
import math
import time

from scipy.ndimage import convolve

kernel = np.ones((3, 3, 3), dtype=np.uint8)  # preallocate once
def updateGrid(grid):
    neighbor_count = convolve(grid, kernel, mode='constant') - grid
    to_live = ((grid==1) & ((neighbor_count==4) | (neighbor_count==5))) | \
              ((grid==0) & ((neighbor_count==5) | (neighbor_count==5)))
    return to_live.astype(np.uint8)

def coords_to_rgb(coords_norm, scale=255):
    """
    Convert 3D coordinates to RGB values.

    Parameters:
    -----------
    coords : np.ndarray
        Array of shape (N, 3) with (x, y, z) coordinates.
    scale : int or float
        Scale of the output RGB values. Use 1 for [0,1], 255 for [0,255].

    Returns:
    --------
    rgb : np.ndarray
        Array of shape (N, 3) with RGB values.
    """

    # Scale to desired range
    rgb = coords_norm * scale

    # Convert to integers if scale > 1
    if scale > 1:
        rgb = rgb.astype(np.uint8)
    
    return rgb.tolist(), (rgb * 0.8).tolist(), (rgb * 0.6).tolist()

def drawCube(display, pos):
    x, y, z = pos
    coords_norm = 1-np.array((x/gridsize[0], y/gridsize[1], z/gridsize[2]), dtype=np.float32)
    colors = coords_to_rgb(coords_norm)
    screen_pos = center + x*xv + y*yv + z*zv
    # top
    points = np.array((
        screen_pos,
        screen_pos + xv,
        screen_pos + xv + yv,
        screen_pos + yv,
    ), dtype=np.int32)
    display = cv2.fillPoly(
        display,
        [points],
        colors[0]
    )
    # left
    points = np.array((
        screen_pos,
        screen_pos + yv,
        screen_pos + yv + zv,
        screen_pos + zv,
    ), dtype=np.int32)
    display = cv2.fillPoly(
        display,
        [points],
        colors[1]
    )
    # right
    points = np.array((
        screen_pos,
        screen_pos + xv,
        screen_pos + xv + zv,
        screen_pos + zv,
    ), dtype=np.int32)
    display = cv2.fillPoly(
        display,
        [points],
        colors[2]
    )

def getDisplayGrid(grid):
    display = np.full((*screensize, 3), colors["bg"], dtype=np.uint8)
    coords = np.argwhere(grid == 1)
    if len(coords) == 0:
        return display

    # Compute screen-space positions
    coords = np.argwhere(grid == 1)  # shape (N, 3)
    # compute priority
    prio = -coords.sum(axis=1)  # x + y + z for each coordinate
    # get sorted indices based on priority
    sorted_idx = np.argsort(prio)
    # reorder coordinates
    coords_sorted = coords[sorted_idx]

    # Draw cubes back-to-front
    for i, pos in enumerate(coords_sorted):
        drawCube(display, pos)

    return display

colors = {
    "bg": (50, 50, 50),
    "top": (225, 225, 225),
    "left": (150, 150, 150),
    "right": (100, 100, 100)
}

screensize = 800, 800
gridsize = 60, 60, 60
center = np.array((screensize[0] // 2, screensize[1] // 2), dtype=np.int32)
s = screensize[0] // gridsize[1] // 2

# basis vectors
xv = np.array((s * 3**0.5 / 2, -s / 2), dtype=np.int32)
yv = np.array((-s * 3**0.5 / 2, -s / 2), dtype=np.int32)
zv = np.array((0, s), dtype=np.int32)

if __name__ == "__main__":
    #grid = np.zeros(gridsize, dtype=np.uint8)
    grid = (np.random.rand(*gridsize) < 0.1).astype(np.uint8)

    start_time = time.time()
    frames = 0
    try:
        while True:
            frames += 1
            grid = updateGrid(grid)
            display = getDisplayGrid(grid)
            cv2.imshow("img", display)
            cv2.waitKey(200)
    except KeyboardInterrupt:
        total_time = time.time() - start_time
        fps = round(1/(total_time/frames), 2)
        print(f"fps: {fps}")
