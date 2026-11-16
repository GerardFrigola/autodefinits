# Autodefinits

Projecte per generar graelles imprimibles d'autodefinits i per fer proves de
processament de paraules en catala.

## Contingut

- `grid/create_grids.py`: cerca distribucions de caselles de definicio en una
  graella de 17 files per 11 columnes. Fixa les definicions de la primera fila
  i la primera columna, prova combinacions a les files interiors i descarta
  distribucions que incompleixen les restriccions o deixen les caselles de
  resposta desconnectades. Per defecte busca fins a 50 distribucions.
- `grid/autodefinido_pdf.py`: dibuixa cada distribucio en una pagina A5; les
  caselles `True` son de definicio (fosques) i les `False` son de resposta
  (blanques). Inclou fletxes centrades a la primera casella blanca de cada
  resposta; les respostes amb un gir es dibuixen amb forma d'angle i les que
  no arriben a la longitud minima no tenen fletxa. Afegeix la numeracio de
  pagina i admet un logotip opcional.
- `cat_pos_tagging.py`: carrega el model gran de catala de spaCy, selecciona
  50 paraules amb una mostra determinista i imprimeix la categoria gramatical
  (POS) del primer token de cada paraula.
- `data/`: conté CSV de paraules, definicions i dades del Paraulògic.
- `test.ipynb`: quadern d'experimentacio.

## Requisits

Es recomana Python 3.10 o posterior. Instal·la les dependències Python:

```bash
python -m venv .venv
```

Activa l'entorn virtual i instal·la les dependències. A PowerShell:

```bash
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

El generador de graelles nomes necessita ReportLab. Per executar el POS
tagging, calen tambe els dos models de spaCy que el script importa:

```bash
python -m spacy download ca_core_news_lg
python -m spacy download ca_core_news_trf
```

El model `ca_core_news_trf` s'importa al script, tot i que actualment no
s'utilitza en el processament.

## Ús

Des de la carpeta arrel del projecte, genera el PDF:

```bash
python grid/create_grids.py
```

El programa crea `outputs/` a l'arrel del projecte si encara no existeix i hi
escriu `quadernet_min2.pdf`. El valor `2` correspon a
`MIN_LETTERS_PER_WORD`; les dimensions, els limits de definicions i el nombre
maxim de candidats es poden ajustar a `grid/create_grids.py`.

Per desar també la sortida de consola a `outputs/output.txt` des de CMD, fes
servir el comandament de `cmd.txt` des de l'arrel del projecte.

Per executar el POS tagging:

```bash
python cat_pos_tagging.py
```

Aquest script espera llegir `data/paraules.csv`, pero el fitxer de paraules
inclòs al projecte es troba actualment a `data/paraulogic/paraules.csv`.
Cal corregir la ruta del CSV al script o posar el fitxer a la ubicacio
esperada abans d'executar-lo.

## Dades i lògica de la cerca

La creació de cada graella és una cerca amb backtracking: es fixa una part de
la geometria, s'intenta completar fila a fila i es descarten aviat les branques
que ja no poden arribar a una solució vàlida.

### Representació i geometria inicial

- Les dimensions són 17 files per 11 columnes. Les coordenades del codi
  comencen a `(0, 0)`.
- La matriu de la graella és booleana: `True` vol dir casella de definició i
  `False`, casella de resposta.
- Hi ha 14 definicions fixes: totes les columnes parelles de la fila 0 i totes
  les files parelles de la columna 0. La casella `(0, 0)` és comuna a les dues
  regles i només es compta una vegada.
- Les altres posicions no són necessàriament disponibles per a definicions.
  `initialize_available_cells()` crea una segona matriu que marca on encara
  es pot provar de posar-ne una. Les `X` del dibuix inicial volen dir
  «prohibit posar-hi una definició»; no són blocs negres de la graella final i
  continuen sent caselles de resposta (`False`).
- També s'impedeixen posicions de vora que, amb `MIN_LETTERS_PER_WORD = 2`,
  deixarien respostes massa curtes o sense continuació possible.

Esquema de les posicions fixes i inicialment prohibides (`D` = definició fixa,
`X` = no disponible per a noves definicions, `.` = candidata):

```text
D.D.D.D.D.D
.X.X.X.X.XX
D.........X
.X.........
D..........
.X.........
D..........
.X.........
D..........
.X.........
D..........
.X.........
D..........
.X.........
D..........
.X.......XX
DXX......XX
```

### Cerca fila a fila

1. `init_row_patterns()` construeix les combinacions de zero, una o dues
   columnes entre la 1 i la 10. Les barreja amb `random.shuffle()`, així que
   l'ordre en què es visiten les opcions pot canviar entre execucions.
2. El DFS comença a la fila 1, perquè la fila 0 ja està fixada. Per a cada fila
   filtra les combinacions i conserva només les que encara estan disponibles.
   A la fila 1 s'exigeixen dues definicions i es descarten parelles de
   columnes consecutives que comencen en una columna parella. A les dues
   últimes files, si hi ha dues definicions, han d'estar separades per almenys
   tres columnes.
3. Per cada combinació candidata crea còpies de l'estat de la branca actual,
   marca les noves definicions a la graella i actualitza les posicions que
   queden prohibides. Aquesta actualització aplica regles locals per evitar
   que les noves caselles tallin les possibles respostes horitzontals o
   verticals de longitud mínima, sobretot a les vores i al voltant de les
   definicions ja posades.
4. Actualitza el recompte de definicions de cada columna. Si una columna
   supera el màxim de tres, es descarta la branca sense explorar-ne les files
   restants.
5. `exists_future_solution()` aplica dues podes globals: rebutja més de 44
   definicions i rebutja una branca si, fins i tot posant dues definicions a
   cadascuna de les files pendents, ja no podria arribar al mínim de 38.
6. Si la branca passa les podes, el DFS continua amb la fila següent. En
   arribar al final, només accepta graelles amb almenys 38 definicions, entre
   una i tres definicions a cadascuna de les columnes 1 a 10 i totes les
   caselles de resposta connectades ortogonalment. La connectivitat es comprova
   amb un recorregut en amplada (`BFS`) des d'una casella de resposta.

La cerca s'atura quan troba el nombre demanat de candidats: la funció té un
valor per defecte de 10, però l'execució directa del script li passa 50.
Després, cada matriu trobada es converteix en una pàgina A5 del PDF.

**Nota sobre el límit actual:** `MAX_TOTAL_DEFS` es calcula com 14 definicions
fixes més dues per cadascuna de les 15 files de `INNER_ROWS` (44 en total),
però el DFS recorre les files 1 a 16. Per tant, el límit de 44 també poda
branques mentre explora l'última fila; el càlcul del màxim no compta aquesta
fila com a fila interior.

Els CSV de `data/paraulogic/` contenen les lletres i paraules per data; el CSV
`data/definicions.csv` conté definicions. Aquests fitxers no intervenen en la
generacio actual de graelles.