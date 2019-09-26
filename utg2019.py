import sys
import math

def log(print):
    print(print, file=sys.stderr)

class Cell:
    def __init__(self, x, y, ore='?', hole=0):
        self.x = x
        self.y = y
        self.ore = ore
        self.hole = hole

    def __repr__(self):
        return "({},{}):[{},{}]".format(self.x, self.y, self.ore, self.hole)

class GameMap:
    def __init__(self, width, height):
        self.grid = list()
        for i in range(height):
            row = list()
            for j in range(width):
                row.append(Cell(j, i))
            self.grid.append(row)

    def __repr__(self):
        return self.grid

    def get_ore_coordinates(self):
        coords = list()
        for row in self.grid:
            for cell in row:
                if cell.ore not in {'?', '0'}:
                    coords.append((cell.x, cell.y))
        return coords

class Robot:
    def __init__(self, x, y, item):
        self.x = x
        self.y = y
        self.item = item

    def has_radar(self):
        return (item == 2)

    def has_trap(self):
        return (item == 3)

    def has_ore(self):
        return (item == 4)

# Deliver more ore to hq (left side of the map) than your opponent. Use radars to find ore but beware of traps!

# height: size of the map
width, height = [int(i) for i in input().split()]
turn = 0
game_map = GameMap(width, height)

# ore = [['?' for i in range(width)] for j in range(height)]
# print(ore, file=sys.stderr)

# game loop
while True:
    # my_score: Amount of ore delivered
    my_score, opponent_score = [int(i) for i in input().split()]
    for i in range(height):
        inputs = input().split()
        for j in range(width):
            # ore: amount of ore or "?" if unknown
            # hole: 1 if cell has a hole
            currOre = inputs[2*j]
            game_map.grid[height][width] = currOre
            hole = int(inputs[2*j+1])
            game_map.grid[height][width] = hole

    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, radar_cooldown, trap_cooldown = [int(i) for i in input().split()]

    my_robots = list()
    opp_robots = list()
    for i in range(entity_count):
        # id: unique id of the entity
        # type: 0 for your robot, 1 for other robot, 2 for radar, 3 for trap
        # y: position of the entity
        # item: if this entity is a robot, the item it is carrying (-1 for NONE, 2 for RADAR, 3 for TRAP, 4 for ORE)
        id, type, x, y, item = [int(j) for j in input().split()]

        if type in {0, 1}:
            robot = Robot(x, y, item)
            if type == 0:
                my_robots.append(robot)
            else:
                opp_robots.append(robot)
        assert(len(my_robots) == 5)

        # print("{} {} {} {} {}".format(id, type, x, y, item), file=sys.stderr)

    ore_coords = game_map.get_ore_coordinates()
    for i in range(5):
        curr_robot = my_robots[i]
        cmd_given = False

        # initial setup for middle robot - get radar and plant in middle
        if i == 2:
            if turn == 0:
                print('REQUEST RADAR')
                cmd_given = True
            elif curr_robot.has_radar():
                print('DIG 15 8')
                cmd_given = True

        if not cmd_given:
            # has ore, return to base
            if curr_robot.has_ore():
                print('MOVE 0 {}'.format(curr_robot.y))

            # no ore, search for some
            if len(ore_coords):
                x, y = ore_coords.pop()
                print('DIG {} {}'.format(x, y))

            # no ore known at the moment, wait in the middle
            else:
                print('MOVE 15 8')

    turn += 1