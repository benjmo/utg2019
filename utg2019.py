import sys
import math
from copy import deepcopy


def log(message):
    print(message, file=sys.stderr)


class Cell:
    def __init__(self, x, y, ore=-1, hole=0):
        self.x = x
        self.y = y
        self.ore = ore
        self.hole = hole
        self.we_dug = False
        self.turn_dug = -1

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
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cell(self, x, y):
        return self.grid[y][x]

    def get_ore_cells(self):
        coords = list()
        for row in self.grid:
            for cell in row:
                if cell.ore > 0 and not cell.has_trap():
                    coords.append(cell)
        return coords

    def get_blind_dig_cells(self, restrict=1):
        cells = list()
        for row in self.grid:
            for cell in row[restrict:]:
                if not cell.hole and cell.ore == -1 and not cell.has_trap():
                    cells.append(cell)
        return cells

    def get_trap_candidate_coords(self):
        candidates = list()
        for row in self.grid:
            for cell in row:
                if not cell.we_dug and cell.ore > 1 and not cell.has_trap() and cell.is_safe():
                    candidates.append(cell)

        return candidates

    def check_first_column_trapped(self, game_state):
        # after certain period, or we already lost bots, assume trap isn't there
        if game_state.turn > turns_to_check_trap or game_state.num_my_bots_alive < bots_alive_to_check_trap:
            game_state.first_col_trapped.clear()
            return

        # assume that if trap was there before, and above not met, trap is still there
        elif len(game_state.first_col_trapped):
            return

        # is opp just blind digging?
        num_cells_opp_dug = 0

        # danger rows
        start_trap, end_trap = estimated_first_column_trap_rows
        opp_dug_in_trap_range = 0
        danger_rows = set()
        prev_cell_dug = False

        # iterate over first cell in each row
        for rownum, row in enumerate(self.grid):
            first_cell = row[0]

            # opp dug this hole
            if first_cell.hole and not first_cell.we_dug:
                num_cells_opp_dug += 1

                # how many consecutive cells dug by opp in expected trap rows
                if start_trap <= rownum <= end_trap:
                    if prev_cell_dug or rownum == start_trap:
                        opp_dug_in_trap_range += 1
                        danger_rows.add(rownum)
                    else:
                        opp_dug_in_trap_range = 0
                        danger_rows.clear()

                prev_cell_dug = True
            elif first_cell.has_trap():  # we contributed to the chain of traps
                prev_cell_dug = True
            else:
                prev_cell_dug = False

        # not a trap
        if num_cells_opp_dug >= first_column_blind_dig_threshold \
                or opp_dug_in_trap_range <= estimated_first_column_trap_size:
            danger_rows.clear()
        else:
            # consider full trap range
            danger_rows.add(min(danger_rows) - 1)
            danger_rows.add(max(danger_rows) + 1)

        game_state.first_col_trapped = danger_rows


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


class GameState:
    def __init__(self):
        self.turn = 0
        self.my_score = 0
        self.opp_score = 0
        self.radar_cooldown = 0
        self.trap_cooldown = 0
        self.radar_requested = 0
        self.trap_requested = 0
        self.ore_available = 0
        self.turns_since_trap_avail = 0
        self.next_radar_coords = None
        self.num_bots_moving_to_radar = 0
        self.first_col_trapped = set()
        self.my_bots_alive = 5

    def update_turns_since_trap(self):
        # set turns since trap
        if self.trap_cooldown == 0:
            self.turns_since_trap_avail += 1
        else:
            self.turns_since_trap_avail = -1

    def radar_ready(self):
        return self.radar_cooldown == 0 \
               and not self.radar_requested \
               and len(remaining_radar_placements) \
               and self.ore_available < ore_remaining_radar_threshold

    def trap_ready(self):
        return self.trap_cooldown == 0 \
               and not self.trap_requested \
               and self.turns_since_trap_avail >= wait_turns_after_trap_cooldown \
               and self.turn < trap_placement_turn_threshold

    def should_move_to_radar(self):
        return self.next_radar_coords and self.turn < move_to_radar_turn_threshold \
               and self.num_bots_moving_to_radar < max_bots_moving_to_radar


# GLOBAL PARAMS

