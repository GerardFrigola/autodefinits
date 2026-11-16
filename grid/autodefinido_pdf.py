"""

Generador de paginas imprimibles para autodefinidos (crucigramas sin numeros/letras).
Incluye funciones para validar la matriz, calcular la geometria de la cuadricula y obtener los inicios de respuestas.

Cada autodefinido se representa como una matriz (lista de listas) de booleanos:
    True  -> casilla de DEFINICION (se pinta mas oscura)
    False -> casilla de RESPUESTA   (se deja clara, para escribir la letra)

El programa genera un PDF en tamano A5 vertical, con una pagina por matriz,
cuadricula centrada con celdas cuadradas, bordes de contorno en cada celda,
margenes libres (para numero de pagina y logo) y numero de pagina automatico.

Requiere: reportlab  (pip install reportlab)
"""

from __future__ import annotations

import os
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
COLOR_FLECHA = Color(0, 0, 0)

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


def _obtener_inicios_respuestas(
    matriz: Sequence[Sequence[bool]],
    fila: int,
    columna: int,
    min_letters_per_word: int,
) -> List[tuple[int, int, str, str]]:
    filas = len(matriz)
    columnas = len(matriz[0])

    if fila == 0 and columna == 0:
        candidates = [
            (fila, columna + 1, "right", "down"),
            (fila + 1, columna, "below", "right"),
        ]
    elif fila == 0:
        if columna == columnas - 1:
            candidates = [(fila + 1, columna, "below", "down")]
        else:
            candidates = [
                (fila, columna + 1, "right", "down"),
                (fila + 1, columna, "below", "down"),
            ]
    elif columna == 0:
        if fila == filas - 1:
            candidates = [(fila, columna + 1, "right", "right")]
        else:
            candidates = [
                (fila, columna + 1, "right", "right"),
                (fila + 1, columna, "below", "right"),
            ]
    elif fila == filas - 1 and columna == columnas - 1:
        candidates = []
    elif fila == filas - 1:
        candidates = [(fila, columna + 1, "right", "right")]
    elif columna == columnas - 1:
        candidates = [(fila + 1, columna, "below", "down")]
    else:
        candidates = [
            (fila, columna + 1, "right", "right"),
            (fila + 1, columna, "below", "down"),
        ]

    return [
        (start_row, start_column, entry_side, direction)
        for start_row, start_column, entry_side, direction in candidates
        if start_row < filas
        and start_column < columnas
        and not matriz[start_row][start_column]
        and _tiene_longitud_minima(
            matriz, start_row, start_column, direction, min_letters_per_word
        )
    ]


def _tiene_longitud_minima(
    matriz: Sequence[Sequence[bool]],
    fila: int,
    columna: int,
    direction: str,
    min_letters_per_word: int,
) -> bool:
    delta_fila, delta_columna = (1, 0) if direction == "down" else (0, 1)
    longitud = 0

    while (
        fila < len(matriz)
        and columna < len(matriz[0])
        and not matriz[fila][columna]
    ):
        longitud += 1
        fila += delta_fila
        columna += delta_columna

    return longitud >= min_letters_per_word


def _dibujar_flechas(c: canvas.Canvas, flechas: Sequence[tuple[str, str]],
                    x: float, y: float, cell: float) -> None:
    if not flechas:
        return

    c.setStrokeColor(COLOR_FLECHA)
    c.setFillColor(COLOR_FLECHA)
    c.setLineWidth(max(0.6, cell * 0.025))
    head_length = cell * 0.12
    head_half_width = cell * 0.08

    for entry_side, direction in flechas:
        center_x = x + cell * 0.5
        center_y = y + cell * 0.5
        arrow_head_length = head_length
        arrow_head_half_width = head_half_width

        if entry_side == "right" and direction == "down":
            arrow_head_length = cell * 0.06
            arrow_head_half_width = cell * 0.05
            bend_x = x + cell * 0.25
            bend_y = y + cell * (11 / 12)
            tip_x = bend_x
            tip_y = y + cell * (2 / 3)
            c.line(x, bend_y, bend_x, bend_y)
            c.line(bend_x, bend_y, tip_x, tip_y + arrow_head_length)
        elif entry_side == "below" and direction == "right":
            arrow_head_length = cell * 0.06
            arrow_head_half_width = cell * 0.05
            bend_x = x + cell * 0.125
            bend_y = y + cell * 0.75
            tip_x = x + cell * 0.375
            tip_y = bend_y
            c.line(bend_x, y + cell, bend_x, bend_y)
            c.line(bend_x, bend_y, tip_x - arrow_head_length, tip_y)
        elif direction == "right":
            arrow_head_length = cell * 0.06
            arrow_head_half_width = cell * 0.05
            tip_x = x + cell * 0.25
            tip_y = y + cell * (2 / 3)
            c.line(x, tip_y, tip_x - arrow_head_length, tip_y)
        else:
            arrow_head_length = cell * 0.06
            arrow_head_half_width = cell * 0.05
            tip_x = center_x
            tip_y = y + cell * 0.75
            c.line(center_x, y + cell, center_x, tip_y + arrow_head_length)

        path = c.beginPath()
        path.moveTo(tip_x, tip_y)
        if direction == "right":
            path.lineTo(tip_x - arrow_head_length, tip_y - arrow_head_half_width)
            path.lineTo(tip_x - arrow_head_length, tip_y + arrow_head_half_width)
        else:
            path.lineTo(tip_x - arrow_head_half_width, tip_y + arrow_head_length)
            path.lineTo(tip_x + arrow_head_half_width, tip_y + arrow_head_length)
        path.close()
        c.drawPath(path, stroke=0, fill=1)


def _dibujar_pagina(c: canvas.Canvas, matriz: Sequence[Sequence[bool]],
                     numero_pagina: Optional[int], total_paginas: Optional[int],
                     min_letters_per_word: int) -> None:
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

    flechas_por_casilla = {}
    for fila_idx, fila in enumerate(matriz):
        for col_idx, es_definicion in enumerate(fila):
            if not es_definicion:
                continue
            inicios = _obtener_inicios_respuestas(
                matriz, fila_idx, col_idx, min_letters_per_word
            )
            for start_row, start_column, entry_side, direction in inicios:
                posiciones = flechas_por_casilla.setdefault(
                    (start_row, start_column), []
                )
                flecha = (entry_side, direction)
                if flecha not in posiciones:
                    posiciones.append(flecha)

    for (fila, columna), flechas in flechas_por_casilla.items():
        x_flecha = x0 + columna*cell
        y_flecha = y0 + alto_grid - (fila + 1)*cell
        _dibujar_flechas(c, flechas, x_flecha, y_flecha, cell)

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
    min_letters_per_word: int = 2,
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
        min_letters_per_word: longitud minima para que una respuesta tenga flecha.
    """
    if not matrices:
        raise ValueError("Debes proporcionar al menos una matriz.")
    if min_letters_per_word < 1:
        raise ValueError("min_letters_per_word debe ser al menos 1.")

    total_paginas = len(matrices)
    c = canvas.Canvas(ruta_salida, pagesize=A5)

    for i, matriz in enumerate(matrices):
        numero_pagina = numeracion_inicial + i
        _dibujar_pagina(
            c, matriz, numero_pagina, total_paginas, min_letters_per_word
        )
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

    outputs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"
    )
    os.makedirs(outputs_dir, exist_ok=True)
    generar_pdf_autodefinidos(
        matrices=[matriz_ejemplo_1, matriz_ejemplo_2],
        ruta_salida=os.path.join(outputs_dir, "autodefinidos_ejemplo.pdf"),
    )
    print("PDF generado correctamente.")
