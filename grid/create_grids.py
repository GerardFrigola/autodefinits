from itertools import combinations
import random
import os
from collections import deque
from autodefinido_pdf import generar_pdf_autodefinidos

ROWS, COLS = 17, 11
INNER_ROWS = list(range(1, ROWS - 1))
INNER_COLS = list(range(1, COLS))
MIN_LETTERS_PER_WORD = 2
assert MIN_LETTERS_PER_WORD >= 1, "Minimum letters per word must be at least 1"
assert MIN_LETTERS_PER_WORD < ROWS/2, "Minimum letters per word must be less than half the number of rows"
assert MIN_LETTERS_PER_WORD < COLS/2, "Minimum letters per word must be less than half the number of columns"

FIXED_DEFS = {(0, c) for c in range(0, COLS, 2)} |\
            {(r, 0) for r in range(0, ROWS, 2)}

FIXED_NOT_AVALABLE = {(1, c) for c in range(1, COLS, 2)} |\
                    {(0, c) for c in range(1, COLS, 2)} |\
                    {(r, 1) for r in range(1, ROWS, 2)} |\
                    {(r, 0) for r in range(1, ROWS, 2)} |\
                    {(r, COLS-1) for r in range(1, MIN_LETTERS_PER_WORD+1)}|\
                    {(ROWS-1, c) for c in range(1, MIN_LETTERS_PER_WORD+1)} |\
                    {(r, c) for r in range(ROWS-MIN_LETTERS_PER_WORD, ROWS) for c in range(COLS-MIN_LETTERS_PER_WORD, COLS)}
                    
MAX_INNER_DEFS = len(INNER_ROWS) * 2
MAX_TOTAL_DEFS = len(FIXED_DEFS) + MAX_INNER_DEFS

TOTAL_DEFS_RANGE = (38, 44)
ROWS_DEFS_RANGE = (0, 2)
COLS_DEFS_RANGE = (1, 3)
###
#------------- 
#|D.D.D.D.D.D|
#|.X.X.X.X.XX|
#|D.........X|
#|.X.........|
#|D..........|
#|.X.........|
#|D..........|
#|.X.........|
#|D..........|
#|.X.........|
#|D..........|
#|.X.........|
#|D..........|
#|.X.........|
#|D..........|
#|.X.......XX|
#|DXX......XX|
#-------------
###


def build_initial_grid():
    grid = [[False for _ in range(COLS)] for _ in range(ROWS)]
    for r, c in FIXED_DEFS:
        grid[r][c] = True
    return grid

def init_row_patterns():
    options = []
    for k in range(3):
        for combo in combinations(list(range(1, COLS)), k): # a la primera columna mai posarem definicions. 
            options.append(combo)
    random.shuffle(options)
    print(f"Each row can contain definition cells in these positions (0 based): \n{options}")
    return options


def initialize_available_cells():
    matrix = [[True for _ in range(COLS)] for _ in range(ROWS)]
    print_matrix = [[ '.' for _ in range(COLS)] for _ in range(ROWS)]

    for i, j in FIXED_DEFS.union(FIXED_NOT_AVALABLE):
        matrix[i][j] = False
        print_matrix[i][j] = 'D' if (i, j) in FIXED_DEFS else 'X'

    print("Initial available cells matrix:\n")
    for row in print_matrix:
        print(row)
    return matrix


def update_available_cells(available_cells, grid, row, combo):
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

        # Si la cella bloqueja l'existencia d'una solució horitzontal d'una cella de la 
        #   seva esquerra, la cella de la seva esquerra haura de tenir solució vertical
        for c in range(max(1, col-MIN_LETTERS_PER_WORD), col):
            if grid[row][c] == True:
                for r in range(row+1, min(row+MIN_LETTERS_PER_WORD+1, ROWS)):
                    new_available_cells[r][c] = False

    return new_available_cells


def update_available_combinations(patterns, available_cells, row_idx):

    # De todas las combinaciones posibles, 
    #    quédate con las que tienen todas sus posiciones disponibles
    valid_patterns = [
        combo
        for combo in patterns
        if all(available_cells[row_idx][col] for col in combo)
    ]

    # No bloquejar les dues solucions verticals de les celles de la primera fila.
    if row_idx < MIN_LETTERS_PER_WORD:
        valid_patterns = [
            combo
            for combo in valid_patterns
            if len(combo) > 1 
            and 
            # Doesn't have conseccutive columns where the first is even and the second is odd
            not any(
                    combo[i] % 2 == 0 and combo[i + 1] == combo[i] + 1
                    for i in range(len(combo) - 1)
                )
        ]

    # Si es de les ultimes files, que estiguin suficientment seaprades, perque no tindran solució vertical. 
    if row_idx >= ROWS - MIN_LETTERS_PER_WORD:
        valid_patterns = [
            combo
            for combo in valid_patterns
            if len(combo) < 2
            or all(
                combo[i + 1] - combo[i] >= MIN_LETTERS_PER_WORD+1
                for i in range(len(combo) - 1)
            )
        ]

    return valid_patterns


