import random
import itertools
import pygame as pg

import prepare
import tools


def footprint_collide(left, right):
    """
    Checks for collision between two sprites using their footprint rects instead of
    their image rects. Used as callback for sprite collision detection methods.
    """
    return left.footprint.colliderect(right.footprint)

def make_conversation(num_frames=20):
    """
    Return two list of image numbers to make conversation bubbles.
    When one side is "talking", the other shows a blank image.
    """    
    img_nums = range(1, 8)
    chat1 = []
    chat2 = []
    toggle = 0
    while len(chat1) < num_frames:
        talker, listener = (chat1, chat2) if not toggle % 2 else (chat2, chat1)
        for i in range(random.randint(2, 5)):
            talker.append(random.choice(img_nums))
            listener.append(0)
        toggle += 1
    return chat1, chat2
    

SPRITE_SIZE = (32, 36)


class RPGSprite(pg.sprite.DirtySprite):
    """Base class for player and AI sprites."""
    def __init__(self, pos, speed,  footprint_size, name, facing="DOWN", *groups):
        super(RPGSprite, self).__init__(*groups)
        self.speed = speed
        self.name = name
        self.direction = facing
        self.old_direction = None  
        self.direction_stack = []  
        self.redraw = True  
        self.animate_timer = 0.0
        self.animate_fps = 10.0
        self.walkframes = None
        self.walkframe_dict = self.make_frame_dict(self.get_frames(name))
        self.adjust_images()
        self.rect = self.image.get_rect(midbottom=pos)
        #rect for collision detection
        self.footprint = pg.Rect((0,0), footprint_size)
        self.footprint.midbottom = self.rect.midbottom
        self.dirty = 1
        
        self.chatting = False
        
        
    def get_frames(self, character):
        """Get a list of all frames."""
        sheet = prepare.GFX["characters"][character]
        all_frames = tools.split_sheet(sheet, SPRITE_SIZE, 3, 4)
        return all_frames

    def make_frame_dict(self, frames):
        """Create a dictionary of animation cycles for each direction."""
        frame_dict = {}
        for i,direct in enumerate(prepare.DIRECTIONS):
            frame_dict[direct] = itertools.cycle([frames[i][0], frames[i][2]])
        return frame_dict

    def wrap_move(self, screen_rect):
        """
        Move sprite's rect and footprint to opposite side of
        screen if rect is completely off-screen.
        """
        if self.rect.right < 0:
            self.rect.move_ip((screen_rect.width, 0))
            self.dirty = 1
        elif self.rect.left > screen_rect.right:
            self.rect.move_ip((-screen_rect.width, 0))
            self.dirty = 1
        elif self.rect.bottom < 0:
            self.rect.move_ip((0, screen_rect.height))
            self.dirty = 1
        elif self.rect.top > screen_rect.bottom:
            self.rect.move_ip((0, -screen_rect.height))
            self.dirty = 1
        self.footprint.midbottom = self.rect.midbottom
        
    def screen_wrap(self, screen_rect, all_sprites, wrapped_sprites):
        """
        Create a temporary sprite to display the portion of self.image
        that is off-screen and adds it to all_sprites for drawing and
        wrapped_sprites for culling on the next tick.
        """        
        x, y = self.rect.topleft
        w, h = self.rect.size
        if self.rect.left < 0:
            sub_rect = pg.Rect((0, 0), (abs(x), h))
            wrap_rect = pg.Rect((screen_rect.right + x, y), sub_rect.size)
        elif self.rect.right >  screen_rect.right:
            sub_w = self.rect.right - screen_rect.right
            sub_rect = pg.Rect((w - sub_w, 0), (sub_w, h))
            wrap_rect = pg.Rect((0, y), sub_rect.size)
        elif self.rect.top < 0:
            sub_rect = pg.Rect((0, 0), (w, abs(y)))
            wrap_rect = pg.Rect((x, screen_rect.bottom + y), sub_rect.size)
        elif self.rect.bottom > screen_rect.bottom:
            sub_h = self.rect.bottom - screen_rect.bottom
            sub_rect = pg.Rect((0, h - sub_h), (w, sub_h))
            wrap_rect = pg.Rect((x, 0), sub_rect.size)
        
        sprite = pg.sprite.DirtySprite(all_sprites, wrapped_sprites)
        sprite.image = self.image.subsurface(sub_rect)
        sprite.rect = wrap_rect
        sprite.dirty = 1
        all_sprites.change_layer(sprite, sprite.rect.bottom)
        self.dirty = 1
            
    def adjust_images(self, now=0):
        """Update the sprite's walkframes as the sprite's direction changes."""
        if self.direction != self.old_direction:
            self.walkframes = self.walkframe_dict[self.direction]
            self.old_direction = self.direction
            self.redraw = True
        self.make_image(now)

    def make_image(self, now):
        """Update the sprite's animation as needed."""
        if self.redraw or now-self.animate_timer > 1000/self.animate_fps:
            self.image = next(self.walkframes)
            self.animate_timer = now
            self.dirty = 1
        self.redraw = False

    def add_direction(self, direction):
        """
        Add direction to the sprite's direction stack and change current
        direction.
        """
        if direction in self.direction_stack:
            self.direction_stack.remove(direction)
        self.direction_stack.append(direction)
        self.direction = direction

    def pop_direction(self, direction):
        """
        Remove direction from direction stack and change current direction
        to the top of the stack (if not empty).
        """
        if direction in self.direction_stack:
            self.direction_stack.remove(direction)
        if self.direction_stack:
            self.direction = self.direction_stack[-1]
    
    def bounce(self, rect, direction, bounce_amount=4):
        """
        Bounce sprite off an obstacle by bounce amount in the opposite
        direction the sprite is travelling. 
        """
        offsets = {"LEFT": (rect.right - (self.footprint.left - bounce_amount), 0),
                    "RIGHT": (rect.left - (self.footprint.right + bounce_amount), 0),
                    "UP": (0, rect.bottom - (self.footprint.top - bounce_amount)),
                    "DOWN": (0, rect.top - (self.footprint.bottom + bounce_amount))}
        self.rect.move_ip(offsets[direction])
        self.footprint.midbottom = self.rect.midbottom
        
    def update(self, now, screen_rect, all_sprites, wrapped_sprites):
        """Update image and position of sprite."""
            
        self.adjust_images(now)
        self.wrap_move(screen_rect)
        if self.rect.clamp(screen_rect) != self.rect:
            self.screen_wrap(screen_rect, all_sprites, wrapped_sprites)
            self.dirty = 1            
        if self.direction_stack and not self.chatting:
            direction_vector = prepare.DIRECT_DICT[self.direction]
            self.rect.x += self.speed*direction_vector[0]
            self.rect.y += self.speed*direction_vector[1]
            self.dirty = 1
        self.footprint.midbottom = self.rect.midbottom
            
    def draw(self, surface):
        """Draw sprite to surface (not used if using group draw functions)."""
        return surface.blit(self.image, self.rect)
       

