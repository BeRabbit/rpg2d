import logging as log
import math
import random

import pyglet
import pyglet.graphics
import pyglet.resource
from pyglet.window import key


# Used to order sprites
back_image = pyglet.graphics.OrderedGroup(0)
background = pyglet.graphics.OrderedGroup(1)
on_floor = pyglet.graphics.OrderedGroup(2)
foreground = pyglet.graphics.OrderedGroup(3)
hud = pyglet.graphics.OrderedGroup(4)


log.basicConfig(level=log.DEBUG, format = '%(asctime)s %(message)s')

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
        self.scale = self.game.brick_scale
        self.x = self.game.base_x + self.col * self.game.brick_px
        self.y = self.game.base_y - (self.row + 1) * self.game.brick_px  # +1 because of anchor point

    def delete(self):
        log.debug("Brick delete, type %s", type(self))
        self.dirty.discard(self)
        self.bricks.remove(self)
        super().delete()

    @classmethod
    def check_collision(cls, col, row, types=None):
        if types is None:
            types = (Wall, Monster, Hero, Chest, Door)

        for brick in cls.bricks:
            if col == brick.col and row == brick.row and isinstance(brick, types):
                return brick
        else:
            return  # No collision, return None


class Wall(Brick):
    pass
class Floor(Brick):
    pass

class UP: dcol = 0; drow = -1; image_fname = 'hero_up.png'
class RIGHT: dcol = 1; drow = 0; image_fname = 'hero_right.png'
class DOWN: dcol = 0; drow = 1; image_fname = 'hero_down.png'
class LEFT: dcol = -1; drow = 0; image_fname = 'hero_left.png'

class Hero(Brick):
    STEP = 0.01

    def __init__(self):
        col = self.game.COLUMNS // 2
        row = self.game.ROWS // 2
        self.direction = RIGHT
        super().__init__(pyglet.resource.image(self.direction.image_fname), col, row)
        log.debug("Draw %s", type (self))
        pyglet.clock.schedule_interval(self.step, self.STEP)
        
        self.health = 10
        self.max_health = 10
        self.potion = 0
        self.xp = 0
        self.level = 1
        self.armor = 0
        self.max_armor = 10
        self.sword = 0
        self.max_sword = 10
        self.attack = 5 + self.level//2
        self.defense = 5 + self.level//2

    def armor_limit(self):
        if self.armor > 10:
            self.armor = self.max_armor


    def sword_limit(self):
        if self.sword > 10:
            self.sword = self.max_sword

    def use_potion(self):
        if self.health < self.max_health:
            self.amount = self.max_health/3
            self.health += amount
            round(self.health)
            self.potion -= 1
        elif self.potion <= 0:
            return
        elif self.health < self.max_health:
            return

    def hp_limit(self):
        if self.health > self.max_health:
            self.health = self.max_health
   
    def level_up(self):
        if self.xp >= self.level**2 * 10:
            self.level += 1
            self.max_health += self.level
            self.health = self.max_health
    
    def die(self):
        if self.health <= 0:
            self.image = pyglet.resource.image('rip.png')
            self.game.label.text = "Game Over"
            pyglet.clock.unschedule(self.step)          


    def step(self, dt):
        want_move = False
        if self.game.keys[key.UP]:
            self.direction = UP
            log.debug('Go Up')
            want_move = True
        elif self.game.keys[key.RIGHT]:
            self.direction = RIGHT
            log.debug('Go Right')
            want_move = True
        elif self.game.keys[key.DOWN]:
            self.direction = DOWN
            log.debug('Go Down')
            want_move = True
        elif self.game.keys[key.LEFT]:
            self.direction = LEFT
            log.debug('Go Left')
            want_move = True

        want_action = False
        
        if self.game.keys[key.SPACE]:
            log.debug('Start Action')
            want_action = True
        if want_move:
            self.image = pyglet.resource.image(self.direction.image_fname)
        if want_action or want_move:
            col, row = self.col + self.direction.dcol, self.row + self.direction.drow
            obstacle = self.check_collision(col, row)
            if not obstacle:
                if want_move:
                    self.col, self.row = col, row
                    armor = self.check_collision(col, row, Armor)
                    if armor:
                        self.armor += 1
                        self.armor_limit()
                        armor.delete()
                    sword = self.check_collision(col, row, Sword)
                    if sword:
                        self.sword += 1
                        self.sword_limit()
                        sword.delete()
            elif isinstance(obstacle, Monster) and want_action:
                self.fight(obstacle)
            elif isinstance(obstacle, Chest) and want_action:
                self.open_chest(obstacle)
            elif isinstance(obstacle, Door) and want_action:
                self.open_door(obstacle)
                
        self.game.set_label_text()
        
        
    def calc_damage(self, attack, defense):
        a = int(random.random() * attack)
        d = int(random.random() * defense)
        return max(0, a-d)      
        
    def fight(self, monster):  
    
        monster.start_fight()
        
        while monster.hp > 0 and self.health > 0:
            defense = self.defense + self.armor
            dmg = self.calc_damage(monster.attack, defense)
            if dmg > 0:
                self.health -= dmg
                if self.health <=0 :
                    break
            else:
                pass

            attack =  self.attack + self.sword
            dmg = self.calc_damage(attack, monster.defense)
            if dmg > 0:
                monster.hp -= dmg
                if monster.hp < 1:
                    self.xp += monster.xp
            else:
                pass
        
        self.game.set_label_text()
        self.level_up()
        self.die()
        self.hp_limit
        
    def open_chest(self, chest):
        chest.open()
        
    def open_door(self, door):
        door.open()    
    
    def delete(self):
        pyglet.clock.unschedule(self.step)
        super().delete()
        

