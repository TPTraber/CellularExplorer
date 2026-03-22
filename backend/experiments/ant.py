import cv2
import numpy as np


# directions for the ant
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


def step_ant(grid: np.ndarray, x: int, y: int, direction: int, wrap: bool = True,) -> tuple[int, int, int]:
    if grid[y, x] == 0:
        direction = (direction + 1) % 4
        grid[y, x] = 1
    else:
        direction = (direction - 1) % 4
        grid[y, x] = 0

    if direction == UP: y -= 1
    elif direction == RIGHT: x += 1
    elif direction == DOWN: y += 1
    else: x -= 1

    if wrap:
        y %= grid.shape[0]
        x %= grid.shape[1]
    else:
        y = min(max(y, 0), grid.shape[0] - 1)
        x = min(max(x, 0), grid.shape[1] - 1)

    return x, y, direction

def make_cell_tiles(cell_size: int = 6, row_scale: int = 1, border: int = 1):
    h = cell_size * row_scale
    w = cell_size

    # White cell and black cell
    white = np.full((h, w, 3), 255, dtype=np.uint8)
    black = np.full((h, w, 3), 0, dtype=np.uint8)

    # Add thin black border
    for tile in (white, black):
        cv2.rectangle(tile, (0, 0), (w - 1, h - 1), (0, 0, 0), border)

    return { 0: white, 1: black,}

def render_grid(grid: np.ndarray, cell_size: int = 6, row_scale: int = 1) -> np.ndarray:
    tiles = make_cell_tiles(cell_size, row_scale)
    lut = np.stack([tiles[0], tiles[1]], axis=0)   # (2, tile_h, tile_w, 3)

    img = lut[grid]  # (rows, cols, tile_h, tile_w, 3)
    img = img.transpose(0, 2, 1, 3, 4)
    img = img.reshape(grid.shape[0] * lut.shape[1], grid.shape[1] * lut.shape[2], 3,)

    return img


def render_ant_frame(grid: np.ndarray, ant_x: int, ant_y: int, cell_size: int) -> np.ndarray:
    frame = render_grid(grid, cell_size=cell_size)

    x0 = ant_x * cell_size
    y0 = ant_y * cell_size
    frame[y0 : y0 + cell_size, x0 : x0 + cell_size] = (200, 60, 220)

    return frame

def apply_precolored_cells( grid: np.ndarray,precolored_cells: list[tuple[int, int]] | None = None,) -> None:
    if not precolored_cells:
        return

    for x, y in precolored_cells:
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            grid[y, x] = 1

def checkerboard_pattern(width: int, height: int) -> np.ndarray:
    grid = np.zeros((height, width), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            grid[y, x] = (x + y) % 2
    return grid

def animate_ant(width: int = 120, height: int = 120, steps: int = 100, cell_size: int = 6,fps: int = 10,wrap: bool = True,show_preview: bool = True, precolored_cells: list[tuple[int, int]] | None = None, checkerboard: bool = False) -> None:
    grid = np.zeros((height, width), dtype=np.uint8)
    if checkerboard:
        grid = checkerboard_pattern(width, height)
    apply_precolored_cells(grid, precolored_cells=precolored_cells)

    ant_x = width // 2
    ant_y = height // 2
    # starts looking up
    direction = UP

    for _ in range(steps):
        frame = render_ant_frame(grid, ant_x, ant_y, cell_size=cell_size)

        if show_preview:
            cv2.imshow("Langton's Ant", frame)
            key = cv2.waitKey(int(1000 / fps))
            if key == 27:
                break

        ant_x, ant_y, direction = step_ant(grid, ant_x, ant_y, direction, wrap=wrap)

    cv2.destroyAllWindows()

"""
example usage:
animate_ant(
    width=120,
    height=120,
    steps=100,
    cell_size=6,
    fps=10,
    wrap=True,
    show_preview=True,
    precolored_cells=[(60, 60), (61, 60)],
    checkerboard=False,
    )
"""