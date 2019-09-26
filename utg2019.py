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

    def is_safe(self):
        if self.hole and not self.we_dug:
            return False
        return True

    def __repr__(self):
        return "({},{}):[{},{}]".format(self.x, self.y, self.ore, self.hole)


class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = list()
        for i in range(height):
            row = list()
            for j in range(width):
                row.append(Cell(j, i))
            self.grid.append(row)

    def __repr__(self):
        return self.grid

    def valid_coords(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height

    def get_cell(self, x, y):
        return self.grid[y][x]

    def get_ore_cells(self):
        coords = list()
        for row in self.grid:
            for cell in row:
                if cell.ore not in {'?', '0'}:
                    coords.append(cell)
        return coords

    def get_blind_dig_cells(self):
        cells = list()
        for row in self.grid:
            for cell in row[1:]:
                if not cell.hole and cell.ore == '?':
                    cells.append(cell)
        return cells

class Robot:
    def __init__(self, x, y, item, id):
        self.x = x
        self.y = y
        self.item = item
        self.id = id

        self.task = None
        self.target_x = None
        self.target_y = None
        self.collected_item = False

        # self.last_command = 'NONE'
        # self.last_command_x = 0
        # self.last_command_y = 0

    def has_radar(self):
        return self.item == 2

    def has_trap(self):
        return self.item == 3

    def has_ore(self):
        return self.item == 4


# radar_placements = [(9,7), (4,11), (4, 3), (14, 2), (14, 12), (20, 6), (26, 2), (25, 10)]
# radar_placements = [(9,7), (14, 2), (14, 12), (20, 6), (26, 2), (25, 10)]
remaining_radar_placements = [(5, 3), (5, 11), (10, 7), (15, 11), (15, 3), (20, 7), (25, 3), (25, 11), (20, 0), (20, 14), (29, 7),
                    (10, 0), (10, 14), (20, 0), (20, 14), (0, 7)]
all_radar_placements = remaining_radar_placements

def command_robot_2(robot, ore_cells, radar_count, radar_cooldown, trap_cooldown, game_map, radar_requested, trap_requested):

    # counting ores visible
    num_ore_available = 0
    for cell in ore_cells:
        num_ore_available += int(cell.ore)

    # checking to see if radar was destroyed
    for (coords in all_radar_placements):
        if (not game_map.get_cell(coords[0], coords[1]).has_radar() and
            not coords in remaining_radar_placements):
            remaining_radar_placements.insert(0, coords)
    cmd_given = None

    placing_traps = False

    # Clear item placement tasks
    if (robot.collected_item and ((robot.task == 'RADAR' and not robot.has_radar()) or
                                  (robot.task == 'TRAP' and not robot.has_trap())))\
            or (robot.task == 'RETURN' and robot.x == 0):
        print('clearing task: has_radar = {}'.format(robot.has_radar()), file=sys.stderr)
        robot.task = None
        robot.collected_item = False
        robot.target_x, robot.target_y = None, None

    elif robot.has_ore():
        robot.task = 'RETURN'

    # Robot doesn't have a task, assign a new one
    if not robot.task:
        # Check item tasks if robot is in HQ
        task_assigned = False
        if robot.x == 0:
            # check if radar is available
            if radar_cooldown == 0 and len(remaining_radar_placements) and not radar_requested and num_ore_available < 10:
                robot.task = 'RADAR'
                robot.target_x, robot.target_y = remaining_radar_placements.pop(0)
                task_assigned = True
            # check if trap is available
            elif placing_traps and trap_cooldown == 0 and not trap_requested:
                robot.task = 'TRAP'
                task_assigned = True
        # go and get some ore
        if not task_assigned:
            robot.task = 'ORE'

    # Perform tasks
    if robot.task == 'RADAR':
        # Robot doesn't have radar - request
        if not robot.has_radar():
            cmd_given = 'REQUEST RADAR'
            robot.collected_item = True

        # Robot has radar - proceed to target
        else:
            cmd_given = 'DIG {} {}'.format(robot.target_x, robot.target_y)
            game_map.get_cell(robot.target_x, robot.target_y).we_dug = True

    elif robot.task == 'TRAP':
        print('ERROR: trap placement not ready yet', file=sys.stderr)

    elif robot.task == 'ORE':
        my_cell = game_map.get_cell(robot.x, robot.y)
        # find closest ore
        if len(ore_cells):
            # print('{} ore cells visible'.format(len(ore_cells)), file=sys.stderr)
            closest_ore = findClosestSafeOre(my_cell, ore_cells)
            # closest_ore = findClosestOre(my_cell, ore_cells)

            if closest_ore:  # close safe ore exists
                cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)
                closest_ore.we_dug = True
            else:
                print('ore exists but closest safe ore is none :(', file=sys.stderr)
                # try a risky one
                closest_ore = findClosestOre(my_cell, ore_cells)
                cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)

        # no (safe) ore found - blind dig
        if not cmd_given:
            print('trying blind dig', file=sys.stderr)
            dig_cell = blind_dig(robot, game_map)
            if dig_cell:
                cmd_given = 'DIG {} {}'.format(dig_cell.x, dig_cell.y)

    elif robot.task == 'RETURN':
        cmd_given = 'MOVE 0 {}'.format(robot.y)

    if not cmd_given:
        # print('ERROR: how did we get here? * no safe blind digs?')
        # temp - return to base
        # cmd_given = 'MOVE 0 {}'.format(robot.y)
        cmd_given = 'WAIT'
        robot.task = None

    return cmd_given