class Monster(Brick):
    STEP = 0.5
    VISION_RADIUS = 5
    monsters = set()


    def __init__(self):
        self.monster_image = pyglet.resource.image('troll.png')
        log.debug('Sprite Monster')
        super().__init__(self.monster_image)
        self.monsters.add(self)
        self.in_fight = False
        self.statistics()
        
        while True:
            col = random.randint(1, self.game.COLUMNS-2)
            row = random.randint(1, self.game.ROWS-2)
            if not self.check_collision(col, row):
                break
        self.col = col
        self.row = row

        pyglet.clock.schedule_interval(self.move, self.STEP - 0.1 * random.random())


    def statistics(self):
        if self.game.hero.level > 0 and self.game.hero.level < 10:
            self.hp = random.randint(2,10)       # HP
            self.attack = random.randint(2,5)     # DMG
            self.defense = random.randint(2,5)     # DEF
            self.xp = random.randint(2,6)           # XP
        elif self.game.hero.level > 10 and self.game.hero.level < 20:
            self.hp = random.randint(8,15)       # HP
            self.attack = random.randint(5,10)    # DMG
            self.defense = random.randint(5,10)    # DEF
            self.xp = random.randint(6,10)          # XP
        elif self.game.hero.level > 20 and self.game.hero.level < 30:
            self.hp = random.randint(14,20)      # HP
            self.attack = random.randint(8,15)    # DMG
            self.defense = random.randint(8,15)    # DEF
            self.xp = random.randint(10,14)         # XP
        elif self.game.hero.level > 30 and self.game.hero.level < 40:
            self.hp = random.randint(20,25)      # HP
            self.attack = random.randint(11,20)   # DMG
            self.defense = random.randint(11,20)   # DEF
            self.xp = random.randint(14,18)         # XP
        elif self.game.hero.level > 40 and self.game.hero.level < 50:
            self.hp = random.randint(26,30)      # HP
            self.attack = random.randint(14,25)   # DMG
            self.defense = random.randint(14,25)   # DEF
            self.xp = random.randint(18,22)         # XP



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
        if not self.check_collision(new_col, new_row):
            self.col = new_col
            self.row = new_row


    def get_step_distance(self, direction):
        col, row = self.col + direction.dcol, self.row + direction.drow
        return math.hypot(col - self.game.hero.col, row - self.game.hero.row)


    def start_fight(self):
        if self.in_fight:
            return
        log.debug("Start fight")
        self.in_fight = True
        pyglet.clock.unschedule(self.move)
        self.image = pyglet.resource.image('blood.png')
        pyglet.clock.schedule_once(self.end_fight, self.STEP)



    def end_fight(self, dt):
        log.debug("End fight")
        self.delete()


    def delete(self):
        pyglet.clock.unschedule(self.move)
        pyglet.clock.unschedule(self.end_fight)
        self.monsters.remove(self)
        super().delete()

