import spacy
import ca_core_news_trf
import ca_core_news_lg
import pandas as pd
from time import perf_counter
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


def load_model():
    print("Carregant el model de llenguatge català...")
    start = perf_counter()
    nlp = ca_core_news_lg.load()
    print(f"    Model carregat amb èxit en {perf_counter() - start:.2f} segons.\n")

    return nlp

def load_data():
    print("Carregant les dades...")
    paraules = pd.read_csv("data/paraules.csv").sample(50, random_state=42)
    print("    Dades carregades amb èxit.\n")

    return paraules

def perform_pos_tagging(nlp, paraules):
    start = perf_counter()
    print("Executant el POS tagging...")

    docs = nlp.pipe(paraules["paraula"])

    paraules["pos"] = [
        doc[0].pos_
        for doc in docs
    ]

    for r in paraules.itertuples():
        print(f"{r.paraula} -> {r.pos}")

    print(f"     POS tagging completat en {perf_counter() - start:.2f} segons.")


if __name__ == "__main__":
    nlp = load_model()

    paraules = load_data()

    perform_pos_tagging(nlp, paraules)