# HARDCODED RADAR PLACEMENTS
# remaining_radar_placements = [(5, 3), (5, 11), (10, 7), (15, 11), (15, 3), (20, 7), (25, 3), (25, 11), (20, 0), (20, 14), (29, 7),
#                     (10, 0), (10, 14), (20, 0), (20, 14), (0, 7)]
remaining_radar_placements = [(10, 7), (15, 11), (15, 3), (20, 7), (25, 3), (25, 11), (20, 0), (20, 14),
                              (10, 0), (10, 14), (29, 7), (20, 0), (20, 14), (5, 3), (5, 11), (0, 7)]
# alternative config:
# remaining_radar_placements = [(10, 3), (10, 11), (15, 7), (20, 3), (20, 11), (15, 0), (15, 14), (25, 7),
#                              (5, 7), (27, 2), (27, 12)]


# SHIFT RADAR PLACEMENTS
shift_x = 0 # x value to shift radar pos by
if shift_x != 0:
    for i, coord in enumerate(remaining_radar_placements):
        remaining_radar_placements[i] = (min(coord[0] + shift_x, 29), coord[1])

all_radar_placements = deepcopy(remaining_radar_placements)

# NUM ORE REMAINING BEFORE SETTING NEW RADAR
ore_remaining_radar_threshold = 15

# STOP PLACING TRAPS AFTER TURN X
trap_placement_turn_threshold = 150

# DON'T DIG IN FIRST X COLUMNS FOR FIRST Y TURNS
early_blind_dig_column_restrict = 3
early_blind_dig_turns = 2

# DON'T SEND BOTS TO SAME ORE, EVEN IF >1 ORE LEFT
send_bots_to_different_ore = False

# EXTRA TURNS TO WAIT BETWEEN REQUESTING TRAP
wait_turns_after_trap_cooldown = 2

# MOVE TO NEXT RADAR DURING FIRST X TURNS
move_to_radar_turn_threshold = 50
max_bots_moving_to_radar = 2

# PREDICT WHETHER FIRST COLUMN TRAPPED
trap_avoidance_active = False
estimated_first_column_trap_rows = (5, 9)
estimated_first_column_trap_size = 3
first_column_blind_dig_threshold = 7  # if more than x cells in first column dug, assume it was just blind digging
turns_to_check_trap = 50
bots_alive_to_check_trap = 4


def update_task(robot, game_state):
    # Clear item placement tasks
    if (robot.collected_item and ((robot.task == 'RADAR' and not robot.has_radar()) or
                                  (robot.task == 'TRAP' and not robot.has_trap())))\
            or (robot.task == 'RETURN' and robot.x == 0):

        # clear game state vars
        if robot.task == 'RADAR':
            game_state.next_radar_coords = None

        # clear robot task
        print('Task complete - clearing'.format(robot.has_radar()), file=sys.stderr)
        robot.task = None
        robot.collected_item = False
        robot.target_x, robot.target_y = None, None

    elif robot.has_ore():
        robot.task = 'RETURN'

    if not robot.task:
        # Check item tasks if robot is in HQ
        task_assigned = False
        if robot.x == 0:
            # check if radar is available
            if game_state.radar_ready():
                robot.task = 'RADAR'
                robot.target_x, robot.target_y = remaining_radar_placements.pop(0)
                task_assigned = True
                game_state.next_radar_coords = (robot.target_x, robot.target_y)
            # check if trap is available
            elif game_state.trap_ready():
                robot.task = 'TRAP'
                task_assigned = True
        # go and get some ore
        if not task_assigned:
            robot.task = 'ORE'


def place_radar(robot, game_state):
    cmd_given = None
    # Robot doesn't have radar - request
    if not robot.has_radar():
        cmd_given = 'REQUEST RADAR'
        robot.collected_item = True
        game_state.radar_requested = True

    # Robot has radar - proceed to target
    else:
        cmd_given = 'DIG {} {}'.format(robot.target_x, robot.target_y)
        game_map.get_cell(robot.target_x, robot.target_y).we_dug = True

    return cmd_given