class Armor(Brick):
    def __init__(self, col, row):
        file_name = random.choice(['armor_left.png', 'armor_right.png', 'helmet_left.png', 
                'helmet_right.png', 'legarmor_left.png', 'legarmor_right.png', 'boot_right.png',
                'boot_left.png', 'shield_left.png', 'shield_right.png'])
        super().__init__(pyglet.resource.image(file_name), col, row, group=on_floor)
        
class Sword(Brick):
    def __init__(self,col, row):
        file_name = random.choice(['sword_piece_one.png','sword_piece_two.png','sword_piece_three.png'])
        super().__init__(pyglet.resource.image(file_name), col, row, group=on_floor)

class Chest(Brick):
    STEP = 0.9
    chests = set()
    
    def __init__(self):
        self.chest_image = pyglet.resource.image('chest_close.png')
        super().__init__(self.chest_image)
        self.chests.add(self)
        self.is_open = False
    
        while True:
            col = random.randint(1, self.game.COLUMNS-2)
            row = random.randint(1, self.game.ROWS-2)
            if not self.check_collision(col, row):
                break
        self.col = col
        self.row = row
    
    def open(self):
        if self.is_open:
            return
        self.is_open = True
        self.image = pyglet.resource.image('chest_open.png')
        pyglet.clock.schedule_once(self.end_opening, self.STEP)
        
    def end_opening(self, dt):
        random.choice ([Armor,Sword])(self.col, self.row)
        self.delete()
        
    
    def delete(self):
        pyglet.clock.unschedule(self.end_opening)
        self.chests.remove(self)
        super().delete()
        
class Door(Brick):
    STEP = 0.9
    doors = set()
    
    def __init__(self):
        self.door_image = pyglet.resource.image('trapdoor_close.png')
        super().__init__(self.door_image)
        self.doors.add(self)
        self.is_open = False
    
        while True:
            col = random.randint(1, self.game.COLUMNS-2)
            row = random.randint(1, self.game.ROWS-2)
            if not self.check_collision(col, row):
                break
        self.col = col
        self.row = row
        
    def open(self):
        if self.is_open:
            return
        self.is_open = True
        self.image = pyglet.resource.image('trapdoor_open.png')
        pyglet.clock.schedule_once(self.end_opening, self.STEP)
    
    def end_opening(self, dt):
        self.delete()
        self.game.start_level()
        
    
    def delete(self):
        pyglet.clock.unschedule(self.end_opening)
        self.doors.remove(self)
        super().delete()

UNVISITED, VISITED_FLOOR, VISITED_WALL = range(3)
def generate_dungeon(width, height, start_col, start_row):
    dungeon = [[UNVISITED for row in range(height)] for col in range(width)]
    for row in range(height):
        for col in range(width):
            if (row == 0 or col == 0
                    or row == height-1 or col == width-1):
                dungeon[col][row] = VISITED_WALL

    dungeon[start_col][start_row] = VISITED_FLOOR
    nodes = [(start_col, start_row)]
    while nodes:
        node = col, row = nodes.pop()
        neighbours = [(col-1, row), (col+1, row), (col, row-1), (col, row+1)]
        kinds = {UNVISITED: [], VISITED_FLOOR: [], VISITED_WALL: []}
        for neighbour in neighbours:
            ncol, nrow = neighbour
            kinds[dungeon[ncol][nrow]].append(neighbour)
        
        random.shuffle(kinds[UNVISITED])
        for unvisited in kinds[UNVISITED]:
            ucol, urow = unvisited
            if len(kinds[VISITED_FLOOR]) < 2:
                new_kind = VISITED_FLOOR
            elif not kinds[VISITED_WALL]:
                new_kind = VISITED_WALL
            else:
                new_kind = random.choice([VISITED_FLOOR, VISITED_WALL])

            dungeon[ucol][urow] = new_kind
            kinds[new_kind].append(unvisited)
            if new_kind == VISITED_FLOOR:
                nodes.append(unvisited)
                
    return dungeon
        
    
