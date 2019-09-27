import sys
import math
from copy import deepcopy


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

    def clear_radar(self):
        if self.radar == 1:
            self.radar = 0
            return True

    def is_safe(self):
        if self.hole and not self.we_dug:
            if self.x == 12 and self.y == 8:
                log('cell (12,8) is NOT safe')
            return False
        if self.x == 12 and self.y == 8:
            log('cell (12,8) is safe')
        return True

    def ore_left(self):
        return int(self.ore) if self.ore != '?' else -1

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
                if cell.ore not in {'?', '0'} and not cell.has_trap():
                    coords.append(cell)
        return coords

    def get_blind_dig_cells(self, restrict=1):
        cells = list()
        for row in self.grid:
            for cell in row[restrict:]:
                if not cell.hole and cell.ore == '?' and not cell.has_trap():
                    cells.append(cell)
        return cells

    def get_trap_candidate_coords(self):
        candidates = list()
        for row in self.grid:
            for cell in row:
                if not cell.we_dug and cell.ore_left() > 1 and not cell.has_trap() and cell.is_safe():
                    candidates.append(cell)

        return candidates


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

        self.dead = False

    def has_radar(self):
        return self.item == 2

    def has_trap(self):
        return self.item == 3

    def has_ore(self):
        return self.item == 4


# GLOBAL PARAMS

# remaining_radar_placements = [(5, 3), (5, 11), (10, 7), (15, 11), (15, 3), (20, 7), (25, 3), (25, 11), (20, 0), (20, 14), (29, 7),
#                     (10, 0), (10, 14), (20, 0), (20, 14), (0, 7)]

remaining_radar_placements = [(10, 7), (15, 11), (15, 3), (20, 7), (25, 3), (25, 11), (20, 0), (20, 14),
                              (10, 0), (10, 14), (29, 7), (20, 0), (20, 14), (5, 3), (5, 11), (0, 7)]

# alternative config:
# remaining_radar_placements = [(10, 3), (10, 11), (15, 7), (20, 3), (20, 11), (15, 0), (15, 14), (25, 7),
#                              (5, 7), (27, 2), (27, 12)]

# x value to shift radar pos by
shift_x = 0
if shift_x != 0:
    for i, coord in enumerate(remaining_radar_placements):
        remaining_radar_placements[i] = (min(coord[0] + shift_x, 29), coord[1])

all_radar_placements = deepcopy(remaining_radar_placements)

ore_remaining_radar_threshold = 15
trap_placement_turn_threshold = 150
early_blind_dig_column_restrict = 3
early_blind_dig_turns = 2


def command_robot(robot, ore_cells, radar_cooldown, trap_cooldown, game_map, radar_requested, trap_requested, turn):

    # counting ores visible (and not trapped)
    num_ore_available = 0
    for cell in ore_cells:
        if not cell.has_trap():
            num_ore_available += int(cell.ore)

    cmd_given = None

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
            if radar_cooldown == 0 and len(remaining_radar_placements) and not radar_requested \
                    and num_ore_available < ore_remaining_radar_threshold:
                robot.task = 'RADAR'
                robot.target_x, robot.target_y = remaining_radar_placements.pop(0)
                task_assigned = True
            # check if trap is available
            elif trap_cooldown == 0 and not trap_requested and turn <= trap_placement_turn_threshold:
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
        if not robot.has_trap():
            cmd_given = 'REQUEST TRAP'
        else:
            my_cell = game_map.get_cell(robot.x, robot.y)
            trap_candidate_coords = game_map.get_trap_candidate_coords()
            if trap_candidate_coords:
                closest_coord = findClosestOre(my_cell, trap_candidate_coords)
                cmd_given = 'DIG {} {}'.format(closest_coord.x, closest_coord.y)
            else:
                dig_cell = blind_dig(robot, game_map)
                if dig_cell:
                    cmd_given = 'DIG {} {}'.format(dig_cell.x, dig_cell.y)

    elif robot.task == 'ORE':
        my_cell = game_map.get_cell(robot.x, robot.y)
        # find closest ore
        if len(ore_cells):
            closest_ore = findClosestSafeOre(my_cell, ore_cells)

            if closest_ore:  # close safe ore exists
                cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)
                closest_ore.we_dug = True
            else:
                print('ore exists but closest safe ore is none - trying a risky one', file=sys.stderr)
                # try a risky one
                closest_ore = findClosestOre(my_cell, ore_cells)
                cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)

        # no (safe) ore found - blind dig
        if not cmd_given:
            if not radar_cooldown:  # no ore, and no radar placement right now
                robot.task = "RETURN"
            else:
                print('trying blind dig', file=sys.stderr)
                dig_cell = blind_dig(robot, game_map, turn)
                if dig_cell:
                    cmd_given = 'DIG {} {}'.format(dig_cell.x, dig_cell.y)

    if robot.task == 'RETURN':
        cmd_given = 'MOVE 0 {}'.format(robot.y)

    if not cmd_given:
        # temp - return to base
        # cmd_given = 'MOVE 0 {}'.format(robot.y)
        cmd_given = 'WAIT'
        robot.task = None

    return cmd_given


