"""

Grid creation utilities for the grid-based puzzle.
Includes functions to build the initial grid, initialize row patterns, and manage available cells.
"""

from itertools import combinations
import random
import os
from collections import deque
from autodefinido_pdf import generar_pdf_autodefinidos
from print import _print_summary
from grid_config import (
    COLS,
    COLS_DEFS_RANGE,
    FIXED_DEFS,
    FIXED_NOT_AVALABLE,
    MAX_TOTAL_DEFS,
    MIN_LETTERS_PER_WORD,
    OUTPUTS_DIR,
    ROWS,
    ROWS_DEFS_RANGE,
    TOTAL_DEFS_RANGE,
)


def _build_initial_grid() -> list[list[bool]]:
    """
    Build the initial grid with fixed definitions placed.
    Cells in FIXED_DEFS are marked as True, all others as False.
    """
    grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
    for r, c in FIXED_DEFS:
        grid[r][c] = True
    return grid


def _init_row_patterns():
    """
    Genera totes les combinacions possibles de posicions de definicions per a cada fila, sense combinacions consecutives.
    """
    options = []
    for k in range(ROWS_DEFS_RANGE[0], ROWS_DEFS_RANGE[1] + 1):
        for combo in combinations(list(range(1, COLS)), k): # a la primera columna mai posarem definicions. 
            if all(
                combo[i + 1] - combo[i] > 1
                for i in range(len(combo) - 1)
            ):
                options.append(combo)

    random.shuffle(options) # Cada execució serà diferent. 
    
    print(f"Each row can contain definition cells in these positions (0 based): \n{options}")
    return options


def _initialize_available_cells():
    """
    Initialize the matrix of available cells for placing definitions.
    Cells in FIXED_DEFS and FIXED_NOT_AVALABLE are marked as unavailable.
    """
    matrix = [[True for _ in range(COLS)] for _ in range(ROWS)]
    print_matrix = [[ '.' for _ in range(COLS)] for _ in range(ROWS)]

    for i, j in FIXED_DEFS.union(FIXED_NOT_AVALABLE):
        matrix[i][j] = False
        print_matrix[i][j] = 'D' if (i, j) in FIXED_DEFS else 'X'

    print("Initial available cells matrix:\n")
    for row in print_matrix:
        print(row)
    return matrix


def _update_available_cells(available_cells: list[list[bool]], grid: list[list[bool]], row: int, combo: list[int]) -> list[list[bool]]:
    """
    Update the matrix of available cells after placing a definition in the specified row and columns.

    Args:
        available_cells (list[list[bool]]): Current state of available cells in the grid.
        grid (list[list[bool]]): Current state of the grid with placed definitions.
        row (int): Index of the row where definitions are being placed.
        combo (list[int]): List of column indices where definitions are placed in the row.

    Returns:
        list[list[bool]]: Updated matrix of available cells.
    """
    # TODO: Check nombre de definicions totals, per columna i per fila i podar -> Hauria d'anar a dfs i una funcion nova?
    # TODO: Limit de nombre de paraules amb cert nombre de lletres. 
    
    new_available_cells = [
        r.copy() for r in available_cells
    ]

    for col in combo:
        # Ultimes columnes no podem posar definicions a sota pk no tenen solució horitzontal
        if col >= COLS-MIN_LETTERS_PER_WORD: 
            for r in range(row+1, min(row+MIN_LETTERS_PER_WORD+1, ROWS)):
                new_available_cells[r][col] = False

        # Si la cella bloqueja la primera solució horitzontal d'una cella de la primera columna,
        #   la cella de la primera columna haura de tenir l'altre solució horitzontal.      
        if col <= MIN_LETTERS_PER_WORD and row%2 == 0:
            for c in range(2, MIN_LETTERS_PER_WORD):
                new_available_cells[row+1][c] = False

        # Si la cella bloqueja una solució vertical de la primera fila,
        #   la cella de la primera fila haura de tenir l'altre solució vertical.
        if row < MIN_LETTERS_PER_WORD:

            if col%2 == 0:
                for r in range(row+1, MIN_LETTERS_PER_WORD): # NOTE: Comença a `row+1`en comptes de 1 perque les celles de dalt ja no les provara
                    # print(f"Blocking vertical solution for cell ({r}, {col+1}) due to cell ({row}, {col})")
                    new_available_cells[r][col+1] = False
            else:
                for r in range(row+1, row+MIN_LETTERS_PER_WORD+1): # NOTE: Comença a `row+1`en comptes de 1 perque les celles de dalt ja no les provara
                    # print(f"Blocking vertical solution for cell ({r}, {col-1}) due to cell ({row}, {col})")
                    new_available_cells[r][col-1] = False

            # Si estem a la segona fila i a les primeres <MIN_LETTERS_PER_WORD> columnes, bloqueja la solució horitzontal
            #     de la cella (0,0), i per tant la cella (0,0) haurà de tenir la solució vertical. 
            if row==1 and col<MIN_LETTERS_PER_WORD:
                for r in range(2, MIN_LETTERS_PER_WORD, 2): # Cada 2 perque les altres ja no estan disponibles des de l'inici.
                    new_available_cells[r][1] = False

        # Bloqueja les <MIN_LETTERS_PER_WORD> cel·les inferiors de la cel·la actual
        for r in range(row+1, min(row+MIN_LETTERS_PER_WORD+1, ROWS)):
            new_available_cells[r][col] = False

    return new_available_cells