class Player(RPGSprite):
    """This class will represent the user controlled character."""
    def __init__(self, pos, speed, footprint_size, name="warrior_m",  facing="DOWN", *groups):
        super(Player, self).__init__(pos, speed, footprint_size, name, facing, *groups)
        self.grunts = [prepare.SFX["gruntsound{}".format(x)] for x in (1,)]
        self.grunt_cooldown_time = 600
        self.grunt_cooldown = 0
        
    def get_event(self, event):
        """Handle events pertaining to player control."""
        if event.type == pg.KEYDOWN:
            self.add_direction(event.key)
        elif event.type == pg.KEYUP:
            self.pop_direction(event.key)

    def update(self, now, screen_rect, all_sprites, wrapped_sprites):
        """Call base classes update method and clamp player to screen."""
        super(Player, self).update(now, screen_rect, all_sprites, wrapped_sprites)
        
    def collide_with_walls(self, walls):
        """
        Bounce off the first wall in walls (a list of allwalls that the sprite collides with).
        Only responding to one collision per tick avoids rattling around in corners or
        "bouncing" multiple times.
        """        
        self.bounce(walls[0].footprint, self.direction)
        now = pg.time.get_ticks()
        if now - self.grunt_cooldown > self.grunt_cooldown_time:
            random.choice(self.grunts).play()
            self.grunt_cooldown = now
            
    def add_direction(self, key):
        """Remove direction from stack if corresponding key is released."""
        if key in prepare.CONTROLS:
            super(Player, self).add_direction(prepare.CONTROLS[key])

    def pop_direction(self, key):
        """Add direction to stack if corresponding key is pressed."""
        if key in prepare.CONTROLS:
            super(Player, self).pop_direction(prepare.CONTROLS[key])


