"""
Generador de paginas imprimibles para autodefinidos (crucigramas sin numeros/letras).

Cada autodefinido se representa como una matriz (lista de listas) de booleanos:
    True  -> casilla de DEFINICION (se pinta mas oscura)
    False -> casilla de RESPUESTA   (se deja clara, para escribir la letra)

El programa genera un PDF en tamano A5 vertical, con una pagina por matriz,
cuadricula centrada con celdas cuadradas, bordes de contorno en cada celda,
margenes libres (para numero de pagina y logo) y numero de pagina automatico.

Requiere: reportlab  (pip install reportlab)
"""

from __future__ import annotations

from typing import List, Sequence, Optional
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color


# ----------------------------------------------------------------------------
# Configuracion visual (ajustable)
# ----------------------------------------------------------------------------

PAGE_WIDTH, PAGE_HEIGHT = A5  # A5 vertical: 148 x 210 mm

# Margenes de la pagina (dejan espacio libre para numero de pagina / logo)
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 16 * mm   # un poco mayor para alojar el numero de pagina
MARGIN_LEFT = 12 * mm
MARGIN_RIGHT = 12 * mm

# Colores
COLOR_DEFINICION = Color(0.20, 0.20, 0.20)   # gris oscuro para casillas True
COLOR_RESPUESTA = Color(1, 1, 1)             # blanco para casillas False
COLOR_BORDE = Color(0, 0, 0)                 # negro para el contorno de celdas

GROSOR_BORDE_CELDA = 0.6          # pt, borde de cada celda individual
GROSOR_BORDE_EXTERIOR = 1.3       # pt, borde exterior de toda la cuadricula

MOSTRAR_NUMERO_PAGINA = True
NUMERO_PAGINA_TAMANO_FUENTE = 9
NUMERO_PAGINA_FUENTE = "Helvetica"


# ----------------------------------------------------------------------------
# Logica de dibujo
# ----------------------------------------------------------------------------

def _validar_matriz(matriz: Sequence[Sequence[bool]]) -> None:
    if not matriz or not matriz[0]:
        raise ValueError("La matriz esta vacia.")
    n_cols = len(matriz[0])
    for i, fila in enumerate(matriz):
        if len(fila) != n_cols:
            raise ValueError(
                f"Todas las filas deben tener el mismo numero de columnas. "
                f"La fila {i} tiene {len(fila)} columnas, se esperaban {n_cols}."
            )


def _calcular_geometria_cuadricula(filas: int, columnas: int):
    """Calcula el tamano de celda (cuadrada) y el origen para centrar
    la cuadricula dentro del area util de la pagina (descontando margenes)."""
    ancho_util = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    alto_util = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    cell = min(ancho_util / columnas, alto_util / filas)

    ancho_grid = cell * columnas
    alto_grid = cell * filas

    # Centrado dentro del area util
    x0 = MARGIN_LEFT + (ancho_util - ancho_grid) / 2
    y0 = MARGIN_BOTTOM + (alto_util - alto_grid) / 2

    return cell, x0, y0, ancho_grid, alto_grid


def _dibujar_pagina(c: canvas.Canvas, matriz: Sequence[Sequence[bool]],
                     numero_pagina: Optional[int], total_paginas: Optional[int]) -> None:
    _validar_matriz(matriz)
    filas = len(matriz)
    columnas = len(matriz[0])

    cell, x0, y0, ancho_grid, alto_grid = _calcular_geometria_cuadricula(filas, columnas)

    # y0 es el borde inferior de la cuadricula; dibujamos fila 0 (la superior
    # de la matriz) arriba del todo, por eso invertimos el indice de fila.
    for fila_idx, fila in enumerate(matriz):
        y_top_celda = y0 + alto_grid - fila_idx * cell
        y_celda = y_top_celda - cell
        for col_idx, es_definicion in enumerate(fila):
            x_celda = x0 + col_idx * cell

            color_relleno = COLOR_DEFINICION if es_definicion else COLOR_RESPUESTA
            c.setFillColor(color_relleno)
            c.setStrokeColor(COLOR_BORDE)
            c.setLineWidth(GROSOR_BORDE_CELDA)
            c.rect(x_celda, y_celda, cell, cell, fill=1, stroke=1)

    # Borde exterior mas grueso para que la cuadricula destaque como bloque
    c.setStrokeColor(COLOR_BORDE)
    c.setLineWidth(GROSOR_BORDE_EXTERIOR)
    c.setFillColor(Color(0, 0, 0, alpha=0))
    c.rect(x0, y0, ancho_grid, alto_grid, fill=0, stroke=1)

    if MOSTRAR_NUMERO_PAGINA and numero_pagina is not None:
        c.setFillColor(COLOR_BORDE)
        c.setFont(NUMERO_PAGINA_FUENTE, NUMERO_PAGINA_TAMANO_FUENTE)
        texto = str(numero_pagina)
        if total_paginas:
            texto = f"{numero_pagina} / {total_paginas}"
        c.drawCentredString(PAGE_WIDTH / 2, MARGIN_BOTTOM / 2, texto)

    # Espacio reservado arriba (MARGIN_TOP) y esquinas queda libre para logo;
    # si se quiere anadir un logo, ver `dibujar_logo` mas abajo.


