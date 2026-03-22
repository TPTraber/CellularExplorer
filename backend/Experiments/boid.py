import pygame
import random
import math

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

boidNum  = 100
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
        self.pos = self.pos + (self.velocity * speed)
        if self.pos.x <= 0:
            self.velocity.x *= -1
        elif self.pos.x >= screen.get_width():
            self.velocity.x *= -1
        if self.pos.y <= 0:
            self.velocity.y *= -1
        elif self.pos.y >= screen.get_height():
            self.velocity.y *= -1
    
    def setNeighbours(self, boids):
        self.neighbors = []
        for boi in boids:
            boiDis = pygame.Vector2.distance_to(self.pos, boi.pos)
            if boi != self and boiDis <= self.fearDistance:
                self.evilNeighbors.append(boi)
            elif boi != self and boiDis <= self.sightDistance:
                self.neighbors.append(boi)
    
    def updateCohesion(self):
        sumVector = pygame.Vector2()
        if len(self.neighbors) == 0: 
            self.cohesion = pygame.Vector2()
            return
        for boi in self.neighbors:
            sumVector += boi.pos - self.pos
        self.cohesion = sumVector / len(self.neighbors)
        
    def updateAlignment(self):
        sumVector = pygame.Vector2()
        if len(self.neighbors) == 0: 
            self.cohesion = sumVector
            return
        for boi in self.neighbors:
            sumVector += boi.velocity
        self.alignment = sumVector / len(self.neighbors)
    
    def updateSeparation(self):
        sumVector = pygame.Vector2()
        if len(self.evilNeighbors) == 0:
            self.separation = sumVector
            return
        for boi in self.evilNeighbors:
            sumVector += self.pos - boi.pos
        self.separation = sumVector / len(self.evilNeighbors)

    def updateVelocity(self, cohesionM = 0.05, alignmentM = 0.05, separationM = 0.01):
        self.updateCohesion()
        self.updateAlignment()
        self.updateSeparation()
        self.velocity += self.cohesion * cohesionM
        self.velocity += self.alignment * alignmentM
        self.velocity += self.separation * separationM

        speed = self.velocity.magnitude()

        if speed > maxSpeed:
            self.velocity = (self.velocity/speed)*maxSpeed
        if speed < minSpeed:
            self.velocity = (self.velocity/speed)*maxSpeed


boids=[]

for i in range(0,boidNum):
    startingX = random.randrange(0, screen.get_width())
    startingY = random.randrange(0, screen.get_width())
    boids.append(Boid(pygame.Vector2(startingX, startingY), 150, 50))

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    #screen.fill("black")
    dim_surface = pygame.Surface(screen.get_size()).convert_alpha()
    dim_surface.fill((5, 5, 5))


    for boi in boids:
        boi.setNeighbours(boids)
        boi.updateVelocity()
        boi.updatePos(0.5)
        bx = boi.pos.x
        by = boi.pos.y
        boiTriangle = [(bx, by - 5), (bx - 3, by + 5), (bx, by + 2), (bx + 3, by + 5)]
        boiRotate = [
            (pygame.Vector2(x, y) - boi.pos).rotate_rad(boi.rotation + math.pi/2) + boi.pos for x, y in boiTriangle
        ]
        pygame.draw.polygon(screen, "white", boiRotate, 2)

    screen.blit(dim_surface, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()