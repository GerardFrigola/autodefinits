from autodefinido_pdf import generar_pdf_autodefinidos

mis_matrices = [[
    [True,  False, True,  False, True,  False, True,  False, True,  False, True],
    [False, False, True,  False, False, False, True,  False, False, False, False],
    [True,  False, False, False, True,  True,  False, False, False, False, False],
    [False, False, True,  False, False, False, False, False, False, True,  False],
    [True,  True,  False, False, False, False, False, True,  False, False, False],
    [False, False, False, False, True,  True,  False, False, False, False, False],
    [True,  False, False, False, False, False, False, True,  False, True,  False],
    [False, False, False, False, False, False, True,  False, False, False, False],
    [True,  True,  False, True,  False, False, False, False, False, False, False],
    [False, False, False, False, False, False, False, True,  False, True,  False],
    [True,  False, False, False, False, True,  False, False, True,  False, False],
    [False, False, False, False, False, False, False, False, False, False, False],
    [True,  True,  False, True,  False, False, False, False, False, False, False],
    [False, False, False, False, False, False, False, False, False, False, False],
    [True,  False, False, False, False, False, False, False, False, False, True],
    [False, False, False, False, False, False, False, False, False, False, False],
    [True,  False, False, True,  False, False, False, False, True,  False, False]
]]

generar_pdf_autodefinidos(
    matrices=mis_matrices,
    ruta_salida="cuadernillo.pdf"
    #logo_path="mi_logo.png",  # opcional
)