def exists_future_solution(total_defs, available_cells, row_idx):
    """
    Checks if there exists a future solution given the current state of the grid and available cells,
    depending on the current number of definitions and the remaining rows. 

    This is used to prune the search space in the DFS algorithm.

    Args:
        total_defs (int): The current number of definitions.
        available_cells (list of list of bool): A matrix indicating which cells are still available for placing definitions.
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


def has_connected_solution(grid):
    """
    Comprueba que todas las celdas de respuesta, representadas por False,
    estén conectadas entre sí ortogonalmente.
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


class RestartSearch(Exception):
    pass


def generate_geometry(max_candidates=10) -> list[list[bool]]:
    """
    TODO: Fer Docstring
    """
    print(f'Generating candidate layouts with total definitions <= {MAX_TOTAL_DEFS} and max candidates = {max_candidates}')
    patterns = init_row_patterns()
    solutions = []
    validity_checks = [0]

    # TODO: A vegades es queda pillat en un minim local -> investigarho. 
    # TODO: Assegurar que la densitat de tota la graella es similar i no hi ha zones sobrepoblades i zones sotapoblades. 
    def dfs(row_idx, grid, col_counts, total_defs, available_cells):
        # print(f"    Processing row {row_idx}")

        if len(solutions) >= max_candidates: # ja hem trobat el numero maxim de possibles taules que volem.
            return
        
        if row_idx == ROWS: # Ja ens hem passat la ultima fila, comprovem.
            validity_checks[0] += 1
            # print(f"Validity check {validity_checks[0]:,}:")

            if total_defs >= TOTAL_DEFS_RANGE[0]: # comprovar que el numero de definicions esta dins el limit. 
                if all(COLS_DEFS_RANGE[0] <= col_counts[col] for col in range(1, COLS)): # Comprovar que les columnes tenen el numero de definicions correctes. 
                    if has_connected_solution(grid): # Comprovar que totes les celdes de resposta estan connectades.    
                        if (len(solutions) + 1)%1000 == 0:
                            print(f"   Solution {len(solutions) + 1} found! With total definitions: {total_defs}")
                        solutions.append([row[:] for row in grid])
                        if len(solutions) < max_candidates: # si encara en falten, reiniciem l'arbre de cerca des de zero.
                            raise RestartSearch()
            return

        # Combinaciones posibles para esta fila según las celdas que todavía están disponibles
        row_patterns = update_available_combinations(patterns, available_cells, row_idx)

        for combo in row_patterns: # backtrack algorithm recorre les combinacions. 

            # copia del estat per cada branca
            new_grid = [row.copy() for row in grid] 
            available_cells_copy = [row.copy() for row in available_cells]

            # Afegir cel·la de definició a la fila actual i actualitzar les disponibles. 
            for col in combo:
                new_grid[row_idx][col] = True 
            new_available_cells = update_available_cells(available_cells_copy, new_grid, row_idx, combo)

            # Actualitza numero de definicions per columna. 
            new_col_counts = col_counts.copy()
            for col in combo:
                new_col_counts[col] += 1

            # Si alguna columna ha superat el maxim de definicions, descarta la combinació.
            if any(new_col_counts[col] > COLS_DEFS_RANGE[1] for col in range(1, COLS)):
                continue

            # Actualitza el total de definicions i comprova si ens hem passat del limit. 
            new_total = total_defs + len(combo)
            if not exists_future_solution(new_total, new_available_cells, row_idx + 1):
                continue

            dfs(row_idx + 1, new_grid, new_col_counts, new_total, new_available_cells)

    initial_grid = build_initial_grid()
    initial_available_cells = initialize_available_cells()

    initial_col_counts = [0] * COLS
    for r, c in FIXED_DEFS:
        initial_col_counts[c] += 1
    # TODO: Ara es poden generar dues solucions iguals. 
    while len(solutions) < max_candidates: # cada cop que es troba una solució, es reinicia l'arbre des de la fila 1.
        try:
            dfs(1, initial_grid, initial_col_counts, len(FIXED_DEFS), initial_available_cells)
        except RestartSearch:
            continue
        else:
            break

    return solutions


def print_summary():
    print('Table: 11x17')
    print(f'Fixed cells on first row/column: {len(FIXED_DEFS)}')
    print(f'Max definition cells in the interior: {MAX_INNER_DEFS}')
    print(f'Max total definition cells: {MAX_TOTAL_DEFS}')
    print(f'Original requested range: {TOTAL_DEFS_RANGE}')
    print()
    if TOTAL_DEFS_RANGE[0] > MAX_TOTAL_DEFS:
        print('WARNING: 36..41 is impossible under the corrected geometry, because the maximum total is 41.')
    else:
        print('The requested range is still possible only if other rules are relaxed or redefined.')


def print_examples(solutions, limit=5):
    for idx, grid in enumerate(solutions[:limit], start=1):
        print_grid = [[ '.' for _ in range(COLS)] for _ in range(ROWS)]

        for row in range(ROWS):
            for col in range(COLS):
                print_grid[row][col] = 'D' if grid[row][col] else '.'

        print(f'\nExample {idx}:')
        for row in print_grid:
            print(row)


if __name__ == '__main__':
    print_summary()
    solutions = generate_geometry(max_candidates=50)
    print(f'Generated candidate layouts: {len(solutions)}')
    # print_examples(solutions)

    generar_pdf_autodefinidos(
        matrices=solutions,
        ruta_salida=f"quadernet_min{MIN_LETTERS_PER_WORD}.pdf"
        #logo_path="mi_logo.png",  # opcional
    )
