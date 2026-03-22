import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import random
import math
import time
import numpy as np
import cv2

DEFAULT_PARAMS = {
    "num_boids":         100,
    "max_speed":         8,
    "min_speed":         3,
    "perception_radius": 150,
    "separation_radius": 50,
    "alignment_weight":  0.05,
    "cohesion_weight":   0.05,
    "separation_weight": 0.01,
    "width":             1280,
    "height":            720,
}

# global surface reference so Boid.updatePos can call screen.get_width/height
screen = None

# ── Boid class copied verbatim from boid.py ───────────────────────

minSpeed = 3
maxSpeed = 8

class Boid:
    def __init__(self, startingPos, sightDistance, fearDistance):
        self.pos = startingPos
        self.sightDistance = sightDistance
        self.fearDistance = fearDistance
        self.velocity = pygame.Vector2(random.random() * 10 - 5,random.random() * 10 - 5)
        self.rotation = 0
        self.neighbors = []
        self.evilNeighbors = []
        self.cohesion = pygame.Vector2()
        self.separation = pygame.Vector2()
        self.alignment = pygame.Vector2()

    def updatePos(self, speed):
        self.rotation = math.atan2(self.velocity.y , self.velocity.x)
        
        if self.pos.x <= 0:
            self.velocity.x *= -1
        elif self.pos.x >= screen.get_width():
            self.velocity.x *= -1
        if self.pos.y <= 0:
            self.velocity.y *= -1
        elif self.pos.y >= screen.get_height():
            self.velocity.y *= -1
        
        self.pos = self.pos + (self.velocity * speed)

    def setNeighbours(self, boids):
        self.neighbors = []
        for boi in boids:
            boiDis = pygame.Vector2.distance_to(self.pos, boi.pos)
            if boi != self and boiDis <= self.fearDistance:
                self.evilNeighbors.append((boi, boiDis))
            elif boi != self and boiDis <= self.sightDistance:
                self.neighbors.append((boi, boiDis))

    def updateCohesion(self):
        sumVector = pygame.Vector2()
        if len(self.neighbors) == 0:
            self.cohesion = pygame.Vector2()
            return
        for boi, d in self.neighbors:
            sumVector += (boi.pos - self.pos) * (1-d/self.sightDistance) / self.sightDistance
        self.cohesion = sumVector / len(self.neighbors)

    def updateAlignment(self):
        sumVector = pygame.Vector2()
        if len(self.neighbors) == 0:
            self.cohesion = sumVector
            return
        for boi, d in self.neighbors:
            sumVector += boi.velocity
        self.alignment = sumVector / len(self.neighbors)

    def updateSeparation(self):
        sumVector = pygame.Vector2()
        if len(self.evilNeighbors) == 0:
            self.separation = sumVector
            return
        for boi, d in self.evilNeighbors:
            sumVector += (self.pos - boi.pos) * (1-d/self.sightDistance) / self.sightDistance
        self.separation = sumVector / len(self.evilNeighbors)

    def updateVelocity(self, cohesionM=0.05, alignmentM=0.05, separationM=0.01):
        self.updateCohesion()
        self.updateAlignment()
        self.updateSeparation()
        self.velocity += (self.cohesion-self.velocity) * cohesionM
        self.velocity += (self.alignment-self.velocity) * alignmentM
        self.velocity += self.separation * separationM

        margin = 50
        if self.pos.x < margin:
            self.velocity.x = self.velocity.x + 0.15
        if self.pos.x > screen.get_width() - margin:
            self.velocity.x = self.velocity.x - 0.15
        if self.pos.y < margin:
            self.velocity.y = self.velocity.y + 0.15
        if self.pos.y > screen.get_height() - margin:
            self.velocity.y = self.velocity.y + 0.15

        speed = self.velocity.magnitude()

        if speed > maxSpeed:
            self.velocity = (self.velocity / speed) * maxSpeed
        if speed < minSpeed:
            self.velocity = (self.velocity / speed) * minSpeed

# ── Stream ────────────────────────────────────────────────────────

def stream(sim_id: str, params=None):
    global screen, minSpeed, maxSpeed

    p = {**DEFAULT_PARAMS, **(params or {})}

    width    = int(p["width"])
    height   = int(p["height"])
    boidNum  = int(p["num_boids"])
    minSpeed = float(p["min_speed"])
    maxSpeed = float(p["max_speed"])
    cohM     = float(p["cohesion_weight"])
    aliM     = float(p["alignment_weight"])
    sepM     = float(p["separation_weight"])
    sightR   = float(p["perception_radius"])
    fearR    = float(p["separation_radius"])

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    

    boids = []
    for i in range(boidNum):
        startingX = random.randrange(0, width)
        startingY = random.randrange(0, height)
        boids.append(Boid(pygame.Vector2(startingX, startingY), sightR, sightR))

    frame_count = 0
    try:
        while True:

            trail = False
            if trail:
                dim_surface = pygame.Surface(screen.get_size()).convert_alpha()
                dim_surface.fill((5, 5, 5))
                screen.blit(dim_surface, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
            else:
                screen.fill((0,0,0))

            for boi in boids:
                if frame_count % 2 == 0:
                    boi.setNeighbours(boids)
                boi.updateVelocity(cohM, aliM, sepM)
                boi.updatePos(0.5)
                bx = boi.pos.x
                by = boi.pos.y
                boiTriangle = [(bx, by - 5), (bx - 3, by + 5), (bx, by + 2), (bx + 3, by + 5)]
                boiRotate = [
                    (pygame.Vector2(x, y) - boi.pos).rotate_rad(boi.rotation + math.pi / 2) + boi.pos
                    for x, y in boiTriangle
                ]
                pygame.draw.polygon(screen, "white", boiRotate, 2)
            

            arr = pygame.surfarray.array3d(screen)   # (w, h, 3) RGB
            arr = np.transpose(arr, (1, 0, 2))       # -> (h, w, 3)
            arr = arr[:, :, ::-1]                    # RGB -> BGR for cv2

            ok, buf = cv2.imencode('.jpg', arr, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                yield buf.tobytes()

            frame_count += 1
            time.sleep(1 / 15)
    finally:
        pygame.quit()