def _update_available_combinations(patterns: list[list[int]], available_cells: list[list[bool]], row_idx: int) -> list[list[int]]:
    """
    Update the available combinations of columns for a given row based on the current state of available cells.

    Args:
        patterns (list[list[int]]): List of possible column combinations for the row.
        available_cells (list[list[bool]]): Current state of available cells in the grid.
        row_idx (int): Index of the row being updated.

    Returns:
        list[list[int]]: Filtered list of valid column combinations for the row.
    """

    # De todas las combinaciones posibles, 
    #    quédate con las que tienen todas sus posiciones disponibles
    valid_patterns = [
        combo
        for combo in patterns
        if all(available_cells[row_idx][col] for col in combo)
    ]

    # Si no es permeten files buides, elimina el patró sense definicions.
    # if max_empty_rows == 0:
    #     valid_patterns.remove(())

    # No bloquejar les dues solucions verticals de les celles de la primera fila.
    if row_idx < MIN_LETTERS_PER_WORD:
        valid_patterns = [
            combo for combo in valid_patterns
            if not any( # Doesn't have conseccutive columns where the first is even and the second is odd
                combo[i] % 2 == 0 and combo[i + 1] == combo[i] + 1
                for i in range(len(combo) - 1)
            )
        ]

    # Si es de les ultimes files, que estiguin suficientment separades, perque no tindran solució vertical. 
    if row_idx >= ROWS - MIN_LETTERS_PER_WORD:
        valid_patterns = [
            combo
            for combo in valid_patterns
            if all(
                combo[i + 1] - combo[i] >= MIN_LETTERS_PER_WORD + 1
                for i in range(len(combo) - 1)
            )
        ]

    return valid_patterns


def _exists_future_solution(total_defs: int, row_idx: int) -> bool:
    """
    Check if there exists a future solution based on the current number of definitions and the remaining rows.

    This is used to prune the search space in the DFS algorithm.

    Args:
        total_defs (int): The current number of definitions.
        row_idx (int): The current row index being processed in the DFS, before placing definitions in it.
    Returns: 
        - True if there exists a future solution, False otherwise. 
    """

    if total_defs > MAX_TOTAL_DEFS:
        return False

    # Si no se llegarà al minimo de definiciones. 
    if ROWS_DEFS_RANGE[1] * (ROWS - row_idx) + total_defs < TOTAL_DEFS_RANGE[0]:
        return False
    
    return True


def _has_connected_solution(grid: list[list[bool]]) -> bool:
    """
    Check that all response cells, represented by False,
    are orthogonally connected to each other.

    Args:
        grid (list[list[bool]]): The grid to check.

    Returns:
        bool: True if all response cells are connected, False otherwise.
    """

    visited = [[False for _ in range(COLS)] for _ in range(ROWS)]

    response_cells = [
        (r, c)
        for r in range(ROWS)
        for c in range(COLS)
        if not grid[r][c]
    ]

    start_r, start_c = response_cells[0]
    queue = deque([(start_r, start_c)])
    visited[start_r][start_c] = True
    visited_count = 1

    while queue:
        curr_r, curr_c = queue.popleft()

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_r = curr_r + dr
            next_c = curr_c + dc

            if (
                0 <= next_r < ROWS
                and 0 <= next_c < COLS
                and not grid[next_r][next_c] # No es definicion
                and not visited[next_r][next_c] 
            ):
                visited[next_r][next_c] = True
                visited_count += 1
                queue.append((next_r, next_c))

    return visited_count == len(response_cells)


def _encode_grid(grid: list[list[bool]]) -> int:
    """
    Encode the grid as an integer by treating each cell as a bit.

    Args:
        grid (list[list[bool]]): The grid to encode.

    Returns:
        int: The encoded integer representation of the grid.
    """
    code = 0
    for bit, cell in enumerate(cell for row in grid for cell in row):
        if cell:
            code |= 1 << bit
    return code


