from sympy import *
import numpy as np
from collections import deque

# represents the knowledge base of the AI, so that moves are not duplicated
mines = set()
empty = set()

# store moves as a tripple - (opp, r, c) - where opp is "flag" or "mine" and
# and r and c represent coordinates row and columns respectively
queue = deque()

# the change in tile for each of the 8 surrounding tiles

coordinates = {(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)}

""" given an n x n board state, create an n^2 x n^2 + 1 matrix representation. Each
row index and col index corresponds to a particular tile. For example a tile index
with (row_index, col_index) in board_state would map to row_index * column_size
+ col_index on either axis. For each row, if the corresponding tile is opened
and has a postive surrounding mine count, mark each of the unopened tiles as 1 
in the corresponding column index. The final row of the matrix should be equal to
the amount of surrounding mines if the tile has been opened."""


def to_matrix(board_state):
    tile_count = len(board_state) * len(board_state[0])
    board_rep = np.zeros((tile_count, tile_count + 1))
    col_size = len(board_state[0])
    row_size = len(board_state)
    for r in range(row_size):
        for c in range(col_size):
            if board_state[r][c] > 0:
                board_rep[c + r * col_size][tile_count] = board_state[r][c]
                for i, j in coordinates:
                    if (
                        r + i >= 0
                        and j + c >= 0
                        and j + c < col_size
                        and r + i < row_size
                        and board_state[r + i][c + j] == -1
                    ):
                        board_rep[c + r * col_size][(c + j) + (r + i) * col_size] = 1
                    elif (
                        r + i >= 0
                        and j + c >= 0
                        and j + c < col_size
                        and r + i < row_size
                        and board_state[r + i][c + j] == -2
                    ):
                        board_rep[c + r * col_size][tile_count] -= 1
    return board_rep


"""For the row reduced version of the matrix representation of board_state,
analyze each row to see if any certain moves can be made. A row is analyzed
by seeing if the final column index is equal to the maximum or minimum of this equation.
If it is equal to the maximum, positive tiles are mines and negative tiles are empty.
If it is equal to the minimum, postive tiles are empty and negative tiles are mines.
The given information should be added to queue, which represents certain moves. Additionally, 
the AI knowledge base (the sets mines and empty) should be updated."""


def analyze_matrix(board_rep, board_state):
    tile_count = len(board_state) * len(board_state[0])
    for r in range(tile_count):
        maximum = 0
        minimum = 0
        for c in range(tile_count):
            if board_rep[r, c] > 0:
                maximum += board_rep[r, c]
            else:
                minimum += board_rep[r, c]
        if maximum == board_rep[r, tile_count]:
            for c in range(tile_count):
                i, j = c // len(board_state), c % len(board_state)
                if board_rep[r, c] > 0:
                    if (i, j) not in mines:
                        queue.append(("flag", i, j))
                        mines.add((i, j))
                elif board_rep[r, c] < 0:
                    if (i, j) not in empty:
                        queue.append(("open", i, j))
                        empty.add((i, j))
        elif minimum == board_rep[r, tile_count]:
            for c in range(tile_count):
                i, j = c // len(board_state), c % len(board_state)
                if board_rep[r, c] > 0:
                    if (i, j) not in empty:
                        queue.append(("open", i, j))
                        empty.add((i, j))
                elif board_rep[r, c] < 0 and (i, j) not in mines:
                    queue.append(("flag", i, j))
                    mines.add((i, j))


"""Given a board_state, run the CSP solver"""


def CSP_solver(board_state):
    # create a matrix representation of the board_state
    board_rep = to_matrix(board_state)

    # row reduce the board representation
    board_rep = Matrix(board_rep)
    board_rep.rref()

    # determine flag and move operations from the row reduced board representation
    analyze_matrix(board_rep, board_state)


"""Given a board_state, run the single point solver. This consists of checking
 whether given the surrounding mine count of a tile, can we reveals known mines 
 or bombs. We may flag tiles if the mine count == unopened tile count, and we
 may open tiles if the mine count == flagged count"""


