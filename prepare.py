import os
import pygame as pg
import tools


# Useful constants.
CAPTION = "Spawn, Collide, Wrap"
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE = (512, 512) #(764, 764)
TILE_SIZE = 32 # Assume tiles are square.
BACKGROUND_COLOR = pg.Color("darkgreen")


DIRECT_DICT = {"UP"    : ( 0,-1),
               "RIGHT" : ( 1, 0),               
               "DOWN"  : ( 0, 1),
               "LEFT"  : (-1, 0)}


DIRECTIONS = ("UP", "RIGHT", "DOWN", "LEFT")


CONTROLS = {pg.K_UP    : "UP",
            pg.K_RIGHT : "RIGHT",
            pg.K_DOWN  : "DOWN",
            pg.K_LEFT  : "LEFT"}


# Set up environment.
os.environ['SDL_VIDEO_CENTERED'] = '1'
pg.init()
pg.display.set_caption(CAPTION)
pg.display.set_mode(SCREEN_SIZE)


# Load all graphics.
GFX = {}
GFX = tools.load_all_gfx("resources")
GFX["characters"] = tools.load_all_gfx(os.path.join("resources", "rpgsprites"))
bubbles = tools.split_sheet(GFX["bubblesheet"], (32, 56), 8, 1)
for i, bubble in enumerate(bubbles[0]):
    GFX["bubble{}".format(i)] = bubble

SFX = tools.load_all_sounds(os.path.join("resources", "sounds"))