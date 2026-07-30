import time

from database import database_manager


# =====================================================
# FUNZIONE DI SUPPORTO
# =====================================================

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
# DATI BASE
# =====================================================

def create_test_pub():

    return {

        "handle": "9999999",

        "title": "Pubblicazione TEST",

        "doi": None,

        "year": "2026",

        "authors": [
            {
                "id": "rpTEST01",
                "name": "Mario",
                "surname": "Rossi"
            }
        ],

        "type": "Articolo",

        "type_driver": "test",

        "venue": None,

        "url": None,

        "keywords": [
            "test",
            "database"
        ],

        "last_update": "999999999"

    }



# =====================================================
# TEST INSERT COMPLETO
# =====================================================

def test_insert():

    pub = create_test_pub()

    print("Inserisco pubblicazione:")
    print(pub["handle"])

    database_manager.sync_database(pub)



# =====================================================
# TEST INSERT CON NULL
# =====================================================

def test_null_values():

    pub = {

        "handle": "9999998",

        "title": "Pub senza metadati",

        "doi": None,

        "year": None,

        "authors": [],

        "type": None,

        "type_driver": None,

        "venue": None,

        "url": None,

        "keywords": [],

        "last_update": "888888888"

    }


    print("Test pubblicazione con NULL")

    database_manager.sync_database(pub)



# =====================================================
# TEST UPDATE CAMPO SINGOLO
# =====================================================

def test_update_title():

    pub = create_test_pub()

    pub["title"] = "Titolo modificato TEST"

    pub["last_update"] = str(int(time.time() * 1000))


    print("Cambio solo titolo")

    database_manager.sync_database(pub)



# =====================================================
# TEST AGGIUNTA KEYWORD
# =====================================================

def test_add_keyword():

    pub = create_test_pub()

    pub["keywords"].append(
        "nuova keyword"
    )

    pub["last_update"] = str(int(time.time() * 1000))


    print("Aggiungo keyword")

    database_manager.sync_database(pub)



# =====================================================
# TEST RIMOZIONE KEYWORD
# =====================================================

def test_remove_keyword():

    pub = create_test_pub()

    pub["keywords"] = [
        "test"
    ]

    pub["last_update"] = str(int(time.time() * 1000))


    print("Tolgo keyword")

    database_manager.sync_database(pub)



# =====================================================
# TEST AGGIUNTA AUTORE
# =====================================================

def test_add_author():

    pub = create_test_pub()


    pub["authors"].append(
        {
            "id": "rpTEST02",
            "name": "Luigi",
            "surname": "Verdi"
        }
    )


    pub["last_update"] = str(int(time.time() * 1000))


    print("Aggiungo autore")

    database_manager.sync_database(pub)



# =====================================================
# TEST RIMOZIONE AUTORE
# =====================================================

def test_remove_author():

    pub = create_test_pub()


    pub["authors"] = []


    pub["last_update"] = str(int(time.time() * 1000))


    print("Tolgo tutti gli autori")

    database_manager.sync_database(pub)



# =====================================================
# AVVIO TEST
# =====================================================


if __name__ == "__main__":


    run_test(
        "INSERT COMPLETO",
        test_insert
    )


    run_test(
        "INSERT CON NULL",
        test_null_values
    )


    run_test(
        "UPDATE TITOLO",
        test_update_title
    )


    run_test(
        "AGGIUNTA KEYWORD",
        test_add_keyword
    )


    run_test(
        "RIMOZIONE KEYWORD",
        test_remove_keyword
    )


    run_test(
        "AGGIUNTA AUTORE",
        test_add_author
    )


    run_test(
        "RIMOZIONE AUTORE",
        test_remove_author
    )