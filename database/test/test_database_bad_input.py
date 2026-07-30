from database import database_manager
from datetime import datetime
import time


def run_test(nome, funzione):

    print("\n" + "=" * 60)
    print("TEST:", nome)
    print("=" * 60)

    try:
        funzione()
        print("TEST COMPLETATO")

    except Exception as e:
        print("TEST FALLITO")
        print("ERRORE:")
        print(e)



# =====================================================
# PUBBLICAZIONE BASE
# =====================================================

def create_pub():

    return {

        "handle": "8888888",

        "title": "Test tipi database",

        "doi": f"10.1234/test-{time.time_ns()}",

        "year": "2026",

        "authors": [],

        "type": "TEST",

        "type_driver": "TEST",

        "venue": "TEST",

        "url": "https://test.com",

        "keywords": [],

        "last_update": str(int(time.time() * 1000))

    }



# =====================================================
# TEST INSERIMENTO BASE
# =====================================================

pub = create_pub()

run_test(
    "PUBBLICAZIONE BASE",
    lambda: database_manager.sync_database(pub)
)



# =====================================================
# TEST LAST UPDATE VECCHIO
# =====================================================

pub = create_pub()

pub["handle"] = "8888886"

# data vecchia (1970)
pub["last_update"] = "999999999"


run_test(
    "LAST UPDATE VECCHIO - NESSUN UPDATE",
    lambda: database_manager.sync_database(pub)
)


# =====================================================
# TEST YEAR NULL
# =====================================================

pub = create_pub()

pub["handle"] = "8888884"

pub["year"] = None


run_test(
    "YEAR NULL",
    lambda: database_manager.sync_database(pub)
)



# =====================================================
# TEST STRINGHE STRANE
# =====================================================

pub = create_pub()

pub["handle"] = "8888883"

pub["title"] = 12345


run_test(
    "TITLE INT AL POSTO DI STRING",
    lambda: database_manager.sync_database(pub)
)



pub = create_pub()

pub["handle"] = "8888882"

pub["doi"] = 12345


run_test(
    "DOI INT AL POSTO DI STRING",
    lambda: database_manager.sync_database(pub)
)



# =====================================================
# TEST LISTE
# =====================================================

pub = create_pub()

pub["handle"] = "8888881"

pub["authors"] = None


run_test(
    "AUTHORS NULL",
    lambda: database_manager.sync_database(pub)
)



pub = create_pub()

pub["handle"] = "8888880"

pub["keywords"] = None


run_test(
    "KEYWORDS NULL",
    lambda: database_manager.sync_database(pub)
)



# =====================================================
# TEST AUTORE MALFORMATO
# =====================================================

pub = create_pub()

pub["handle"] = "8888879"

pub["authors"] = [

    {
        "id": "rpTEST",
        "name": None,
        "surname": None
    }

]


run_test(
    "AUTORE CON CAMPI NULL",
    lambda: database_manager.sync_database(pub)
)