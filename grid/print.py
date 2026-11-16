"""

Print utilities for the grid-based puzzle.
Includes functions to print example solutions and a summary of the grid configuration.
"""

from grid_config import (
    COLS, 
    ROWS, 
    FIXED_DEFS, 
    MAX_INNER_DEFS, 
    MAX_TOTAL_DEFS, 
    TOTAL_DEFS_RANGE
)

def _print_examples(solutions, limit=5):
    for idx, grid in enumerate(solutions[:limit], start=1):
        print_grid = [[ '.' for _ in range(COLS)] for _ in range(ROWS)]

        for row in range(ROWS):
            for col in range(COLS):
                print_grid[row][col] = 'D' if grid[row][col] else '.'

        print(f'\nExample {idx}:')
        for row in print_grid:
            print(row)


def _print_summary():
    print('Table: 11x17')
    print(f'Fixed cells on first row/column: {len(FIXED_DEFS)}')
    print(f'Max definition cells in the interior: {MAX_INNER_DEFS}')
    print(f'Max total definition cells: {MAX_TOTAL_DEFS}')
    print(f'Original requested range: {TOTAL_DEFS_RANGE}')
    print()
    if TOTAL_DEFS_RANGE[0] > MAX_TOTAL_DEFS:
        print('WARNING: requested minimum is impossible under the current geometry.')
    else:
        print('The requested range may require relaxing other rules.')
