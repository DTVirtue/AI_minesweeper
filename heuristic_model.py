import itertools
from math import sqrt
from sympy import *
import numpy as np
from collections import deque

mines = set()
opened = set()

# store operations
queue = deque()

# the change in tile for each of the 8 surrounding tiles

coordinates = {(-1, -1), (-1, 0), (-1, 1), (0, -1),
               (0, 1), (1, -1), (1, 0), (1, 1)}

# given a board_state output an opp: open or flag, an a coordinate to do such operation


def matrix_solver(matrix):
    def check_solution(augmented_matrix, solution):
        A = augmented_matrix[:, :-1]
        b = augmented_matrix[:, -1]
        return np.allclose(A @ solution, b)

    def generate(augmented_matrix):
        R, C = augmented_matrix.shape
        R = int(sqrt(R))
        num_vars = augmented_matrix.shape[1] - 1

        # Generate all possible combinations of 0s and 1s for the variables
        combinations = itertools.product([0, 1], repeat=num_vars)

        solutions = []
        for combination in combinations:
            if check_solution(augmented_matrix, combination):
                solutions.append(combination)

        variables_to_be_one = set()
        variables_to_be_zero = set()

        for i in range(num_vars):
            must_be_one = all(solution[i] == 1 for solution in solutions)
            must_be_zero = all(solution[i] == 0 for solution in solutions)
            if must_be_one:
                variables_to_be_one.add((i // R, i - (i // R) * R))

            if must_be_zero:
                variables_to_be_zero.add((i // R, i - (i // R) * R))

        return [variables_to_be_zero, variables_to_be_one]

    return generate(matrix)


def ai_heuristic_logic(board_state):
    if queue:
        return queue.popleft()

    tile_count = len(board_state) ** 2
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
                        board_rep[c + r *
                                  col_size][(c + j) + (r + i) * col_size] = 1
    board_rep = Matrix(board_rep)
    board_rep.rref()

    # fill queue
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
                    if (i, j) not in opened:
                        queue.append(("open", i, j))
                        opened.add((i, j))
        elif minimum == board_rep[r, tile_count]:
            for c in range(tile_count):
                i, j = c // len(board_state), c % len(board_state)
                if board_rep[r, c] > 0:
                    if (i, j) not in opened:
                        queue.append(("open", i, j))
                        opened.add((i, j))
                elif board_rep[r, c] < 0 and (i, j) not in mines:
                    queue.append(("flag", i, j))
                    mines.add((i, j))

    # output first move, update queue
    if queue:
        return queue.popleft()

    # if no queue chose a random unopened tile
    unopened = np.argwhere(board_state == -1)
    index = np.random.choice(len(unopened))
    r, c = unopened[index][0], unopened[index][1]
    opened.add((r, c))
    return ("open", r, c)
