#!/usr/bin/env python3
"""
parse_viccionari.py

Parseja el dump XML de Viccionari (ca.wiktionary.org) i extreu, per a cada
paraula catalana, la seva categoria gramatical i les seves definicions.

Ús:
    python parse_viccionari.py cawiktionary-latest-pages-articles.xml -o sortida.csv

Accepta tant el .xml descomprimit com el .xml.bz2 original (el detecta per
l'extensió i el llegeix en mode streaming, sense carregar-lo sencer a memòria).

Requereix:
    pip install mwparserfromhell
"""

import argparse
import bz2
import csv
import re
import sys
import xml.etree.ElementTree as ET

import mwparserfromhell

# Etiquetes de secció (nivell 3, "=== ... ===") que Viccionari fa servir per
# indicar la categoria gramatical. La llista no és exhaustiva: qualsevol
# capçalera de nivell 3 que no hi aparegui es descarta (etimologia,
# pronunciació, referències, etc. no són categories gramaticals).
POS_HEADERS = {
    "nom": "nom",
    "nom propi": "nom propi",
    "verb": "verb",
    "adjectiu": "adjectiu",
    "adverbi": "adverbi",
    "pronom": "pronom",
    "preposició": "preposició",
    "preposicio": "preposició",
    "conjunció": "conjunció",
    "conjuncio": "conjunció",
    "interjecció": "interjecció",
    "interjeccio": "interjecció",
    "determinant": "determinant",
    "article": "article",
    "numeral": "numeral",
    "prefix": "prefix",
    "sufix": "sufix",
    "locució": "locució",
    "locucio": "locució",
    "sigla": "sigla",
    "símbol": "símbol",
    "simbol": "símbol",
}

# Namespace que Wikimedia posa a les etiquetes del XML d'exportació.
# En comptes d'assumir-ne un de fix, el detectem del primer element llegit.
NS_RE = re.compile(r"\{.*\}")


def strip_ns(tag: str) -> str:
    return NS_RE.sub("", tag)


def open_dump(path: str):
    if path.endswith(".bz2"):
        return bz2.open(path, "rb")
    return open(path, "rb")


def iter_pages(path: str):
    """Genera (title, ns, is_redirect, wikitext) per a cada <page> del dump,
    llegint en streaming amb iterparse per no carregar tot el fitxer a RAM."""
    f = open_dump(path)
    context = ET.iterparse(f, events=("end",))
    for event, elem in context:
        tag = strip_ns(elem.tag)
        if tag == "page":
            title = None
            ns = None
            is_redirect = False
            text = None
            for child in elem:
                ctag = strip_ns(child.tag)
                if ctag == "title":
                    title = child.text
                elif ctag == "ns":
                    ns = child.text
                elif ctag == "redirect":
                    is_redirect = True
                elif ctag == "revision":
                    for rchild in child:
                        if strip_ns(rchild.tag) == "text":
                            text = rchild.text
            yield title, ns, is_redirect, text
            # Alliberem l'element (i els seus fills) per no acumular memòria.
            elem.clear()
    f.close()


def extract_language_section(wikitext: str, language: str = "Català"):
    """Retorna el text de la secció d'un idioma concret (capçalera nivell 2),
    tallant just abans de la següent capçalera de nivell 2, si n'hi ha."""
    if not wikitext:
        return None
    pattern = re.compile(
        r"^==\s*" + re.escape(language) + r"\s*==\s*$", re.MULTILINE
    )
    m = pattern.search(wikitext)
    if not m:
        return None
    start = m.end()
    next_h2 = re.search(r"^==[^=].*==\s*$", wikitext[start:], re.MULTILINE)
    end = start + next_h2.start() if next_h2 else len(wikitext)
    return wikitext[start:end]