def place_trap(robot, game_map, game_state):
    cmd_given = None
    if not robot.has_trap():
        cmd_given = 'REQUEST TRAP'
        game_state.trap_requested = True
    else:
        my_cell = game_map.get_cell(robot.x, robot.y)
        trap_candidate_coords = game_map.get_trap_candidate_coords()
        if trap_candidate_coords:
            closest_coord = find_closest_ore(my_cell, trap_candidate_coords)
            cmd_given = 'DIG {} {}'.format(closest_coord.x, closest_coord.y)
        else:
            dig_cell = blind_dig(robot, game_map, game_state.turn)
            if dig_cell:
                cmd_given = 'DIG {} {}'.format(dig_cell.x, dig_cell.y)
    return cmd_given


def find_ore(robot, ore_cells, game_map, game_state):
    cmd_given = None
    my_cell = game_map.get_cell(robot.x, robot.y)
    # find closest ore
    if len(ore_cells):
        closest_ore = find_closest_safe_ore(my_cell, ore_cells)

        if closest_ore:  # close safe ore exists
            cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)
            closest_ore.we_dug = True
        else:
            print('ore exists but closest safe ore is none - trying a risky one', file=sys.stderr)
            # try a risky one
            closest_ore = find_closest_ore(my_cell, ore_cells)
            cmd_given = 'DIG {} {}'.format(closest_ore.x, closest_ore.y)

        # try to send bots to different ores
        # (doesn't matter if we don't dig it this turn - map is refreshed each turn)
        if send_bots_to_different_ore:  # no bots to same ore
            closest_ore.ore = 0
        else:  # decrement count so other bots don't target empty ore
            closest_ore.ore -= 1

        # remove empty ore from list
        if closest_ore.ore == 0:
            ore_cells.remove(closest_ore)

    # no (safe) ore found - blind dig
    if not cmd_given:
        if game_state.radar_ready():  # no ore, and no radar placement right now
            robot.task = "RETURN"
        else:
            # inside early game window, move towards next radar placement
            if game_state.should_move_to_radar():
                log('moving to next radar location')
                move_x, move_y = game_state.next_radar_coords
                cmd_given = 'MOVE {} {}'.format(move_x, move_y)
                game_state.num_bots_moving_to_radar += 1
            else:
                log('trying blind dig')
                dig_cell = blind_dig(robot, game_map, game_state.turn)
                if dig_cell:
                    cmd_given = 'DIG {} {}'.format(dig_cell.x, dig_cell.y)
    return cmd_given


def return_to_base(robot, game_state):
    cmd_given = None
    if trap_avoidance_active \
            and len(game_state.first_col_trapped) \
            and robot.y in game_state.first_col_trapped:  # bot would return to danger zone
        middle_trap_row = int((min(game_state.first_col_trapped) + max(game_state.first_col_trapped)) / 2)
        # below the middle of trap, go to first safe row below
        if robot.y > middle_trap_row:
            cmd_given = 'MOVE 0 {}'.format(max(game_state.first_col_trapped) + 1)
        # above the middle of trap, go to first safe row above
        else:
            cmd_given = 'MOVE 0 {}'.format(min(game_state.first_col_trapped) - 1)
    else:
        cmd_given = 'MOVE 0 {}'.format(robot.y)

    return cmd_given


def command_robot(robot, ore_cells, game_map, game_state):
    cmd_given = None

    update_task(robot, game_state)

    # Perform tasks
    if robot.task == 'RADAR':
        cmd_given = place_radar(robot, game_state)

    elif robot.task == 'TRAP':
        cmd_given = place_trap(robot, game_map, game_state)

    elif robot.task == 'ORE':
        cmd_given = find_ore(robot, ore_cells, game_map, game_state)

    if robot.task == 'RETURN':
        cmd_given = return_to_base(robot, game_state)

    if not cmd_given:
        log('ERROR: no command given - clear robot task and WAIT')
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
            if manhattan_distance(cell, robot_cell) < manhattan_distance(closest, robot_cell):
                closest = cell
        return closest
    print('tried blind dig but no safe cells, len = {}'.format(len(safe_cells)), file=sys.stderr)
    return None


def find_closest_ore(cell, ore_cells):
    """
    Find closest ore (not sure if safe) - assumes there are visible ore cells
    :param cell: grid location x,y
    :param ore_cells: list cells with visible ores
    :return: return closest cell with ore
    """
    closest = ore_cells[0]
    for ore_cell in ore_cells:
        if manhattan_distance(cell, ore_cell) < manhattan_distance(cell, closest):
            closest = ore_cell
    return closest


