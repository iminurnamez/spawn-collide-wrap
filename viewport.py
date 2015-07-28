import pygame as pg
import prepare


class Viewport(object):
    """A simple viewport/camera to handle scrolling and zooming a surface."""

    def __init__(self, base_map, view_size=prepare.SCREEN_SIZE, active=True):
        """The base_map argument should be a pygame.Surface object.
            Works best with view_size[0] == view_size[1]"""
        self.active = active
        self.base_map = base_map
        self.base_rect = self.base_map.get_rect()
        self.zoom_levels = {}
        for i in range(3):
            self.zoom_levels[i] = (self.base_rect.width // 2**i,
                                             self.base_rect.height // 2**i)
        self.zoom_level = 0
        self.max_zoom = len(self.zoom_levels) - 1
        self.view_size = view_size
        self.zoom_rect = pg.Rect((0, 0), self.zoom_levels[self.zoom_level])
        self.scroll_margin = 20
        self.scroll_speed = 5
        self.scroll([0, 0])

    def scroll(self, offset):
        """Move self.room_rect by offset and update image."""
        self.zoom_rect.move_ip(offset)
        self.zoom_rect.clamp_ip(self.base_rect)
        self.zoom_image()

    def zoom_image(self):
        """Set self.zoomed_image to the properly scaled subsurface."""
        subsurface = self.base_map.subsurface(self.zoom_rect)
        self.zoomed_image = pg.transform.scale(subsurface, self.view_size)

    def get_scales(self):
        """Returns the magnification scale for the current zoom level."""
        view_width, view_height = self.view_size
        x_scale = self.zoom_levels[self.zoom_level][0] / float(view_width)
        y_scale = self.zoom_levels[self.zoom_level][1] / float(view_height)
        return x_scale, y_scale
        
    def get_map_pos(self, screen_pos):
        """
        Takes in a tuple of screen coordinates and returns a tuple of
        the screen_position translated to the proper map coordinates
        for the current zoom level.
        """
        x, y = screen_pos
        x_scale, y_scale = self.get_scales()
        mapx = self.zoom_rect.left + (x * x_scale)
        mapy = self.zoom_rect.top + (y * y_scale)
        return mapx, mapy

    def get_zoom_rect(self, mapx, mapy):
        """Return a Rect of the current zoom resolution centered at mapx, mapy."""
        zoom_rect = pg.Rect((0, 0), self.zoom_levels[self.zoom_level])
        zoom_rect.center = (mapx, mapy)
        zoom_rect.clamp_ip(self.base_rect)
        return zoom_rect

    def get_event(self, event):
        """Respond to MOUSEBUTTONDOWN events, zooming in on
            left click and out on right click."""
        if not self.active:
            return
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.zoom_level < self.max_zoom:
                    mapx, mapy = self.get_map_pos(event.pos)
                    self.zoom_level += 1
                    self.zoom_rect = self.get_zoom_rect(mapx, mapy)
                    self.zoom_image()
                    pg.mouse.set_pos(prepare.SCREEN_SIZE[0]//2, prepare.SCREEN_SIZE[1]//2)
            elif event.button == 3:
                if self.zoom_level > 0:
                    mapx, mapy = self.get_map_pos(event.pos)
                    self.zoom_level -= 1
                    self.zoom_rect = self.get_zoom_rect(mapx, mapy)
                    self.zoom_image()
                    pg.mouse.set_pos(prepare.SCREEN_SIZE[0]//2, prepare.SCREEN_SIZE[1]//2)

    def update(self, surface, dirty):
        """Check for scrolling each frame."""
        if surface:
            self.base_map = surface
        mouse_pos = pg.mouse.get_pos()
        offset = [0, 0]
        
        if mouse_pos[0] < self.scroll_margin:
            offset[0] -= self.scroll_speed
        elif mouse_pos[0] > self.view_size[0] - self.scroll_margin:
            offset[0] += self.scroll_speed
        if mouse_pos[1] < self.scroll_margin:
            offset[1] -= self.scroll_speed
        elif mouse_pos[1] > self.view_size[1] - self.scroll_margin:
            offset[1] += self.scroll_speed
        if (offset != [0, 0]) or (self.zoom_rect.collidelist(dirty) != -1):
            self.scroll(offset)
        
    def draw(self, surface):
        surface.blit(self.zoomed_image, (0, 0))

            