def dibujar_logo(c: canvas.Canvas, ruta_imagen: str, ancho: float = 16 * mm,
                  esquina: str = "top-left") -> None:
    """Dibuja un logo en una esquina dentro del margen superior.
    Llamar ANTES de c.showPage() en la pagina deseada, o pasar
    `logo_path` a generar_pdf_autodefinidos para aplicarlo a todas."""
    from reportlab.lib.utils import ImageReader

    img = ImageReader(ruta_imagen)
    iw, ih = img.getSize()
    alto = ancho * ih / iw

    y = PAGE_HEIGHT - MARGIN_TOP / 2 - alto / 2
    if esquina == "top-left":
        x = MARGIN_LEFT
    else:  # top-right
        x = PAGE_WIDTH - MARGIN_RIGHT - ancho

    c.drawImage(img, x, y, width=ancho, height=alto, mask="auto")


# ----------------------------------------------------------------------------
# Funcion principal
# ----------------------------------------------------------------------------

def generar_pdf_autodefinidos(
    matrices: List[List[List[bool]]],
    ruta_salida: str,
    logo_path: Optional[str] = None,
    numeracion_inicial: int = 1,
) -> None:
    """Genera un PDF con una pagina A5 vertical por cada matriz de la lista.

    Args:
        matrices: lista de autodefinidos; cada uno es una lista de listas de
                   bool (True = casilla de definicion, False = casilla de respuesta).
                   El numero de filas/columnas puede variar entre matrices.
        ruta_salida: ruta del archivo .pdf a generar.
        logo_path: ruta opcional a una imagen (PNG/JPG) para incluir en la
                   esquina superior de cada pagina.
        numeracion_inicial: numero desde el que empieza la numeracion de paginas.
    """
    if not matrices:
        raise ValueError("Debes proporcionar al menos una matriz.")

    total_paginas = len(matrices)
    c = canvas.Canvas(ruta_salida, pagesize=A5)

    for i, matriz in enumerate(matrices):
        numero_pagina = numeracion_inicial + i
        _dibujar_pagina(c, matriz, numero_pagina, total_paginas)
        if logo_path:
            dibujar_logo(c, logo_path)
        c.showPage()

    c.save()


# ----------------------------------------------------------------------------
# Ejemplo de uso
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import random

    def generar_matriz_ejemplo(filas: int, columnas: int) -> List[List[bool]]:
        """Genera una matriz aleatoria solo para poder ver el resultado visual.
        Sustituye esto por tus matrices reales."""
        random.seed(42)
        return [[random.random() < 0.35 for _ in range(columnas)] for _ in range(filas)]

    matriz_ejemplo_1 = generar_matriz_ejemplo(11, 17)

    matriz_ejemplo_2 = [
        [True, False, False, True, False, False, True, False],
        [False, False, True, False, False, True, False, False],
        [True, False, False, False, True, False, False, True],
        [False, True, False, False, False, False, True, False],
        [False, False, True, False, True, False, False, False],
        [True, False, False, False, False, True, False, True],
    ]

    generar_pdf_autodefinidos(
        matrices=[matriz_ejemplo_1, matriz_ejemplo_2],
        ruta_salida="/mnt/user-data/outputs/autodefinidos_ejemplo.pdf",
    )
    print("PDF generado correctamente.")
