import random
import math
import pyglet
import pyglet.graphics
import pyglet.resource
from pyglet.window import key


# Used to order sprites
background = pyglet.graphics.OrderedGroup(0)
foreground = pyglet.graphics.OrderedGroup(1)


class Brick(pyglet.sprite.Sprite):
    bricks = set()
    dirty = set()
    game = None

    def __init__(self, image, col=0, row=0, group=foreground):
        super().__init__(image, batch=self.game.batch, group=group)
        self.bricks.add(self)
        self.col, self.row = col, row

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, v):
        self._col = v
        self.dirty.add(self)

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, v):
        self._row = v
        self.dirty.add(self)

    def place(self):
        try:
            self.scale = self.game.brick_scale
        except AttributeError as e:
            print(type(self))
            raise
        self.x = self.game.base_x + self.col * self.game.brick_px
        self.y = self.game.base_y - (self.row + 1) * self.game.brick_px  # +1 because of anchor point

    def delete(self):
        self.dirty.discard(self)
        self.bricks.remove(self)
        super().delete()
    
    @classmethod
    def check_if_empty(cls, col, row):
        for brick in cls.bricks:
            if col == brick.col and row == brick.row and isinstance(brick, Wall):
                return False
        else:
            return True

        
class Wall(Brick):
    pass
class Floor(Brick):
    pass
    
class UP: dcol = 0; drow = -1; image_fname = 'hero_up.png'
class RIGHT: dcol = 1; drow = 0; image_fname = 'hero_right.png'
class DOWN: dcol = 0; drow = 1; image_fname = 'hero_down.png'
class LEFT: dcol = -1; drow = 0; image_fname = 'hero_left.png'

class Hero(Brick):
    def __init__(self):
        col = self.game.COLUMNS // 2
        row = self.game.ROWS // 2
        self.direction = RIGHT
        super().__init__(pyglet.resource.image(self.direction.image_fname), col, row)
        self.game.push_handlers(self.on_key_press)


    def on_key_press(self, symbol, modifiers):
        should_move = False
        if symbol == key.UP:
            self.direction = UP
            should_move = True
        elif symbol == key.RIGHT:
            self.direction = RIGHT
            should_move = True
        elif symbol == key.DOWN:
            self.direction = DOWN
            should_move = True
        elif symbol == key.LEFT:
            self.direction = LEFT
            should_move = True
            
        if should_move:
            self.image = pyglet.resource.image(self.direction.image_fname)
            col, row = self.col + self.direction.dcol, self.row + self.direction.drow
            for brick in self.bricks:
                if col == brick.col and row == brick.row and isinstance(brick, Wall):
                    break
            else:
                self.col, self.row = col, row
    
    def delete(self):
        self.game.pop_handlers()
        super().delete()
            
            
class Monster(Brick):
    STEP = 0.5
    VISION_RADIUS = 10
    def __init__(self):
        self.monster_image = pyglet.resource.image('troll.png')
        super().__init__(self.monster_image)
        
        while True:
            col = random.randint(1, self.game.COLUMNS-2)
            row = random.randint(1, self.game.ROWS-2)
            for brick in self.bricks:
                if col == brick.col and row == brick.row and not isinstance(brick, Floor):
                    break
            else:
                break  # No collision
        self.col = col
        self.row = row
        
        pyglet.clock.schedule_interval(self.move, self.STEP)
    
    
    def move(self, dt):
        current_distance = math.hypot(self.col - self.game.hero.col, self.row - self.game.hero.row)
        
        if current_distance == 0:
            return
        elif current_distance < self.VISION_RADIUS:
            best_direction = None
            best_distance = 99999
            for direction in (UP, RIGHT, DOWN, LEFT):
                distance = self.get_step_distance(direction)
                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction
        else:
            best_direction = random.choice([UP, RIGHT, DOWN, LEFT])
        
        new_col = self.col + best_direction.dcol
        new_row = self.row + best_direction.drow
        if self.check_if_empty(new_col, new_row):
            self.col = new_col
            self.row = new_row

            
    def get_step_distance(self, direction):
        col, row = self.col + direction.dcol, self.row + direction.drow
        return math.hypot(col - self.game.hero.col, row - self.game.hero.row)

    def delete(self):
        pyglet.clock.unschedule(self.move)
        super().delete()
        
        
class Game(pyglet.window.Window):
    STEP = 0.25  # Seconds
    COLUMNS = 32
    ROWS = 18

    def __init__(self):
        super().__init__(resizable=True)
        pyglet.clock.set_fps_limit(60)
        self.batch = pyglet.graphics.Batch()
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)

        self.back_image = pyglet.resource.image('background.png')
        self.back = pyglet.sprite.Sprite(
                self.back_image, batch=self.batch, group=background)

        self.ground_image = pyglet.resource.image('ground.png')
        self.brick_image = pyglet.resource.image('wall.png')
        Brick.game = self  # Set up globally used game object
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if (row == 0 or col == 0
                        or row == self.ROWS-1 or col == self.COLUMNS-1):
                    Wall(self.brick_image, col, row)
                else:
                    Floor(self.ground_image, col, row)

        self.hero = self.monster = None


    def start(self):
        if self.hero:
            self.hero.delete()
        self.hero = Hero()
        if self.monster:
            self.monster.delete()
        self.monster = Monster()
        pyglet.clock.unschedule(self.update)
        pyglet.clock.tick()
        pyglet.clock.schedule(func=self.update)
        self.time = 0.0


    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.back.scale = max(
                width / self.back_image.width, height / self.back_image.height)

        self.brick_px = min(width / self.COLUMNS, height / self.ROWS)
        self.brick_scale = self.brick_px / self.brick_image.width
        self.base_x = (width - self.brick_px * self.COLUMNS) / 2
        self.base_y = height - (height - self.brick_px * self.ROWS) / 2

        Brick.dirty |= Brick.bricks


    def on_draw(self):
        self.clear()
        while Brick.dirty:
            brick = Brick.dirty.pop()
            brick.place()
        self.batch.draw()


    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.R:
            self.start()


    def update(self, dt):
        pass


if __name__ == "__main__":
    pyglet.resource.path = ['res']
    pyglet.resource.reindex()
    window = Game()
pyglet.app.run()