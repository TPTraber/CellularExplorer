import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import time
import random
import math
import numpy as np
import cv2
import pygame

import experiments.boid as boid

DEFAULT_PARAMS = {
    "num_boids":         100,
    "max_speed":         8,
    "min_speed":         3,
    "perception_radius": 150,
    "separation_radius": 50,
    "width":             1280,
    "height":            720,
}


def stream(sim_id: str, params=None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    width  = int(p["width"])
    height = int(p["height"])

    boid.minSpeed = float(p["min_speed"])
    boid.maxSpeed = float(p["max_speed"])

    pygame.init()
    boid.screen = pygame.Surface((width, height))

    boids = []
    for i in range(int(p["num_boids"])):
        startingX = random.randrange(0, width)
        startingY = random.randrange(0, height)
        boids.append(boid.Boid(
            pygame.Vector2(startingX, startingY),
            float(p["perception_radius"]),
            float(p["separation_radius"]),
        ))

    try:
        while True:
            boid.screen.fill((0, 0, 0))

            for boi in boids:
                boi.setNeighbours(boids)
                boi.updateVelocity()
                boi.updatePos(0.5)
                bx = boi.pos.x
                by = boi.pos.y
                boiTriangle = [(bx, by - 5), (bx - 3, by + 5), (bx, by + 2), (bx + 3, by + 5)]
                boiRotate = [
                    (pygame.Vector2(x, y) - boi.pos).rotate_rad(boi.rotation + math.pi / 2) + boi.pos
                    for x, y in boiTriangle
                ]
                pygame.draw.polygon(boid.screen, "white", boiRotate, 2)


            arr = pygame.surfarray.array3d(boid.screen)
            arr = np.transpose(arr, (1, 0, 2))
            arr = arr[:, :, ::-1]

            ok, buf = cv2.imencode('.jpg', arr, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                yield buf.tobytes()

            time.sleep(1 / 60)
    finally:
        pygame.quit()
