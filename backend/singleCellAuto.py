import cv2
import numpy as np


def rule_to_map(rule_number: int) -> dict[tuple[int, int, int], int]:
    if not (0 <= rule_number <= 255):
        raise ValueError("rule_number must be between 0 and 255")
    
    # rule_number is converted to an 8-bit binary string, where each bit corresponds to a specific neighborhood configuration
    bits = f"{rule_number:08b}"
    neighborhoods = [
        (1, 1, 1),
        (1, 1, 0),
        (1, 0, 1),
        (1, 0, 0),
        (0, 1, 1),
        (0, 1, 0),
        (0, 0, 1),
        (0, 0, 0),
    ]
    return {n: int(bit) for n, bit in zip(neighborhoods, bits)}


def next_generation(row: np.ndarray, rule_map: dict[tuple[int, int, int], int], wrap: bool = False) -> np.ndarray:
    width = len(row)
    new_row = np.zeros_like(row)

    for i in range(width):
        if wrap:
            left = row[i - 1] if i > 0 else row[-1]
            center = row[i]
            right = row[i + 1] if i < width - 1 else row[0]
        else:
            left = row[i - 1] if i > 0 else 0
            center = row[i]
            right = row[i + 1] if i < width - 1 else 0

        new_row[i] = rule_map[(int(left), int(center), int(right))]

    return new_row


def render_grid(grid: np.ndarray, cell_size: int = 6, row_scale: int = 1) -> np.ndarray:
    img = np.where(grid == 1, 0, 255).astype(np.uint8)

    img = cv2.resize(
        img,
        (grid.shape[1] * cell_size, grid.shape[0] * cell_size * row_scale),
        interpolation=cv2.INTER_NEAREST,
    )

    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    return img


def animate_rule(
    rule_number: int = 110, width: int = 151, steps: int = 120, cell_size: int = 6,
    fps: int = 10, output_path: str = "rule110.mp4", wrap: bool = False, show_preview: bool = True,
    ) -> None:

    rule_map = rule_to_map(rule_number)

    # accrding to wolfram research paper
    ether = "000100110111111"
    tile = np.array([int(ch) for ch in ether], dtype=np.uint8)

    repeats = (width + len(tile) - 1) // len(tile)
    row = np.tile(tile, repeats)[:width].copy()


    grid = np.zeros((steps, width), dtype=np.uint8)
    grid[0] = row

    frame_width = width * cell_size
    frame_height = steps * cell_size

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    for t in range(steps):
        if t > 0:
            row = next_generation(row, rule_map, wrap=wrap)
            grid[t] = row

        frame = render_grid(grid[: t + 1], cell_size=cell_size)

        if frame.shape[0] < frame_height:
            pad_height = frame_height - frame.shape[0]
            pad = np.full((pad_height, frame_width, 3), 255, dtype=np.uint8)
            frame = np.vstack([frame, pad])

        writer.write(frame)

        if show_preview:
            cv2.imshow(f"Rule {rule_number}", frame)
            key = cv2.waitKey(int(1000 / fps))
            if key == 27:
                break

    writer.release()
    cv2.destroyAllWindows()
    print(f"Saved video to {output_path}")

def main():
    animate_rule(
        rule_number=110,
        width=151,
        steps=180,
        cell_size=8,
        fps=10,
        output_path="rule110.mp4",
        wrap=False,
        show_preview=True,
    )


if __name__ == "__main__":
    main()