def find_closest_safe_ore(cell, ore_cells):
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
            elif manhattan_distance(cell, ore_cell) < manhattan_distance(cell, closest):
                closest = ore_cell
    return closest


def manhattan_distance(c1, c2):
    return abs(c1.x - c2.x) + abs(c1.y - c2.y)


# return list of robots within dist of a given coord
def robots_within_distance_from_cell(robots, game_map, target_cell, dist):
    robots_in_range = list()
    for robot in robots.values():
        robot_cell = game_map.get_cell(robot.x, robot.y)
        if manhattan_distance(robot_cell, target_cell) < dist:
            robots_in_range.append(robot)
    return robots_in_range


# return set of coordinates that will be affected if trap is activated at given cell
def get_affected_cells_for_trap_at(base_cell, game_map, visited_cells=set()):
    """
    Find set of coordinates that will be affected if trap is activated at base_cell
    :param base_cell
    :param game_map
    :return: Set of cells that will be affected. Empty if no trap at given base_cell
    """
    affected_cells = set()
    visited_cells.add(base_cell)
    if not base_cell.has_trap():
        return affected_cells

    affected_cells.add(base_cell)

    neighbours = neighbouring_cells(base_cell, game_map)
    for cell in neighbours:
        affected_cells.add(cell)
        if cell.has_trap() and not cell in visited_cells:
            affected_cells = affected_cells.union(get_affected_cells_for_trap_at(cell, game_map, visited_cells))

    return affected_cells


def neighbouring_cells(base_cell, game_map):
    """
    Get the direct neighbours (up to 4) of a cell
    :param base_cell
    :param game_map
    :return: Set of cells, max 4
    """
    neighbours = set()
    x = base_cell.x
    y = base_cell.y
    if x - 1 >= 0:
        neighbours.add(game_map.get_cell(x - 1, y))
    if x + 1 <= 29:
        neighbours.add(game_map.get_cell(x + 1, y))
    if y - 1 >= 0:
        neighbours.add(game_map.get_cell(x, y - 1))
    if y + 1 <= 14:
        neighbours.add(game_map.get_cell(x, y + 1))
    return neighbours

def get_num_robots_in(cells, robots):
    """
    Gets the number of robots in given cells
    :param cells
    :param robots
    :return: number of robots
    """
    num_bots = 0

    for cell in cells:
        for robot in robots:
            if robot.x == cell.x and robot.y == cell.y:
                num_bots += 1

# MAIN

# setup game map
width, height = [int(i) for i in input().split()]

game_map = GameMap(width, height)
game_state = GameState()
game_state.turn = 0

my_robots = {}
opp_robots = {}

# game loop
while True:
    game_state.my_score, game_state.opp_score = [int(i) for i in input().split()]

    # Update game map
    had_radar = list()
    for i in range(height):
        inputs = input().split()
        for j in range(width):
            # ore: amount of ore or "?" if unknown
            currOre = inputs[2*j]
            game_map.grid[i][j].ore = -1 if currOre == '?' else int(currOre)

            # hole: 1 if cell has a hole
            hole = int(inputs[2*j+1])

            # check if hole was dug this turn
            if hole and not game_map.grid[i][j].hole:
                game_map.grid[i][j].turn_dug = game_state.turn

            game_map.grid[i][j].hole = hole

            # clear trap info
            game_map.grid[i][j].clear_trap()

            # clear radar - keep track of which cells did have radar before
            if game_map.grid[i][j].clear_radar():
                had_radar.append(game_map.grid[i][j])

    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, game_state.radar_cooldown, game_state.trap_cooldown = [int(i) for i in input().split()]
    game_state.update_turns_since_trap()

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
                        game_state.my_bots_alive -= 1
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
    for cell in ore_cells:
        if not cell.has_trap():
            game_state.ore_available += cell.ore

    game_state.radar_requested, game_state.trap_requested = False, False
    game_state.num_bots_moving_to_radar = 0

    if trap_avoidance_active:
        game_map.check_first_column_trapped(game_state)

    for id, robot in my_robots.items():
        if not robot.dead:
            command = command_robot(robot, ore_cells, game_map, game_state)
            command += ' {}'.format(robot.task)
            print(command)
        else:
            print('WAIT I THINK I AM DEAD')

    game_state.turn += 1
