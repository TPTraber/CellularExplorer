import numpy as np
import cv2
import math
import time


def generateAgents():
    # agent: y, x, angle
    # agents: y, x, angle, species
    agents = np.zeros((n_agents, 4), dtype=np.float32)

    center_y, center_x = gridsize[0] / 2, gridsize[1] / 2
    max_radius = min(gridsize[0], gridsize[1]) * 0.2  # circle radius

    # Random radii (uniform in area)
    r = max_radius * np.sqrt(rng.random(n_agents))  # sqrt for uniform area distribution
    theta = rng.random(n_agents) * 2 * math.pi       # random angles

    agents[:,0] = center_y + r * np.sin(theta)  # y position
    agents[:,1] = center_x + r * np.cos(theta)  # x position
    agents[:,2] = np.arctan2(center_y - agents[:,0], center_x - agents[:,1])
    agents[:,3] = rng.integers(0, n_species, size=n_agents)
    return agents

def sense(agents, angles, kernel_sum):
    dy, dx = np.sin(angles) * sensor_distance, np.cos(angles) * sensor_distance
    sense_positions = agents[:,:2].copy()
    sense_positions[:,0] += dy
    sense_positions[:,1] += dx
    sense_positions[:,0] = np.clip(sense_positions[:,0], 0, gridsize[0]-1)
    sense_positions[:,1] = np.clip(sense_positions[:,1], 0, gridsize[1]-1)
    sense_positions = sense_positions.astype(np.uint32)
    return kernel_sum[sense_positions[:,0], sense_positions[:,1]]

def updateAgents(agents, trails):
    angles = agents[:,2]

    kernel_sums = cv2.blur(trails, (sensor_size, sensor_size))
    if kernel_sums.ndim == 2:
        kernel_sums = kernel_sums.reshape((*kernel_sums.shape, n_species))

    total = np.sum(kernel_sums, axis=-1)
    for i in range(n_species):
        species_mask = agents[:,3] == i
        agents_masked = agents[species_mask]
        angles_masked = agents_masked[:,2]

        own = kernel_sums[..., i]
        other = total - own
        kernel_sum = own - other

        weights_forward = sense(agents_masked, angles_masked, kernel_sum)
        weights_left = sense(agents_masked, angles_masked - sensor_angle_spacing, kernel_sum)
        weights_right = sense(agents_masked, angles_masked + sensor_angle_spacing, kernel_sum)

        random_mask = (weights_forward < weights_left) & (weights_forward < weights_right)
        left_mask   = (weights_left > weights_forward) & (weights_left > weights_right)
        right_mask  = (weights_right > weights_forward) & (weights_right > weights_left)

        angles_masked[random_mask] += (rng.random(np.sum(random_mask)) - 0.5)
        angles_masked[left_mask]   -= turn_speed * rng.random(np.sum(left_mask))
        angles_masked[right_mask]  += turn_speed * rng.random(np.sum(right_mask))

        agents[species_mask, 2] = angles_masked

    angles = agents[:,2]

    dy, dx = np.sin(angles), np.cos(angles)
    agents[:,0] += dy
    agents[:,1] += dx

    agents_alt = np.zeros_like(agents)
    agents_alt[:,0] = np.clip(agents[:,0], 0, gridsize[0]-1)
    agents_alt[:,1] = np.clip(agents[:,1], 0, gridsize[1]-1)
    agents_alt[:,2] = rng.random(n_agents, dtype=np.float32) * 2 * math.pi
    agents_alt[:,3] = agents[:,3]

    mask = ((0 <= agents[:,0]) & \
            (agents[:,0] <= gridsize[0]-1) & \
            (0 <= agents[:,1]) & \
            (agents[:,1] <= gridsize[1]-1)).reshape(-1, 1)

    agents = np.where(
        mask,
        agents,
        agents_alt
    )

    return agents

def updateTrails(agents_int, trails):
    diffused_trail = cv2.blur(trails, (3,3)).astype(np.uint8)
    if diffused_trail.ndim == 2:
        diffused_trail = diffused_trail.reshape((*diffused_trail.shape, n_species))
    
    trails = (1-diffusion_speed) * trails + diffusion_speed * diffused_trail
    mask = trails >= evaporation_speed
    trails[mask] -= evaporation_speed
    trails[~mask] = 0

    for i in range(n_species):
        species = agents_int[np.where(agents_int[:,3]==i)]
        trails[species[:,0], species[:,1], i] = 255
    #trails = trails.astype(np.uint8)
    return trails

def getDisplayGrid(agents_int, trails):
    h, w, n_species = trails.shape
    grid = np.zeros((h, w, 3), dtype=np.float32)

    trails_float = trails.astype(np.float32)

    # Compute display trails: own - sum of other species
    total = np.sum(trails_float, axis=-1, keepdims=True)  # shape (h, w, 1)
    display_trails = np.maximum(0, 2*trails_float - total)  # shape (h, w, n_species)

    # Blend each species color
    for i in range(n_species):
        color = np.array(trail_color[i], dtype=np.float32) / 255.0
        grid += display_trails[..., i:i+1] * color  # broadcast to RGB

    # Clip and convert to uint8
    grid = np.clip(grid, 0, 255).astype(np.uint8)

    # Optionally draw agents on top
    for i in range(n_species):
        species_agents = agents_int[agents_int[:,3] == i]
        grid[species_agents[:,0], species_agents[:,1]] = trail_color[i]

    # Resize for display
    grid = cv2.resize(grid, (800, 800), interpolation=cv2.INTER_LINEAR)
    return grid


trail_color = [
    #(255, 255, 255),    # teal
    (250, 150, 0),    # teal
    (255, 255, 0),    # cyan
    (255, 0, 255),    # magenta
]

n_agents = 10000
n_species = 3
gridsize = 600, 600, n_species
sensor_distance = 3
sensor_size = 3
sensor_angle_spacing = math.pi / 4
turn_speed = math.pi / 15
diffusion_speed = 0.3
evaporation_speed = 4

rng = np.random.default_rng(seed=42)

if __name__ == "__main__":
    agents = generateAgents()
    trails = np.zeros(gridsize, dtype=np.uint8)

    start_time = time.time()
    frames = 0
    try:
        while True:
            frames += 1

            agents = updateAgents(agents, trails)
            agents_int = agents.astype(np.uint32)
            trails = updateTrails(agents_int, trails)
            grid = getDisplayGrid(agents_int, trails)
            cv2.imshow("img", grid)
            cv2.waitKey(20)
    except KeyboardInterrupt:
        total_time = time.time() - start_time
        fps = round(1/(total_time/frames), 2)
        print(f"fps: {fps}")