def blind_dig(robot, game_map):
    safe_cells = game_map.get_blind_dig_cells()
    if safe_cells:
        robot_cell = game_map.get_cell(robot.x, robot.y)
        closest = safe_cells[0]
        for cell in safe_cells:
            if manhattanDistance(cell, robot_cell) < manhattanDistance(closest, robot_cell):
                closest = cell
        return closest
    print('tried blind dig but no safe cells, len = {}'.format(len(safe_cells)), file=sys.stderr)
    return None

# assume there are visible ores
# @param cell a grid location with x and y
# @param ore_coords list of tuples of visible ores
# returns closest (x, y) coordinate with ore
def findClosestOre(cell, ore_cells):
    closest = ore_cells[0]
    for ore_cell in ore_cells:
        if (manhattanDistance(cell, ore_cell) < manhattanDistance(cell, closest)):
            closest = ore_cell
    return closest

# assume there are visible ores
# @param cell a grid location with x and y
# @param ore_coords list of tuples of visible ores
# returns closest (x, y) coordinate with ore that was not an enemy hole
def findClosestSafeOre(cell, ore_cells):
    closest = None
    for ore_cell in ore_cells:
        if ore_cell.is_safe():
            if not closest:
                closest = ore_cell
            elif manhattanDistance(cell, ore_cell) < manhattanDistance(cell, closest) and ore_cell.is_safe():
                closest = ore_cell
    return closest


def manhattanDistance(c1, c2):
    return abs(c1.x - c2.x) + abs(c1.y - c2.y)

# return list of robots within dist of a given coord
def robots_within_distance(robots, coord, dist):
    for robot in robots.values():
        if manhattanDistance((robot.x, robot.y), coord) < dist:
            yield robot

# Deliver more ore to hq (left side of the map) than your opponent. Use radars to find ore but beware of traps!

########### MAIN ##########
# setup game map
width, height = [int(i) for i in input().split()]
turn = 0
game_map = GameMap(width, height)
# print(str(game_map.grid), file=sys.stderr)
# ore = [['?' for i in range(width)] for j in range(height)]
# print(ore, file=sys.stderr)

my_robots = {}
opp_robots = {}

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
    for i in range(entity_count):
        id, type, x, y, item = [int(j) for j in input().split()]

        if type in {0, 1}:
            robot = Robot(x, y, item, id)
            if type == 0:
                if id in my_robots:  # Robot already exists
                    my_robots[id].x = x
                    my_robots[id].y = y
                    my_robots[id].item = item
                    my_robots[id].id = id
                else:
                    my_robots[id] = robot

                # log(id)
            else:
                if id in opp_robots:
                    opp_robots[id].x = x
                    opp_robots[id].y = y
                    opp_robots[id].item = item
                    opp_robots[id].id = id
                else:
                    opp_robots[id] = robot 

        # Radars
        elif type == 2:
            game_map.get_cell(x, y).radar = 1
            radar_count += 1

        # Traps
        elif type == 3:
            game_map.get_cell(x, y).trap = 1

    ore_cells = game_map.get_ore_cells()
    radar_requested, trap_requested = False, False

    for id, robot in my_robots.items():
        command = command_robot_2(robot, ore_cells, radar_count, radar_cooldown, trap_cooldown, game_map,
                                  radar_requested, trap_requested)

        if command == 'REQUEST RADAR':
            radar_requested = True
        elif command == 'REQUEST TRAP':
            trap_requested = True

        command += ' {}'.format(robot.task)
        print(command)

    turn += 1
