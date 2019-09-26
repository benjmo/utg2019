import sys
import math


def log(message):
    print(message, file=sys.stderr)


class Cell:
    def __init__(self, x, y, ore='?', hole=0):
        self.x = x
        self.y = y
        self.ore = ore
        self.hole = hole
        self.we_dug = False

        # items: 0 = none, 1 = ours, 2 = opponent
        self.trap = 0
        self.radar = 0

    def has_trap(self):
        return self.trap > 0

    def has_radar(self):
        return self.radar > 0

    def clear_trap(self):
        if self.trap == 1:
            self.trap = 0

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

    def get_cell(self, x, y):
        return self.grid[y][x]

    def get_ore_coordinates(self):
        coords = list()
        for row in self.grid:
            for cell in row:
                if cell.ore not in {'?', '0'}:
                    coords.append((cell.x, cell.y))
        return coords


class Robot:
    def __init__(self, x, y, item, id):
        self.x = x
        self.y = y
        self.item = item
        self.id = id

    def has_radar(self):
        return self.item == 2

    def has_trap(self):
        return self.item == 3

    def has_ore(self):
        return self.item == 4


########### MAIN ##########
# setup game map
width, height = [int(i) for i in input().split()]
turn = 0
game_map = GameMap(width, height)
# print(str(game_map.grid), file=sys.stderr)
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
            currOre = inputs[2*j]
            game_map.grid[i][j].ore = currOre

            # hole: 1 if cell has a hole
            hole = int(inputs[2*j+1])
            game_map.grid[i][j].hole = hole

            # clear trap info
            game_map.grid[i][j].clear_trap()

    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, radar_cooldown, trap_cooldown = [int(i) for i in input().split()]

    radar_count = 0
    # Create/update entities
    my_robots = list()
    opp_robots = list()
    for i in range(entity_count):
        # id: unique id of the entity
        # type: 0 for your robot, 1 for other robot, 2 for radar, 3 for trap
        # y: position of the entity
        # item: if this entity is a robot, the item it is carrying (-1 for NONE, 2 for RADAR, 3 for TRAP, 4 for ORE)
        id, type, x, y, item = [int(j) for j in input().split()]

        if type in {0, 1}:
            robot = Robot(x, y, item, id)
            if type == 0:
                # our alive robots
                my_robots.append(robot)
            else:
                opp_robots.append(robot)

        # Radars
        elif type == 2:
            game_map.get_cell(x, y).radar = 1
            radar_count += 1

        # Traps
        elif type == 3:
            game_map.get_cell(x, y).trap = 1

    ore_coords = game_map.get_ore_coordinates()
    for position, curr_robot in enumerate(my_robots):
        command_robot(curr_robot, position, ore_coords, radar_count)
    turn += 1


def command_robot(robot, position, ore_coords, radar_count):
    cmd_given = False

    # initial setup for middle robot - get radar and plant in middle
    if position == 2:
        if turn == 0:
            print('REQUEST RADAR')
            cmd_given = True
        elif robot.has_radar():
            print('DIG 15 8')
            cmd_given = True
            game_map.get_cell(15, 8).we_dug = True

    if position == 3:
        # wait until we can get a radar then place it at coords
        if (not robot.has_radar() and radar_count < 2):
            print("REQUEST RADAR")
            cmd_given = True
        elif:
            print('DIG 7 8')
            cmd_given = True

    if not cmd_given:
        # has ore, return to base
        if robot.has_ore():
            print('MOVE 0 {}'.format(robot.y))
        # no ore, search for some
        elif len(ore_coords):
            x, y = ore_coords.pop()
            print('DIG {} {}'.format(x, y))
            game_map.get_cell(15, 8).we_dug = True
        # no ore known at the moment, wait in the middle
        else:
            print('MOVE 15 8')