def SP_solver(board_state):
    col_size = len(board_state[0])
    row_size = len(board_state)
    for r in range(row_size):
        for c in range(col_size):
            mine_count = board_state[r][c]
            unopened_tiles = []
            flaged_tiles = []
            if mine_count > 0:
                for i, j in coordinates:
                    if (
                        r + i >= 0
                        and j + c >= 0
                        and j + c < col_size
                        and r + i < row_size
                    ):
                        if board_state[r + i][j + c] == -1:
                            unopened_tiles.append((r + i, j + c))
                        elif board_state[r + i][j + c] == -2:
                            flaged_tiles.append((r + i, j + c))
                if len(flaged_tiles) == mine_count:
                    for x, y in unopened_tiles:
                        if (x, y) not in empty:
                            queue.append(("open", x, y))
                            empty.add((x, y))
                elif len(unopened_tiles) + len(flaged_tiles) == mine_count:
                    for x, y in unopened_tiles:
                        if (x, y) not in mines:
                            queue.append(("flag", x, y))
                            mines.add((x, y))


"""Given a board_state, choose a random unopened tile """


def random_move(board_state):
    unopened = np.argwhere(board_state == -1)
    index = np.random.choice(len(unopened))
    r, c = unopened[index][0], unopened[index][1]
    empty.add((r, c))
    print("random!")
    return ("open", r, c)


"""Given a board_state and bomb_count, output the tile with the lowest local probability.
If there is a conflict when assigning a local probability, assign the the highest probability
to that tile """


def select_tile_with_lowest_local_probability(board_state, bomb_count):
    col_size = len(board_state[0])
    row_size = len(board_state)
    local_probabilites = np.ones_like(board_state).astype(float)
    # find the probability of all the mines in the frontier set
    # if there is a conflicting probability, assign the highest local probability
    for r in range(row_size):
        for c in range(col_size):
            mine_count = board_state[r][c]
            unopened_tiles = []
            flaged_tiles = []
            if mine_count != -1:
                local_probabilites[r][c] = 2
            if mine_count > 0:
                for i, j in coordinates:
                    if (
                        r + i >= 0
                        and j + c >= 0
                        and j + c < col_size
                        and r + i < row_size
                    ):
                        if board_state[r + i][j + c] == -1:
                            unopened_tiles.append((r + i, j + c))
                        elif board_state[r + i][j + c] == -2:
                            flaged_tiles.append((r + i, j + c))
                mine_count = mine_count - len(flaged_tiles)
                if mine_count > 0:
                    for x, y in unopened_tiles:
                        lp = mine_count / len(unopened_tiles)
                        if (
                            local_probabilites[x][y] == 1
                            or lp > local_probabilites[x][y]
                        ):
                            local_probabilites[x][y] = lp

    # the amount of bombs in the unknown set
    unknown_set_count = np.sum(local_probabilites[local_probabilites == 1])

    # we are considering the unkown set for selection because it is not always the best to select from the frontier
    if unknown_set_count > 0:
        # by the linearity of expectation - we can estimate the amount of bombs in the frontier set
        frontier_set_expected_mines = np.sum(local_probabilites[local_probabilites < 1])
        # probability of any tile in the unkown set being a mine
        unexplored_probabilites = (
            bomb_count
            - frontier_set_expected_mines
            - np.count_nonzero(board_state[board_state == -2])
        ) / unknown_set_count
        # set all tiles in the unkown set to the same probability
        local_probabilites[local_probabilites == 1] = unexplored_probabilites

    # find lowest probabiltiy
    lowest_probability = np.amin(local_probabilites)

    # find all indices lowest probability
    indices = np.argwhere(local_probabilites == lowest_probability)

    # find a random tile out of all of the lowest probability tiles
    select = np.random.randint(0, len(indices))

    return indices[select][0], indices[select][1]


"""Given a board_state output an opp: open or flag, an a coordinate r, c to do such operation """

# certain_move shows how we developed the AI's certain move strategy
# 0 is the basic strategy where it makes a move based on information at a single point
# 1 takes into account all the information we know and creates a constraint satisfaction problem


# uncertain_move shows how we developed the AI's uncertain move strategy
# 0 is the basic strategy where it makes a random move if there are no certain moves
# 1 takes into account the locaal probability of each tile and returns the one with lowest chance of being a mine
# 2 adds a distance heuristic
def ai_heuristic_logic(
    board_state, first_move, bomb_count, certain_move_model, uncertain_move_strat
):
    if first_move:
        while queue:
            queue.pop()
        mines.clear()
        empty.clear()

    # If a move remains from last AI call, return move
    if queue:
        return queue.popleft()

    if not certain_move_model:
        SP_solver(board_state)
    else:
        CSP_solver(board_state)

    # If trivial move was found, make trivial move
    if queue:
        return queue.popleft()

    # if no queue chose a random unopened tile
    if not uncertain_move_strat:
        return random_move(board_state)
    else:
        r, c = select_tile_with_lowest_local_probability(board_state, bomb_count)
        return ("open", r, c)