def blind_dig(robot, game_map, turn):
    """
    Find closest safe cell to try blind dig
    :param robot:
    :param game_map:
    :return:
    """

    # try to dig further in on first 2 turns
    restrict_columns = early_blind_dig_column_restrict if turn < early_blind_dig_turns else 1

    safe_cells = game_map.get_blind_dig_cells(restrict_columns)
    if safe_cells:
        robot_cell = game_map.get_cell(robot.x, robot.y)
        closest = safe_cells[0]
        for cell in safe_cells:
            if manhattanDistance(cell, robot_cell) < manhattanDistance(closest, robot_cell):
                closest = cell
        return closest
    print('tried blind dig but no safe cells, len = {}'.format(len(safe_cells)), file=sys.stderr)
    return None


def findClosestOre(cell, ore_cells):
    """
    Find closest ore (not sure if safe) - assumes there are visible ore cells
    :param cell: grid location x,y
    :param ore_cells: list cells with visible ores
    :return: return closest cell with ore
    """
    closest = ore_cells[0]
    for ore_cell in ore_cells:
        if manhattanDistance(cell, ore_cell) < manhattanDistance(cell, closest):
            closest = ore_cell
    return closest


def findClosestSafeOre(cell, ore_cells):
    """
    Find closest safe ore - assumes there are visible ore cells
    :param cell:
    :param ore_cells:
    :return: Closest safe ore if exists, else None
    """
    closest = None
    for ore_cell in ore_cells:
        if ore_cell.is_safe():
            if not closest:
                closest = ore_cell
            elif manhattanDistance(cell, ore_cell) < manhattanDistance(cell, closest):
                closest = ore_cell
    return closest


def manhattanDistance(c1, c2):
    return abs(c1.x - c2.x) + abs(c1.y - c2.y)


# return list of robots within dist of a given coord
def robots_within_distance(robots, coord, dist):
    for robot in robots.values():
        if manhattanDistance((robot.x, robot.y), coord) < dist:
            yield robot


# MAIN

# setup game map
width, height = [int(i) for i in input().split()]
turn = 0
game_map = GameMap(width, height)

my_robots = {}
opp_robots = {}

# game loop
while True:
    # my_score: Amount of ore delivered
    my_score, opponent_score = [int(i) for i in input().split()]
    had_radar = list()
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

            # clear radar - keep track of which cells did have radar before
            if game_map.grid[i][j].clear_radar():
                had_radar.append(game_map.grid[i][j])

    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, radar_cooldown, trap_cooldown = [int(i) for i in input().split()]

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
                    if x == -1 and y == -1:
                        my_robots[id].dead = True
                else:
                    my_robots[id] = robot

                # log(id)
            else:
                if id in opp_robots:
                    opp_robots[id].x = x
                    opp_robots[id].y = y
                    opp_robots[id].item = item
                    opp_robots[id].id = id
                    if x == -1 and y == -1:
                        opp_robots[id].dead = True
                else:
                    opp_robots[id] = robot 

        # Radars
        elif type == 2:
            radar_cell = game_map.get_cell(x, y).radar = 1

        # Traps
        elif type == 3:
            game_map.get_cell(x, y).trap = 1

    # check for radars lost
    for cell in had_radar:
        if not cell.has_radar():
            remaining_radar_placements.insert(0, (cell.x, cell.y))
            log('lost radar at ({},{}) reinserted'.format(cell.x, cell.y))

    ore_cells = game_map.get_ore_cells()
    radar_requested, trap_requested = False, False

    for id, robot in my_robots.items():
        if not robot.dead:
            command = command_robot(robot, ore_cells, radar_cooldown, trap_cooldown, game_map,
                                    radar_requested, trap_requested, turn)

            if command == 'REQUEST RADAR':
                radar_requested = True
            elif command == 'REQUEST TRAP':
                trap_requested = True

            command += ' {}'.format(robot.task)
            print(command)
        else:
            print('WAIT DEAD')

    turn += 1
