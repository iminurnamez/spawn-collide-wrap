#!/usr/bin/env python 
import sys
import random
import itertools
import pygame as pg

# Importing prepare initializes the display.
import tools
import prepare
import actors
import viewport        

MAX_NPCS = 20
DEBUG = False


class App(object):
    """This is the main class that runs the program."""
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.surface = pg.Surface(prepare.SCREEN_SIZE).convert()
        self.screen_rect = self.screen.get_rect()
        self.bg = tools.tile_surface(prepare.SCREEN_SIZE, prepare.GFX["grass"])
        self.clock  = pg.time.Clock()
        self.fps = 60
        self.done = False
        self.all_sprites = pg.sprite.LayeredDirty()
        #portions of npcs and player that wrap screen, all are Sprite.killed each tick
        self.wrapped_sprites = pg.sprite.Group()
        #holds NPCs + player
        self.people = pg.sprite.Group()
        self.player = actors.Player(self.screen_rect.center, 3, (30, 6))
        self.obstacles = self.make_obstacles()
        self.npcs = self.make_npcs()
        self.people.add(self.player)
        self.all_sprites.add(self.player)
        self.trees = self.make_trees(7)
        
        self.all_sprites.clear(self.surface, self.bg)
        
        self.viewport = viewport.Viewport(self.surface)
                    
    def divide_screen(self, cell_size, collision_group, rect=None):
        """
        Divides the screen into (TILE_SIZE, footprint_height)-sized rects.
        Returns a list of the midbottom positions of the rects that don't
        collide with any obstacles in collision_group.
        """
        size = cell_size
        rect = rect if rect else pg.Rect((0, 0), prepare.SCREEN_SIZE)
        width, height = rect.size
        spots = [pg.Rect((x, y), (size ))
                    for x in range(rect.left + size[0]//2, rect.right, size[0])
                    for y in range(rect.top + size[1], rect.bottom, size[1])
                ]
        open_spots = pg.sprite.Group()
        #Turn spots into Sprites 
        for spot in spots:
            sprite = pg.sprite.Sprite(open_spots)
            sprite.footprint = spot
        
        pg.sprite.groupcollide(collision_group, open_spots, False, True,
                                         actors.footprint_collide)
        return [open_spot.footprint.midbottom for open_spot in open_spots]
        
    def make_npcs(self):
        """
        Create a group of NPCs and add them to the all_sprites group.
        """
        #Find all open positions and grab one for each NPC
        taken = self.obstacles.copy()
        taken.add(self.player)
        open_positions = random.sample(self.divide_screen((prepare.TILE_SIZE,6), taken), MAX_NPCS)  
        
        characters = list(prepare.GFX["characters"].keys())
        npcs = pg.sprite.Group()
        for pos in open_positions:
            name = random.choice(characters)
            while name == self.player.name:
                name = random.choice(characters)
            speed = random.randint(1,3)
            way = random.choice(prepare.DIRECTIONS)
            actors.AISprite(pos, speed, (30, 6), name, way, self.all_sprites,
                                   npcs, self.people)    
        return npcs

    def make_obstacles(self):
        """
        Create some arbitrary obstacles for the sprites to run in to.
        """
        size = prepare.TILE_SIZE
        width, height = prepare.SCREEN_SIZE
        walls = pg.sprite.Group()
        footprint_size = (28, 30)
        for i in range(0, width, size):
            if i < width//2-size*2 or i >= width//2+size*2:
                actors.Obstacle((i,-size), footprint_size, "stone", walls)
                actors.Obstacle((i,0), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((i,height-size), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((i,height), footprint_size, "stone", walls)
            if size*4 <= i < size*7 or width-size*4 > i >= width-size*7:
                actors.Obstacle((i,size*4), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((i,height-size*5), footprint_size, "stone", self.all_sprites, walls)
        for j in range(size, height-size, size):
            if j < height//2-size*2 or j >= height//2+size*2:
                actors.Obstacle((-size,j), footprint_size, "stone", walls)
                actors.Obstacle((0,j), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((width-size,j), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((width,j), footprint_size, "stone", walls)
            if size*5 <= j < size*7 or height-size*5 > j >= height-size*7:
                actors.Obstacle((size*6,j), footprint_size, "stone", self.all_sprites, walls)
                actors.Obstacle((width-size*7,j), footprint_size, "stone", self.all_sprites, walls)
        return walls

    def make_trees(self, num_trees):
        size = prepare.TILE_SIZE
        width, height = prepare.SCREEN_SIZE
        trees = pg.sprite.Group()
        footprint_size = (10, 6)
        taken = self.obstacles.copy()
        taken.add(self.player, self.npcs)
        open_positions = random.sample(self.divide_screen((prepare.TILE_SIZE, footprint_size[1]), taken,
                                                         self.screen_rect.inflate((-size*2, -size*2))), num_trees)
        imgs = ("tree2",)
        for pos in open_positions:
            actors.Obstacle((pos[0], pos[1]-76), footprint_size, random.choice(imgs), self.all_sprites, self.obstacles, trees) 
        return trees
        
    def event_loop(self):
        """
        Process all events.
        Send event to player so that they can also handle the event.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            self.player.get_event(event)
            self.viewport.get_event(event)

    def display_fps(self):
        """Show the program's FPS in the window handle."""
        template = "{} - FPS: {:.2f}"
        caption = template.format(prepare.CAPTION, self.clock.get_fps())
        pg.display.set_caption(caption)

    def update(self):
        """Update all actors."""
        now = pg.time.get_ticks()
        for wrapped in self.wrapped_sprites:
            wrapped.kill()
        
        self.all_sprites.update(now, self.screen_rect, self.all_sprites,
                                         self.wrapped_sprites)
        
        #Get all collisions between people and obstacles using their
        #footprints for collison detection.  
        wall_collisions = pg.sprite.groupcollide(self.people, self.obstacles,
                                                                 False, False, actors.footprint_collide)
        npc_collisions = pg.sprite.groupcollide(self.npcs, self.npcs, False, False,
                                                                 actors.footprint_collide)
        #Deal with the collisions.
        for person, walls in wall_collisions.items():
            person.collide_with_walls(walls)
        for npc, npcs in npc_collisions.items():
            npc.collide_with_npcs(npcs, self.all_sprites)        
        for sprite in self.all_sprites:
            layer = self.all_sprites.get_layer_of_sprite(sprite)
            if layer != sprite.rect.bottom:
                self.all_sprites.change_layer(sprite, sprite.rect.bottom)
        self.render_world()
        
    def render_world(self):
        dirty = self.all_sprites.draw(self.surface)
        self.viewport.update(self.surface, dirty)
        
    def render(self):
        """
        Render all actors.
        Only update portions of the screen that change.
        """
        self.viewport.draw(self.screen)
        pg.display.update()

    def main_loop(self):
        """
        The main game loop for the whole program.
        Process events; update; render.
        """
        while not self.done:
            self.event_loop()
            self.update()
            self.render()
            self.clock.tick(self.fps)
            self.display_fps()


def main():
    """Create an App and start the program."""
    App().main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
