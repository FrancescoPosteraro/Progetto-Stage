"""
========================================================
Nome File: test_database_manager.py

DESCRIZIONE:
Test automatici con pytest per verificare il funzionamento
del modulo database_manager.

I test verificano l'inserimento e l'aggiornamento delle
pubblicazioni, la gestione degli autori e delle keyword,
la sincronizzazione delle relazioni e il comportamento
in presenza di dati incompleti o anomali.

========================================================
"""

from database import database_manager
import time


def create_pub():

    return {
        "handle": "ZZZ_TEST_PUBLICATION_0001",
        "title": "ZZZ_Titolo_Test_Database_0001",
        "doi": f"10.0000/zzz-test-{time.time_ns()}",
        "year": "2099",
        "authors": [],
        "type": "ZZZ_TYPE_TEST",
        "type_driver": "ZZZ_DRIVER_TEST",
        "venue": "ZZZ_VENUE_TEST",
        "url": "https://invalid.test/zzz-publication",
        "keywords": [],
        "last_update": str(int(time.time() * 1000))
    }


# =====================================================
# CONNESSIONE AL DATABASE
# Verifica che get_connection utilizzi psycopg.connect
# con i parametri configurati.
# =====================================================
def test_get_connection():

    connection = database_manager.get_connection()

    assert connection is not None

    connection.close()


