import sys
import math

# Deliver more ore to hq (left side of the map) than your opponent. Use radars to find ore but beware of traps!

# height: size of the map
width, height = [int(i) for i in input().split()]
turn = 0
ore = [['?' for i in range(width)] for j in range(height)] 
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
            ore[i][j] = currOre
            hole = int(inputs[2*j+1])
    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, radar_cooldown, trap_cooldown = [int(i) for i in input().split()]
    for i in range(entity_count):
        # id: unique id of the entity
        # type: 0 for your robot, 1 for other robot, 2 for radar, 3 for trap
        # y: position of the entity
        # item: if this entity is a robot, the item it is carrying (-1 for NONE, 2 for RADAR, 3 for TRAP, 4 for ORE)
        id, type, x, y, item = [int(j) for j in input().split()]
        # print("{} {} {} {} {}".format(id, type, x, y, item), file=sys.stderr)
    for i in range(5):

        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)

        # WAIT|MOVE x y|DIG x y|REQUEST item
        if (i == 2 and turn == 0):
            print("REQUEST RADAR")
        else if (i == 2 and 
        else:
            for i in range(len(ore)):
                for j in range(len(ore[i])):
                    if (ore[i][j] != '?'):
                        print("MOVE " + i + j)
                        break
            print("MOVE 15 8")
        # print("WAIT")
    turn += 1