class AISprite(RPGSprite):
    """A non-player controlled sprite."""
    def __init__(self, pos, speed, footprint_size, name, facing, *groups):
        super(AISprite, self).__init__(pos, speed, footprint_size, name, facing, *groups)
        self.wait_range = (500, 2000)
        self.wait_delay = random.randint(*self.wait_range)
        self.wait_time = 0.0
        self.change_direction()
        self.chat_cooldown_range = (5000, 10000)
        self.chat_cooldown_time = random.randint(*self.chat_cooldown_range)
        self.chat_duration = 5000
        self.chat_timer = 0
        
        self.bubble = None
        
    def update(self, now, screen_rect, all_sprites, wrapped_sprites):
        """
        Choose a new direction if wait_time has expired or the sprite
        attempts to leave the screen.
        """
        if now-self.wait_time > self.wait_delay and not self.chatting:
            self.change_direction(now)
        if now - self.chat_timer > self.chat_duration:
            self.chatting = False
            if self.bubble:
                self.bubble.kill()
        super(AISprite, self).update(now, screen_rect, all_sprites, wrapped_sprites)
                        
    def collide_with_walls(self, walls):
        """
        Bounce off the first wall in walls (a list of allwalls that the sprite collides with)
        and change direction to something other than the sprite's current direction.
        """
        self.bounce(walls[0].footprint, self.direction)
        self.change_direction(restricted=self.direction)
        
    def collide_with_npcs(self, npcs, all_sprites):
        now = pg.time.get_ticks()
        for npc in npcs:
            if npc is not self:
                if (now - self.chat_timer > self.chat_cooldown_time and 
                    now - npc.chat_timer > npc.chat_cooldown_time):
                    if self.rect.centerx < npc.rect.centerx:
                        self.add_direction("RIGHT")
                        npc.add_direction("LEFT")
                    else:
                        self.add_direction("LEFT")
                        npc.add_direction("RIGHT")
                    self.wait_time = now
                    npc.wait_time = now
                    self.wait_dealy = self.chat_duration
                    npc.wait_dealy = npc.chat_duration
                    self.chat_timer = now
                    npc.chat_timer = now
                    self.chatting = True
                    npc.chatting = True
                    chat1, chat2 = make_conversation()
                    self.bubble = ChatBubble(self.rect.midbottom, chat1, self.chat_duration, all_sprites)
                    npc.bubble = ChatBubble(npc.rect.midbottom, chat2, npc.chat_duration, all_sprites)
                    self.chat_cooldown_time = random.randint(*self.chat_cooldown_range) + self.chat_duration
                    npc.chat_cooldown_time = random.randint(*npc.chat_cooldown_range) + npc.chat_duration
                    break
        
    def change_direction(self, now=0, restricted=None):
        """
        Empty the stack and choose a new direction.  The sprite may also
        choose not to go idle (choosing direction=None). Passing a direction
        as restricted eliminates that direction and None from the possible
        new directions.
        """
        self.direction_stack = []
        directions = list(prepare.DIRECTIONS + (None, ))
        if restricted:
            directions.remove(restricted)
            directions.remove(None)
        direction = random.choice(directions)
        if direction:
            super(AISprite, self).add_direction(direction)
        
        self.wait_delay = random.randint(*self.wait_range)
        self.wait_time = now    
            
    
class ChatBubble(pg.sprite.DirtySprite):    
    def __init__(self, midbottom, img_nums, chat_duration, *groups):
        super(ChatBubble, self).__init__(*groups)
        images = [prepare.GFX["bubble{}".format(x)] for x in img_nums]
        self.images = itertools.cycle(images)
        self.frame_duration = 300
        self.frame_time = pg.time.get_ticks()
        self.image = next(self.images)
        self.rect = self.image.get_rect(midbottom=midbottom)
        
    def update(self, now, screen_rect, all_sprites, wrapped_sprites):
        if now - self.frame_time > self.frame_duration:
            self.frame_time = now
            self.image = next(self.images)
            self.dirty = 1
    

class Obstacle(pg.sprite.DirtySprite):
    def __init__(self, pos, footprint_size, image_name, *groups):
        super(Obstacle, self).__init__(*groups)
        self.image = prepare.GFX[image_name]
        self.rect = self.image.get_rect(topleft=pos)
        self.footprint = pg.Rect((0,0), footprint_size)
        self.footprint.midbottom = self.rect.midbottom