# =====================================================
# INSERIMENTO PUBBLICAZIONE
# Verifica che insert_publication_table inserisca
# correttamente una pubblicazione nel database.
# =====================================================
def test_insert_publication_table():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            cur.execute(
                """
                SELECT handle
                FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

            result = cur.fetchone()

            assert result is not None
            assert result[0] == pub["handle"]

        con.rollback()


# =====================================================
# INSERIMENTO PUBBLICAZIONE CON NULL
# Verifica che insert_publication_table accetti
# correttamente i valori NULL nei campi opzionali.
# =====================================================
def test_insert_publication_table_null():

    pub = create_pub()

    pub["doi"] = None
    pub["year"] = None
    pub["type_driver"] = None
    pub["venue"] = None
    pub["url"] = None

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            cur.execute(
                """
                SELECT doi, year, type_driver, venue, url
                FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

            result = cur.fetchone()

            assert result == (
                None,
                None,
                None,
                None,
                None
            )

        con.rollback()


# =====================================================
# INSERIMENTO AUTORE
# Verifica che insert_author inserisca un nuovo autore
# e restituisca correttamente il suo identificativo.
# =====================================================
def test_insert_author():

    author = {
        "id": "ZZZ_TEST_AUTHOR_0001",
        "name": "ZZZ_Nome_Autore_0001",
        "surname": "ZZZ_Cognome_Autore_0001"
    }

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            result = database_manager.insert_author(cur, author)

            assert result == author["id"]

            cur.execute(
                """
                SELECT id, name, surname
                FROM authors
                WHERE id = %s
                """,
                (author["id"],)
            )

            row = cur.fetchone()

            assert row == (
                "ZZZ_TEST_AUTHOR_0001",
                "ZZZ_Nome_Autore_0001",
                "ZZZ_Cognome_Autore_0001"
            )

        con.rollback()


# =====================================================
# AUTORE GIÀ PRESENTE
# Verifica che insert_author non crei duplicati
# e restituisca l'id dell'autore già presente.
# =====================================================
def test_insert_author_existing():

    author = {
        "id": "ZZZ_TEST_AUTHOR_0002",
        "name": "ZZZ_Nome_Autore_0002",
        "surname": "ZZZ_Cognome_Autore_0002"
    }

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_author(cur, author)

            result = database_manager.insert_author(cur, author)

            assert result == author["id"]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM authors
                WHERE id = %s
                """,
                (author["id"],)
            )

            count = cur.fetchone()[0]

            assert count == 1

        con.rollback()


# =====================================================
# COLLEGAMENTO AUTORE-PUBBLICAZIONE
# Verifica che link_author_publication crei correttamente
# il collegamento tra una pubblicazione e un autore.
# =====================================================
def test_link_author_publication():

    pub = create_pub()

    author = {
        "id": "ZZZ_TEST_AUTHOR_0003",
        "name": "ZZZ_Nome_Autore_0003",
        "surname": "ZZZ_Cognome_Autore_0003"
    }

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)
            database_manager.insert_author(cur, author)

            database_manager.link_author_publication(
                cur,
                pub["handle"],
                author["id"]
            )

            cur.execute(
                """
                SELECT publication_handle, author_id
                FROM publications_authors
                WHERE publication_handle = %s
                AND author_id = %s
                """,
                (pub["handle"], author["id"])
            )

            result = cur.fetchone()

            assert result == (
                pub["handle"],
                author["id"]
            )

        con.rollback()


# =====================================================
# COLLEGAMENTO AUTORE-PUBBLICAZIONE DUPLICATO
# Verifica che lo stesso collegamento non venga inserito
# più di una volta.
# =====================================================
def test_link_author_publication_duplicate():

    pub = create_pub()

    author = {
        "id": "ZZZ_TEST_AUTHOR_0004",
        "name": "ZZZ_Nome_Autore_0004",
        "surname": "ZZZ_Cognome_Autore_0004"
    }

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)
            database_manager.insert_author(cur, author)

            database_manager.link_author_publication(
                cur,
                pub["handle"],
                author["id"]
            )

            database_manager.link_author_publication(
                cur,
                pub["handle"],
                author["id"]
            )

            cur.execute(
                """
                SELECT COUNT(*)
                FROM publications_authors
                WHERE publication_handle = %s
                AND author_id = %s
                """,
                (pub["handle"], author["id"])
            )

            count = cur.fetchone()[0]

            assert count == 1

        con.rollback()


# =====================================================
# INSERIMENTO KEYWORD
# Verifica che insert_keyword inserisca una nuova keyword
# e restituisca correttamente il suo identificativo.
# =====================================================
def test_insert_keyword():

    keyword = "ZZZ_KEYWORD_TEST_0001"

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            result = database_manager.insert_keyword(cur, keyword)

            assert result is not None

            cur.execute(
                """
                SELECT id, name
                FROM keywords
                WHERE name = %s
                """,
                (keyword,)
            )

            row = cur.fetchone()

            assert row is not None
            assert row[1] == keyword
            assert row[0] == result

        con.rollback()


# =====================================================
# KEYWORD GIÀ PRESENTE
# Verifica che insert_keyword non crei duplicati
# e restituisca l'id della keyword già presente.
# =====================================================
def test_insert_keyword_existing():

    keyword = "ZZZ_KEYWORD_TEST_0002"

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            first_id = database_manager.insert_keyword(cur, keyword)

            second_id = database_manager.insert_keyword(cur, keyword)

            assert second_id == first_id

            cur.execute(
                """
                SELECT COUNT(*)
                FROM keywords
                WHERE name = %s
                """,
                (keyword,)
            )

            count = cur.fetchone()[0]

            assert count == 1

        con.rollback()


# =====================================================
# COLLEGAMENTO KEYWORD-PUBBLICAZIONE
# Verifica che link_keyword_publication crei correttamente
# il collegamento tra una pubblicazione e una keyword.
# =====================================================
def test_link_keyword_publication():

    pub = create_pub()

    keyword = "ZZZ_KEYWORD_TEST_0003"

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            keyword_id = database_manager.insert_keyword(cur, keyword)

            database_manager.link_keyword_publication(
                cur,
                pub["handle"],
                keyword_id
            )

            cur.execute(
                """
                SELECT publication_handle, keyword_id
                FROM publications_keywords
                WHERE publication_handle = %s
                AND keyword_id = %s
                """,
                (pub["handle"], keyword_id)
            )

            result = cur.fetchone()

            assert result == (
                pub["handle"],
                keyword_id
            )

        con.rollback()


# =====================================================
# COLLEGAMENTO KEYWORD-PUBBLICAZIONE DUPLICATO
# Verifica che lo stesso collegamento non venga inserito
# più di una volta.
# =====================================================
def test_link_keyword_publication_duplicate():

    pub = create_pub()

    keyword = "ZZZ_KEYWORD_TEST_0004"

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            keyword_id = database_manager.insert_keyword(cur, keyword)

            database_manager.link_keyword_publication(
                cur,
                pub["handle"],
                keyword_id
            )

            database_manager.link_keyword_publication(
                cur,
                pub["handle"],
                keyword_id
            )

            cur.execute(
                """
                SELECT COUNT(*)
                FROM publications_keywords
                WHERE publication_handle = %s
                AND keyword_id = %s
                """,
                (pub["handle"], keyword_id)
            )

            count = cur.fetchone()[0]

            assert count == 1

        con.rollback()


# =====================================================
# RECUPERO PUBBLICAZIONE
# Verifica che get_publication recuperi correttamente
# una pubblicazione tramite il suo handle.
# =====================================================
def test_get_publication():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            result = database_manager.get_publication(
                cur,
                pub["handle"]
            )

            assert result["handle"] == pub["handle"]
            assert result["title"] == pub["title"]
            assert result["doi"] == pub["doi"]
            assert result["year"] == int(pub["year"])
            assert result["type"] == pub["type"]
            assert result["type_driver"] == pub["type_driver"]
            assert result["venue"] == pub["venue"]
            assert result["url"] == pub["url"]
            assert result["last_update"] == int(pub["last_update"])
            assert result["authors"] == []
            assert result["keywords"] == []

        con.rollback()


# =====================================================
# PUBBLICAZIONE NON ESISTENTE
# Verifica che get_publication restituisca None
# quando l'handle non è presente nel database.
# =====================================================
def test_get_publication_not_found():

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            result = database_manager.get_publication(
                cur,
                "ZZZ_HANDLE_NON_ESISTENTE_0001"
            )

            assert result is None

        con.rollback()


# =====================================================
# AGGIORNAMENTO DATI PUBBLICAZIONE
# Verifica che update_publication_table aggiorni
# solo i dati modificati e last_update.
# =====================================================
def test_update_publication_table():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            pub["title"] = "ZZZ_Titolo_Aggiornato_0001"
            pub["last_update"] = str(int(time.time() * 1000))

            database_manager.update_publication_table(cur, pub)

            cur.execute(
                """
                SELECT title, last_update
                FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

            result = cur.fetchone()

            assert result[0] == "ZZZ_Titolo_Aggiornato_0001"
            assert result[1] == int(pub["last_update"])

        con.rollback()


# =====================================================
# RECUPERO AUTORI PUBBLICAZIONE
# Verifica che get_publication_authors restituisca
# correttamente gli id degli autori collegati.
# =====================================================
def test_get_publication_authors():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            author = {
                "id": "ZZZ_TEST_AUTHOR_GET_0001",
                "name": "ZZZ_Nome_Autore_Get_0001",
                "surname": "ZZZ_Cognome_Autore_Get_0001"
            }

            database_manager.insert_author(cur, author)

            database_manager.link_author_publication(
                cur,
                pub["handle"],
                author["id"]
            )

            result = database_manager.get_publication_authors(
                cur,
                pub["handle"]
            )

            assert result == {"ZZZ_TEST_AUTHOR_GET_0001"}

        con.rollback()


# =====================================================
# SINCRONIZZAZIONE AUTORI
# Verifica che sync_authors aggiunga un nuovo autore
# e crei il relativo collegamento con la pubblicazione.
# =====================================================
def test_sync_authors():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            author = {
                "id": "ZZZ_TEST_AUTHOR_SYNC_0001",
                "name": "ZZZ_Nome_Autore_Sync_0001",
                "surname": "ZZZ_Cognome_Autore_Sync_0001"
            }

            pub["authors"] = [author]

            database_manager.sync_authors(cur, pub)

            result = database_manager.get_publication_authors(
                cur,
                pub["handle"]
            )

            assert result == {"ZZZ_TEST_AUTHOR_SYNC_0001"}

        con.rollback()


# =====================================================
# RIMOZIONE AUTORE
# Verifica che sync_authors rimuova il collegamento
# con un autore non più presente nella pubblicazione.
# =====================================================
def test_sync_authors_remove():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            author = {
                "id": "ZZZ_TEST_AUTHOR_REMOVE_0001",
                "name": "ZZZ_Nome_Autore_Remove_0001",
                "surname": "ZZZ_Cognome_Autore_Remove_0001"
            }

            database_manager.insert_author(cur, author)

            database_manager.link_author_publication(
                cur,
                pub["handle"],
                author["id"]
            )

            pub["authors"] = []

            database_manager.sync_authors(cur, pub)

            result = database_manager.get_publication_authors(
                cur,
                pub["handle"]
            )

            assert result == set()

        con.rollback()


# =====================================================
# RECUPERO KEYWORD PUBBLICAZIONE
# Verifica che get_publication_keywords restituisca
# correttamente gli id delle keyword collegate.
# =====================================================
def test_get_publication_keywords():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            keyword_id = database_manager.insert_keyword(
                cur,
                "ZZZ_KEYWORD_GET_0001"
            )

            database_manager.link_keyword_publication(
                cur,
                pub["handle"],
                keyword_id
            )

            result = database_manager.get_publication_keywords(
                cur,
                pub["handle"]
            )

            assert result == {keyword_id}

        con.rollback()


# =====================================================
# SINCRONIZZAZIONE KEYWORD
# Verifica che sync_keywords aggiunga una nuova keyword
# e crei il relativo collegamento con la pubblicazione.
# =====================================================
def test_sync_keywords():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            database_manager.insert_publication_table(cur, pub)

            pub["keywords"] = ["ZZZ_KEYWORD_SYNC_0001"]

            database_manager.sync_keywords(cur, pub)

            result = database_manager.get_publication_keywords(
                cur,
                pub["handle"]
            )

            keyword_id = database_manager.insert_keyword(
                cur,
                "ZZZ_KEYWORD_SYNC_0001"
            )

            assert result == {keyword_id}

        con.rollback()


# =====================================================
# AGGIORNAMENTO PUBBLICAZIONE
# Verifica che update_publication aggiorni i dati
# della pubblicazione e sincronizzi autori e keyword.
# =====================================================
def test_update_publication():

    pub = create_pub()

    with database_manager.get_connection() as con:
        with con.cursor() as cur:
            database_manager.insert_publication_table(cur, pub)

    pub["title"] = "ZZZ_Titolo_Aggiornato_0002"
    pub["authors"] = [
        {
            "id": "ZZZ_TEST_AUTHOR_UPDATE_0001",
            "name": "ZZZ_Nome_Autore_Update_0001",
            "surname": "ZZZ_Cognome_Autore_Update_0001"
        }
    ]
    pub["keywords"] = ["ZZZ_KEYWORD_UPDATE_0001"]
    pub["last_update"] = str(int(time.time() * 1000))

    database_manager.update_publication(pub)

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            result = database_manager.get_publication(
                cur,
                pub["handle"]
            )

            authors = database_manager.get_publication_authors(
                cur,
                pub["handle"]
            )

            keywords = database_manager.get_publication_keywords(
                cur,
                pub["handle"]
            )

            cur.execute(
                """
                SELECT id
                FROM keywords
                WHERE name = %s
                """,
                ("ZZZ_KEYWORD_UPDATE_0001",)
            )

            keyword_id = cur.fetchone()[0]

            assert result["title"] == "ZZZ_Titolo_Aggiornato_0002"
            assert authors == {"ZZZ_TEST_AUTHOR_UPDATE_0001"}
            assert keywords == {keyword_id}

            cur.execute(
                """
                DELETE FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

            cur.execute(
                """
                DELETE FROM authors
                WHERE id = %s
                """,
                ("ZZZ_TEST_AUTHOR_UPDATE_0001",)
            )

            cur.execute(
                """
                DELETE FROM keywords
                WHERE id = %s
                """,
                (keyword_id,)
            )

        con.commit()


# =====================================================
# NUOVA PUBBLICAZIONE
# Verifica che sync_database inserisca una pubblicazione
# non ancora presente nel database.
# =====================================================
def test_sync_database_new_publication():

    pub = create_pub()

    database_manager.sync_database(pub)

    with database_manager.get_connection() as con:
        with con.cursor() as cur:

            result = database_manager.get_publication(
                cur,
                pub["handle"]
            )

            assert result is not None
            assert result["handle"] == pub["handle"]
            assert result["title"] == pub["title"]

            cur.execute(
                """
                DELETE FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

        con.commit()