class Game(pyglet.window.Window):
    STEP = 0.3  # Seconds
    COLUMNS = 32
    ROWS = 18
    HUD_HEIGHT = 50

    def __init__(self):
        super().__init__(resizable=True)
        pyglet.clock.set_fps_limit(60)
        self.batch = pyglet.graphics.Batch()
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.score = 0

        self.label = pyglet.text.Label(
                'Press R to Start', 'Times New Roman', 36,
                color=(255, 0, 0, 255),
                anchor_x='center', anchor_y='center',
                batch=self.batch, group=hud)
        self.level_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='right', anchor_y='bottom',
                batch=self.batch, group=hud)
        self.xp_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='right', anchor_y='top',
                batch=self.batch, group=hud)
        self.health_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='center', anchor_y='bottom',
                batch=self.batch, group=hud)
        self.potion_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='center', anchor_y='top',
                batch=self.batch, group=hud)
        self.armor_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='right', anchor_y='bottom',
                batch=self.batch, group=hud)
        self.sword_label = pyglet.text.Label(
                '', 'Times New Roman', 10,
                color=(255, 255, 0, 255),
                anchor_x='right', anchor_y='top',
                batch=self.batch, group=hud)

        self.back_image = pyglet.resource.image('background.png')
        self.back = pyglet.sprite.Sprite(
                self.back_image, batch=self.batch, group=back_image)

        self.ground_image = pyglet.resource.image('ground.png')
        self.brick_image = pyglet.resource.image('wall.png')
        Brick.game = self  # Set up globally used game object
        
        self.hero = None


    def start_game(self):

        if self.hero:
            self.hero.delete()
        self.hero = Hero()
       
        
    def start_level(self):
        for brick in list(Brick.bricks):
            if not isinstance(brick, Hero):
                brick.delete()
    
        dungeon = generate_dungeon(self.COLUMNS, self.ROWS, self.hero.col, self.hero.row)
    
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if dungeon[col][row] == VISITED_FLOOR:
                    log.debug("Floor")
                    Floor(self.ground_image, col, row, group=background)
                else:
                    log.debug("Wall")
                    Wall(self.brick_image, col, row, group=background)
       
        for x in range(random.randint(3,9)):
            Monster()
            
        for x in range(random.randint(1,3)):
            Chest()

        for x in range(1):
            Door()       
        
        pyglet.clock.unschedule(self.update)
        pyglet.clock.tick()
        pyglet.clock.schedule(func=self.update)
        self.label.text = ""
        self.time = 0.0
        self.set_label_text()

    def set_label_text(self):
        self.level_label.text = "LEVEL: %s" % (self.hero.level)
        self.xp_label.text = "XP: %s / %s" % (self.hero.xp, self.hero.level**2 * 10 - self.hero.xp)
        self.health_label.text = "HP: %s / %s" % (self.hero.health, self.hero.max_health)
        self.potion_label.text = "POTIONS: %s" % (self.hero.potion)
        self.sword_label.text = "SWORD PIECES: %s / %s" % (self.hero.sword, self.hero.max_sword)
        self.armor_label.text = "ARMOR PIECES: %s / %s" % (self.hero.armor, self.hero.max_armor)

    def set_score(self, v):
        self.score = v
        self.score_label.text = str(self.score)


    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.back.scale = max(
                width / self.back_image.width, height / self.back_image.height)

        self.brick_px = min(width / self.COLUMNS, (height - self.HUD_HEIGHT) / self.ROWS)
        self.brick_scale = self.brick_px / self.brick_image.width
        self.base_x = (width - self.brick_px * self.COLUMNS) / 2
        self.base_y = height - (height - self.brick_px * self.ROWS + self.HUD_HEIGHT) / 2

        self.label.x = self.width // 2
        self.label.y = self.height // 2

        self.level_label.x = self.width // 6
        self.level_label.y = self.base_y + self.HUD_HEIGHT // 2

        self.xp_label.x = self.width // 6
        self.xp_label.y = self.base_y + self.HUD_HEIGHT // 2

        self.health_label.x = self.width // 2
        self.health_label.y = self.base_y + self.HUD_HEIGHT // 2

        self.potion_label.x = self.width // 2
        self.potion_label.y = self.base_y + self.HUD_HEIGHT // 2

        self.sword_label.x = self.width // 1.1
        self.sword_label.y = self.base_y + self.HUD_HEIGHT // 2

        self.armor_label.x = self.width // 1.1
        self.armor_label.y = self.base_y + self.HUD_HEIGHT // 2

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
            self.start_game()
            self.start_level()


    def update(self, dt):
        pass


if __name__ == "__main__":
    pyglet.resource.path = ['res']
    pyglet.resource.reindex()
    window = Game()
pyglet.app.run()
