"""

Configuration for the grid-based puzzle, including dimensions, fixed cells, and constraints.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

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
ROWS_DEFS_RANGE = (1, 2)
COLS_DEFS_RANGE = (1, 3)
### For min letters = 2
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