def generate_geometry(max_candidates: int = 10, max_attempts: int = 10_000) -> list[list[bool]]:
    """
    Generate a grid with definitions placed according to the constraints.

    Args:
        max_candidates (int): Maximum number of candidate solutions to generate.
        max_attempts (int): Maximum number of attempts to find a valid solution.

    Returns:
        list[list[bool]]: A grid represented as a list of lists of booleans, where True indicates a definition.
    """

    patterns = _init_row_patterns()
    initial_available_cells = _initialize_available_cells()
    initial_col_counts = [0] * COLS
    for row, col in FIXED_DEFS:
        initial_col_counts[col] += 1

    solutions = []
    seen = set()
    validity_checks = [0]
    attempts = 0

    def dfs(row_idx, grid, col_counts, total_defs, available_cells):
        # Ja s'han assignat totes les files; valida la graella completa.
        if row_idx == ROWS:
            validity_checks[0] += 1
            print(f"Validity check num. {validity_checks[0]}")

            # Comprova que el nombre total de definicions estigui dins dels limits.
            if not TOTAL_DEFS_RANGE[0] <= total_defs <= TOTAL_DEFS_RANGE[1]:
                print(f"    Discarting candidate: Total definitions out of range {TOTAL_DEFS_RANGE} ({total_defs})")
                return None
            
            # Comprova els limits de definicions de cada columna.
            if not all(
                COLS_DEFS_RANGE[0] <= col_counts[col] <= COLS_DEFS_RANGE[1]
                for col in range(1, COLS)
            ):
                print(f"    Discarting candidate: Column {col} definitions out of range {COLS_DEFS_RANGE} ({col_counts[col]})")
                return None
            
            # Les caselles de resposta han de continuar formant una zona connectada.
            if not _has_connected_solution(grid):
                print(f"    Discarting candidate: Solution not connected")
                return None

            print(f"    Solution found with total definitions {total_defs}!")
            return [row.copy() for row in grid]

        # Obte les combinacions legals per a aquesta fila i n'aleatoritza l'ordre.
        row_patterns = _update_available_combinations(
            patterns, available_cells, row_idx
        )
        random.shuffle(row_patterns)

        for combo in row_patterns:
            # Cada combinacio explora una branca amb copies del seu estat.
            new_grid = [row.copy() for row in grid]
            for col in combo:
                new_grid[row_idx][col] = True

            # Actualitza les posicions bloquejades per les noves definicions.
            new_available_cells = _update_available_cells(
                available_cells, new_grid, row_idx, combo
            )

            # Actualitza el recompte de definicions per columna.
            new_col_counts = col_counts.copy()
            for col in combo:
                new_col_counts[col] += 1

            # Poda la branca si alguna columna supera el maxim.
            if any(
                new_col_counts[col] > COLS_DEFS_RANGE[1]
                for col in range(1, COLS)
            ):
                continue

            new_total = total_defs + len(combo)

            # Poda si ja no es pot assolir el rang total de definicions.
            if not _exists_future_solution(new_total, row_idx + 1):
                continue

            # Poda abans de continuar si les respostes han quedat desconnectades.
            if not _has_connected_solution(new_grid):
                continue

            solution = dfs(
                row_idx + 1,
                new_grid,
                new_col_counts,
                new_total,
                new_available_cells,
            )
            
            if solution is not None:
                return solution

        return None

    # Cada solucio trobada inicia una cerca nova des de la primera fila.
    while len(solutions) < max_candidates and attempts < max_attempts:
        attempts += 1
        candidate = dfs(
            1,
            _build_initial_grid(),
            initial_col_counts,
            len(FIXED_DEFS),
            initial_available_cells,
        )
        if candidate is None:
            break

        signature = _encode_grid(candidate)
        if signature not in seen:
            seen.add(signature)
            solutions.append(candidate)

    print(
        f"Unique solutions: {len(solutions)}; attempts: {attempts}; "
        f"complete grids checked: {validity_checks[0]}"
    )
    if len(solutions) < max_candidates and attempts >= max_attempts:
        print("Maximum search attempts reached before finding all requested solutions.")

    return solutions


if __name__ == '__main__':
    _print_summary()
    solutions = generate_geometry(max_candidates=50)
    print(f'Generated unique candidate layouts: {len(solutions)}')

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    generar_pdf_autodefinidos(
        matrices=solutions,
        ruta_salida=os.path.join(
            OUTPUTS_DIR, f"quadernet_min{MIN_LETTERS_PER_WORD}.pdf"
        ),
        min_letters_per_word=MIN_LETTERS_PER_WORD,
    )
