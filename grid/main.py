import os

from grid.print import _print_summary
from grid.create_grids import generate_geometry
from grid.autodefinido_pdf import generar_pdf_autodefinidos
from grid.grid_config import OUTPUTS_DIR, MIN_LETTERS_PER_WORD

def main():
    pass

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