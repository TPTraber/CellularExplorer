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
        # if wrap then lines are circular 
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


def adjusted_width_for_single_seed(min_width: int, seed_len: int, period: int) -> int:
    final_width = max(min_width, seed_len)
    remainder = (final_width - seed_len) % (2 * period)
    if remainder != 0:
        final_width += (2 * period) - remainder
    return final_width


def two_seed_layout(
    min_width: int,
    seed1_len: int,
    seed2_len: int,
    period: int,
) -> tuple[int, int, int]:
    min_ether_units = max(1, (max(min_width, 0) - seed1_len - seed2_len + period - 1) // period)
    final_width = seed1_len + seed2_len + (min_ether_units * period)

    gap_units = 1 if min_ether_units % 2 == 1 or min_ether_units == 1 else 2
    outer_units = (min_ether_units - gap_units) // 2

    left_padding = outer_units * period
    middle_gap = gap_units * period

    return final_width, left_padding, middle_gap


def animate_rule(
    rule_number: int = 110, width: int = 140, steps: int = 120, cell_size: int = 6, fps: int = 10, wrap: bool = False,
      show_preview: bool = True, ether: str = "11111000100110", seed1: str = "11111000100110", seed2: str = ""
    ) -> None:
    rule_map = rule_to_map(rule_number)

    tile = np.array([int(ch) for ch in ether], dtype=np.uint8)
    period = len(tile)

    seed_bits1 = np.array([int(ch) for ch in seed1], dtype=np.uint8)
    seed_bits2 = np.array([int(ch) for ch in seed2], dtype=np.uint8) if seed2 else np.array([], dtype=np.uint8)

    if seed_bits2.size == 0:
        width = adjusted_width_for_single_seed(width, len(seed_bits1), period)
        base_width = width - len(seed_bits1)
        repeats = (base_width + period - 1) // period
        base_row = np.tile(tile, repeats)[:base_width].copy()

        # For a centered seed, both ether flanks must be multiples of the ether period.
        start = base_width // 2
        row = np.concatenate((base_row[:start], seed_bits1, base_row[start:]))
    else:
        width, left_padding, middle_gap = two_seed_layout(width, len(seed_bits1), len(seed_bits2), period)
        right_padding = width - left_padding - len(seed_bits1) - middle_gap - len(seed_bits2)

        left_row = np.tile(tile, (left_padding + period - 1) // period)[:left_padding]
        gap_row = np.tile(tile, (middle_gap + period - 1) // period)[:middle_gap]
        right_row = np.tile(tile, (right_padding + period - 1) // period)[:right_padding]

        row = np.concatenate((left_row, seed_bits1, gap_row, seed_bits2, right_row))

    grid = np.zeros((steps, width), dtype=np.uint8)
    grid[0] = row

    frame_width = width * cell_size
    frame_height = steps * cell_size

    for t in range(steps):
        if t > 0:
            row = next_generation(row, rule_map, wrap=wrap)
            grid[t] = row

        frame = render_grid(grid[: t + 1], cell_size=cell_size)

        if frame.shape[0] < frame_height:
            pad_height = frame_height - frame.shape[0]
            pad = np.full((pad_height, frame_width, 3), 255, dtype=np.uint8)
            frame = np.vstack([frame, pad])

        if show_preview:
            cv2.imshow(f"Rule {rule_number}", frame)
            key = cv2.waitKey(int(1000 / fps))
            if key == 27:
                break

    cv2.destroyAllWindows()


def main():
    animate_rule(
        rule_number=77,
        width=140, 
        steps=80,
        cell_size=10,
        fps=12,
        wrap=True,
        show_preview=True, 
        ether="0",
        seed1 ="11"
    )
    
    # possible glider seeds: https://www.comunidad.escom.ipn.mx/genaro/Papers/Papers_on_CA_files/ATLAS/node14.html
    #  '111110100111110011100110'
    #  '111110'
    #  '11111010'


if __name__ == "__main__":
    main()
