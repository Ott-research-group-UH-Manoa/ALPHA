#!/usr/bin/env python3
import os
os.environ["SDL_VIDEODRIVER"] = "x11"   # set BEFORE importing pygame
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
os.environ["SDL_RENDER_DRIVER"] = "software"
# optional: ensure we don't accidentally try Wayland
os.environ.pop("WAYLAND_DISPLAY", None)
os.environ["XDG_SESSION_TYPE"] = "x11"

import pygame, sys
print("DISPLAY =", os.environ.get("DISPLAY"))
pygame.display.init()
print("driver:", pygame.display.get_driver())
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Pygame over X11")
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: running = False
    screen.fill((0, 100, 200))
    pygame.display.flip()
pygame.quit(); sys.exit()