def split_pos_subsections(section_text: str):
    """Divideix la secció d'idioma en blocs per capçalera de nivell 3
    (=== Nom ===, === Verb ===, etc.) i retorna (etiqueta_normalitzada, cos)."""
    if not section_text:
        return []
    header_re = re.compile(r"^===\s*([^=]+?)\s*===\s*$", re.MULTILINE)
    headers = list(header_re.finditer(section_text))
    blocks = []
    for i, h in enumerate(headers):
        raw_label = h.group(1).strip().lower()
        # Alguns POS porten un número al darrere ("Nom 2") si hi ha diverses
        # etimologies; ho normalitzem traient dígits finals.
        clean_label = re.sub(r"\s*\d+$", "", raw_label).strip()
        if clean_label not in POS_HEADERS:
            continue
        body_start = h.end()
        body_end = (
            headers[i + 1].start() if i + 1 < len(headers) else len(section_text)
        )
        blocks.append((POS_HEADERS[clean_label], section_text[body_start:body_end]))
    return blocks


def clean_wikitext(raw: str) -> str:
    wikicode = mwparserfromhell.parse(raw)
    text = wikicode.strip_code(normalize=True, collapse=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_definitions(body_text: str, max_defs: int = None):
    """Extreu les línies de definició (# ...), ignorant sub-elements (## ...)
    que solen ser exemples d'ús o cites, no definicions pròpiament dites."""
    defs = []
    for line in body_text.splitlines():
        if re.match(r"^#[^#*:]", line):  # "#" però no "##", "#*", "#:"
            raw_def = line[1:].strip()
            cleaned = clean_wikitext(raw_def)
            if cleaned:
                defs.append(cleaned)
        if max_defs and len(defs) >= max_defs:
            break
    return defs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", help="Fitxer cawiktionary-*-pages-articles.xml(.bz2)")
    parser.add_argument("-o", "--output", default="viccionari_ca.csv")
    parser.add_argument(
        "--min-len", type=int, default=1, help="Longitud mínima de la paraula"
    )
    parser.add_argument(
        "--max-len", type=int, default=None, help="Longitud màxima de la paraula"
    )
    parser.add_argument(
        "--max-defs-per-pos",
        type=int,
        default=3,
        help="Màxim de definicions a exportar per paraula+categoria",
    )
    parser.add_argument(
        "--only-single-word",
        action="store_true",
        help="Descarta títols amb espais, guions o apòstrofs (locucions, etc.)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=20000,
        help="Cada quantes pàgines processades mostrar un missatge de progrés",
    )
    args = parser.parse_args()

    out_f = open(args.output, "w", newline="", encoding="utf-8")
    writer = csv.writer(out_f)
    writer.writerow(
        ["paraula", "longitud", "categoria_gramatical", "definicio", "num_definicions_totals", "font"]
    )

    pages_seen = 0
    words_written = 0

    for title, ns, is_redirect, text in iter_pages(args.dump):
        pages_seen += 1
        if args.progress_every and pages_seen % args.progress_every == 0:
            print(
                f"... {pages_seen} pàgines llegides, {words_written} paraules exportades",
                file=sys.stderr,
            )

        if ns != "0" or is_redirect or not title or not text:
            continue
        if args.only_single_word and re.search(r"[\s\-'ʼ]", title):
            continue
        if len(title) < args.min_len:
            continue
        if args.max_len and len(title) > args.max_len:
            continue

        ca_section = extract_language_section(text, "Català")
        if not ca_section:
            continue

        for pos_label, body in split_pos_subsections(ca_section):
            all_defs = extract_definitions(body)
            if not all_defs:
                continue
            defs_to_write = all_defs[: args.max_defs_per_pos]
            for d in defs_to_write:
                writer.writerow(
                    [title, len(title), pos_label, d, len(all_defs), "Viccionari (CC BY-SA)"]
                )
                words_written += 1

    out_f.close()
    print(
        f"Fet. {pages_seen} pàgines llegides, {words_written} files (paraula+definició) exportades a {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
