"""
========================================================
Nome File: test_api_integration.py

DESCRIZIONE:
Test di integrazione per verificare il corretto
funzionamento dell'endpoint delle ultime pubblicazioni.

Il test utilizza l'API reale e verifica la paginazione,
il numero di pubblicazioni per pagina e la presenza
di pubblicazioni differenti tra pagine consecutive.

========================================================
"""


from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)

# =====================================================
# TEST DELLA PAGINAZIONE
# Verifica il corretto funzionamento della paginazione
# delle pubblicazioni.
# =====================================================
def test_get_latest_publications_pagination():

    response_page_1 = client.get(
        "/publications/latest",
        params={
            "page": 1,
            "per_page": 5
        }
    )

    assert response_page_1.status_code == 200

    data_page_1 = response_page_1.json()

    assert "data" in data_page_1
    assert "meta" in data_page_1

    assert data_page_1["meta"]["page"] == 1
    assert data_page_1["meta"]["per_page"] == 5
    assert data_page_1["meta"]["count"] <= 5

    response_page_2 = client.get(
        "/publications/latest",
        params={
            "page": 2,
            "per_page": 5
        }
    )

    assert response_page_2.status_code == 200

    data_page_2 = response_page_2.json()

    assert "data" in data_page_2
    assert "meta" in data_page_2

    assert data_page_2["meta"]["page"] == 2
    assert data_page_2["meta"]["per_page"] == 5
    assert data_page_2["meta"]["count"] <= 5

    handles_page_1 = {
        publication["handle"]
        for publication in data_page_1["data"]
    }

    handles_page_2 = {
        publication["handle"]
        for publication in data_page_2["data"]
    }

    assert handles_page_1.isdisjoint(handles_page_2)


# =====================================================
# VALIDAZIONE NUMERO PAGINA
# Verifica che una pagina con valore non valido
# restituisca un errore.
# =====================================================
def test_get_latest_publications_invalid_page():

    response = client.get(
        "/publications/latest",
        params={
            "page": 0,
            "per_page": 5
        }
    )

    assert response.status_code == 400


# =====================================================
# VALIDAZIONE PUBBLICAZIONI PER PAGINA
# Verifica che un numero di pubblicazioni per pagina
# non valido restituisca un errore.
# =====================================================
def test_get_latest_publications_invalid_per_page():

    response = client.get(
        "/publications/latest",
        params={
            "page": 1,
            "per_page": 0
        }
    )

    assert response.status_code == 400


# =====================================================
# TEST RICERCA PUBBLICAZIONI PER AUTORE INESISTENTE
# Verifica che l'API restituisca errore quando l'autore
# richiesto non esiste.
# =====================================================
def test_get_publications_by_author_not_found():

    response = client.get(
        "/publications/authors",
        params={
            "name": "ZZZ_Nome_Fittizio_404",
            "surname": "ZZZ_Cognome_Fittizio_404"
        }
    )

    assert response.status_code == 404


# =====================================================
# TEST PARAMETRI AUTORE MANCANTI
# Verifica che l'API restituisca errore quando
# nome e cognome non vengono forniti.
# =====================================================
def test_get_publications_by_author_missing_parameters():

    response = client.get(
        "/publications/authors"
    )

    assert response.status_code == 400


# =====================================================
# TEST RICERCA PUBBLICAZIONI PER AUTORE
# Inserisce dati mock nel database, richiama realmente
# l'endpoint API e verifica che restituisca esattamente
# le pubblicazioni associate all'autore inserito.
# =====================================================
def test_get_publications_by_author_with_publications():

    from database.database_manager import get_connection

    author_id = "ZZZ_TEST_AUTHOR_API_001"
    publication_1 = "ZZZ_TEST_PUBLICATION_API_001"
    publication_2 = "ZZZ_TEST_PUBLICATION_API_002"

    with get_connection() as con:
        with con.cursor() as cur:

            try:

                cur.execute(
                    """
                    INSERT INTO authors (id, name, surname)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        author_id,
                        "ZZZ_Nome_Autore_Test",
                        "ZZZ_Cognome_Autore_Test"
                    )
                )

                cur.execute(
                    """
                    INSERT INTO publications
                    (
                        handle,
                        title,
                        doi,
                        year,
                        type,
                        type_driver,
                        venue,
                        url,
                        last_update
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        publication_1,
                        "ZZZ_Titolo_Pubblicazione_001",
                        "10.0000/zzz-test-api-001",
                        2091,
                        "ZZZ_Tipo_Pubblicazione_001",
                        "ZZZ_DRIVER_001",
                        "ZZZ_Venue_Test_001",
                        "https://invalid.test/zzz-publication-001",
                        900001
                    )
                )

                cur.execute(
                    """
                    INSERT INTO publications
                    (
                        handle,
                        title,
                        doi,
                        year,
                        type,
                        type_driver,
                        venue,
                        url,
                        last_update
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        publication_2,
                        "ZZZ_Titolo_Pubblicazione_002",
                        "10.0000/zzz-test-api-002",
                        2092,
                        "ZZZ_Tipo_Pubblicazione_002",
                        "ZZZ_DRIVER_002",
                        "ZZZ_Venue_Test_002",
                        "https://invalid.test/zzz-publication-002",
                        900002
                    )
                )

                cur.execute(
                    """
                    INSERT INTO publications_authors
                    (
                        publication_handle,
                        author_id
                    )
                    VALUES
                    (%s, %s),
                    (%s, %s)
                    """,
                    (
                        publication_1,
                        author_id,
                        publication_2,
                        author_id
                    )
                )

                con.commit()

                response = client.get(
                    "/publications/authors",
                    params={
                        "name": "ZZZ_Nome_Autore_Test",
                        "surname": "ZZZ_Cognome_Autore_Test"
                    }
                )

                assert response.status_code == 200

                data = response.json()

                returned_handles = {
                    publication["handle"]
                    for publication in data
                }

                expected_handles = {
                    publication_1,
                    publication_2
                }

                assert returned_handles == expected_handles

            finally:

                cur.execute(
                    """
                    DELETE FROM publications
                    WHERE handle IN (%s, %s)
                    """,
                    (
                        publication_1,
                        publication_2
                    )
                )

                cur.execute(
                    """
                    DELETE FROM authors
                    WHERE id = %s
                    """,
                    (author_id,)
                )

                con.commit()


# =====================================================
# TEST AUTORE SENZA PUBBLICAZIONI
# Verifica che un autore esistente ma senza pubblicazioni
# associate restituisca una lista vuota con stato 200.
# =====================================================
def test_get_author_without_publications():

    from database.database_manager import get_connection

    author_id = "ZZZ_TEST_AUTHOR_NO_PUBLICATIONS_001"

    with get_connection() as con:
        with con.cursor() as cur:

            try:

                cur.execute(
                    """
                    INSERT INTO authors (id, name, surname)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        author_id,
                        "ZZZ_Nome_Senza_Pubblicazioni",
                        "ZZZ_Cognome_Senza_Pubblicazioni"
                    )
                )

                con.commit()

                response = client.get(
                    "/publications/authors",
                    params={
                        "name": "ZZZ_Nome_Senza_Pubblicazioni",
                        "surname": "ZZZ_Cognome_Senza_Pubblicazioni"
                    }
                )

                assert response.status_code == 200

                data = response.json()

                assert data == []

            finally:

                cur.execute(
                    """
                    DELETE FROM authors
                    WHERE id = %s
                    """,
                    (author_id,)
                )

                con.commit()