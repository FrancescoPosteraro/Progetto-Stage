"""
========================================================
Script utilizzato per valutare in percentuale la presenza di determinati campi in base alla tipologia di pubblicazione
========================================================
"""

from urllib.parse import urlparse, parse_qs
from pathlib import Path
import json, os

JSON_PATH = r"C:\Users\franc\Desktop\Progetto-Stage\publications.json"

campi_da_controllare_rivista = [
    "dc.authority.ancejournal",
    "dc.relation.volume",
    "dc.relation.issue",
    "dc.relation.firstpage",
    "dc.relation.lastpage",
    "dc.type.publicationstatus",
    "dc.publisher.name"
]

campi_da_controllare_convegno = [
    "dc.relation.conferencename",
    "dc.relation.conferencedate",
    "dc.relation.conferenceplace",
    "dc.relation.ispartofbook",
    "dc.publisher.name",
    "dc.relation.firstpage",
    "dc.relation.lastpage",
    "dc.publisher.name"
]

campi_da_controllare_libro = [
    "dc.publisher.name",
    "dc.relation.firstpage",
    "dc.relation.lastpage",
    "dc.relation.ispartofbook",
    "dc.relation.volume",
    "dc.identifier.isbn",
    "dc.publisher.name",
    "dc.publisher.country",
    "dc.type.research"
]

campi_da_controllare_monografia = [
    "dc.identifier.isbn",
    "dc.relation.ispartofseries",
    "dc.publisher.place",
    "dc.publisher.country",
    "dc.publisher.name"
]

campi_da_controllare_curatele = [
    "dc.identifier.isbn",
    "dc.publisher.name",
    "dc.relation.medium",
    "dc.type.research"
]

campi_da_controllare_tesi = [
    "dc.description.phdCourse",
    "dc.coverage.academiccycle",
    "dc.coverage.academicyear",
    "dc.authority.advisor",
    "dc.publisher.name"

]

campi_da_controllare_altro = [
    "dc.type.dcmi",
    "dc.identifier.url",
    "dc.description.generic",
    "dc.description.abstracteng"
]


def analizza_metadati_riviste():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Articolo su rivista"
    ]

    totale = len(articoli)

    print(f"Articoli su rivista trovati: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_rivista:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")
    
    print("\n")

def analizza_metadati_convegni():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Intervento a convegno"
    ]

    totale = len(articoli)

    print(f"Interventi a convegno trovati: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_convegno:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")

    print("\n")


def analizza_metadati_libri():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Contributo in libro"
    ]

    totale = len(articoli)

    print(f"Contributi in Libro trovati: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_libro:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")

    print("\n")

def analizza_metadati_monografia():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Monografia"
    ]

    totale = len(articoli)

    print(f"Monografie trovate: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_monografia:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")
    
    print("\n")

def analizza_metadati_curatele():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Curatele"
    ]

    totale = len(articoli)

    print(f"Curatele trovati: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_curatele:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")
    
    print("\n")

def analizza_metadati_tesi():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Tesi di dottorato"
    ]

    totale = len(articoli)

    print(f"Tesi trovate: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_tesi:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")
    
    print("\n")

def analizza_metadati_altro():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)

    articoli = [
        pub for pub in pubblicazioni
        if pub.get("dc.type") == "Altro"
    ]

    totale = len(articoli)

    print(f"Altro trovati: {totale}\n")

    if totale == 0:
        return

    risultati = {}

    for campo in campi_da_controllare_altro:
        presenti = sum(
            1 for articolo in articoli
            if campo in articolo and articolo[campo] not in [None, "", []]
        )

        percentuale = (presenti / totale) * 100

        risultati[campo] = percentuale

    print("Presenza metadati:\n")

    for campo, percentuale in risultati.items():
        print(f"{campo:40} {percentuale:.2f}%")
    
    print("\n")

analizza_metadati_riviste()
analizza_metadati_convegni()
analizza_metadati_libri()
analizza_metadati_monografia()
analizza_metadati_curatele()
analizza_metadati_tesi()
analizza_metadati_altro()