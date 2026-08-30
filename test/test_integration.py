"""
========================================================
Nome File: test_integration.py
AUTORE: Francesco Posteraro

DESCRIZIONE:
Test di integrazione tra Web Scraper, Database e API.

Il test avvia il Web Scraper utilizzando pagine HTML
simulate.

Il Web Scraper:
- recupera i dati simulati
- aggiorna il JSON
- chiama internamente il database

Successivamente il test verifica tramite API che la
pubblicazione sia stata correttamente salvata.

Al termine vengono rimossi tutti i dati creati dal test.
========================================================
"""

import json

from fastapi.testclient import TestClient

from api.main import app
import web_scraper.web_scraper as web_scraper
from database.database_manager import get_connection


client = TestClient(app)


def test_web_scraper_database_api_integration(
    monkeypatch,
    tmp_path
):

    json_path = tmp_path / "publications.json"

    monkeypatch.setattr(
        web_scraper,
        "JSON_PATH",
        json_path
    )

    # ======================================================
    # DATI DI TEST
    # ======================================================

    test_handle = "999999999"

    test_author_id = "AUTHOR_IMPOSSIBLE_847261"

    test_keyword_1 = "KEYWORD_IMPOSSIBILE_847261"
    test_keyword_2 = "KEYWORD_INTEGRAZIONE_IMPOSSIBILE_592731"

    # ======================================================
    # PAGINA DI RICERCA SIMULATA
    # ======================================================

    search_html = """
    <html>
        <table class="table table-striped table-hover">

            <tr>
                <th>Intestazione</th>
            </tr>

            <tr>
                <td id="t_2_1">
                    <a href="/cris/item/999999999">
                        PUBBLICAZIONE_INTEGRAZIONE_IMPOSSIBILE_847261
                    </a>
                </td>
            </tr>

        </table>
    </html>
    """

    # ======================================================
    # PAGINA DELLA PUBBLICAZIONE SIMULATA
    #
    # IMPORTANTE:
    # Le etichette dei metadata sono mantenute sulla stessa
    # riga del td perché il Web Scraper utilizza:
    #
    # table.find("td", string="...")
    #
    # ======================================================

    publication_html = """
    <html>

        <div class="accordion-body">
            <code>https://hdl.handle.net/99999/999999999</code>
        </div>

        <a
            class="authority author"
            href="/cris/rp/AUTHOR_IMPOSSIBLE_847261"
        >
            COGNOME_IMPOSSIBILE_847261, NOME_IMPOSSIBILE_847261
        </a>

        <table class="card-body table itemDisplayTable">

            <tr>
                <td class="metadataFieldLabel">dc.type</td>
                <td class="metadataFieldValue">Articolo su rivista</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.authority.ancejournal</td>
                <td class="metadataFieldValue">RIVISTA_IMPOSSIBILE_847261</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.title</td>
                <td class="metadataFieldValue">TITOLO_INTEGRAZIONE_IMPOSSIBILE_847261</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.doi</td>
                <td class="metadataFieldValue">10.99999/DOI-IMPOSSIBILE-847261</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.date.issued</td>
                <td class="metadataFieldValue">2026</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.uri</td>
                <td class="metadataFieldValue">https://url-impossibile-847261.example</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.type.driver</td>
                <td class="metadataFieldValue">article</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">iris.orcid.lastModifiedMillisecond</td>
                <td class="metadataFieldValue">9999999999999</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">KEYWORD_IMPOSSIBILE_847261</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">KEYWORD_INTEGRAZIONE_IMPOSSIBILE_592731</td>
            </tr>

        </table>

    </html>
    """

    # ======================================================
    # PAGINA AUTORE SIMULATA
    # ======================================================

    author_html = """
    <html>
        <p id="displayValue">COGNOME_IMPOSSIBILE_847261, NOME_IMPOSSIBILE_847261</p>
    </html>
    """

    # ======================================================
    # RISPOSTA HTTP SIMULATA
    # ======================================================

    class FakeResponse:

        def __init__(self, text):
            self.status_code = 200
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, *args, **kwargs):

        if "simple-search" in url:
            return FakeResponse(search_html)

        if test_author_id in url:
            return FakeResponse(author_html)

        return FakeResponse(publication_html)

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)
    try:

        # ==================================================
        # AVVIO WEB SCRAPER
        #
        # Il database viene chiamato internamente dal
        # Web Scraper.
        # ==================================================

        web_scraper.sync_pubblication()

        # ==================================================
        # VERIFICA JSON
        # ==================================================

        with open(json_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        assert len(json_data) == 1

        publication = json_data[0]

        assert publication["handle"] == test_handle

        assert publication["title"] == ("TITOLO_INTEGRAZIONE_IMPOSSIBILE_847261")

        assert publication["doi"] == ("10.99999/DOI-IMPOSSIBILE-847261")

        assert publication["year"] == "2026"

        assert publication["type"] == "Articolo su rivista"

        assert publication["venue"] == ("RIVISTA_IMPOSSIBILE_847261")

        assert publication["type_driver"] == "article"

        assert publication["url"] == ("https://url-impossibile-847261.example")

        assert publication["last_update"] == "9999999999999"

        assert publication["authors"] == [
            {
                "id": test_author_id,
                "name": "Nome_Impossibile_847261",
                "surname": "Cognome_Impossibile_847261"
            }
        ]

        assert set(publication["keywords"]) == {test_keyword_1.lower(), test_keyword_2.lower()}

        # ==================================================
        # VERIFICA API
        # ==================================================

        response = client.get(
            "/publications/latest",
            params={
                "page": 1,
                "per_page": 100
            }
        )

        assert response.status_code == 200

        api_data = response.json()

        result = next(
            (
                pub
                for pub in api_data["data"]
                if pub["handle"] == test_handle
            ),
            None
        )

        assert result is not None

        assert result["handle"] == test_handle

        assert result["title"] == (
            "TITOLO_INTEGRAZIONE_IMPOSSIBILE_847261"
        )

        assert result["doi"] == (
            "10.99999/DOI-IMPOSSIBILE-847261"
        )

        assert str(result["year"]) == "2026"

        assert result["type"] == "Articolo su rivista"

        assert result["type_driver"] == "article"

        assert result["venue"] == (
            "RIVISTA_IMPOSSIBILE_847261"
        )

        assert result["url"] == (
            "https://url-impossibile-847261.example"
        )

        assert str(result["last_update"]) == (
            "9999999999999"
        )

        assert result["authors"] == [
            {
                "id": test_author_id,
                "name": "Nome_Impossibile_847261",
                "surname": "Cognome_Impossibile_847261"
            }
        ]

        assert set(result["keywords"]) == {
            test_keyword_1.lower(),
            test_keyword_2.lower()
        }

    finally:

        # ==================================================
        # PULIZIA DATABASE
        #
        # Eliminiamo esclusivamente i dati creati da questo
        # test.
        # ==================================================

        with get_connection() as con:

            with con.cursor() as cur:

                cur.execute(
                    """
                    DELETE FROM publications_authors
                    WHERE publication_handle = %s
                    """,
                    (test_handle,)
                )

                cur.execute(
                    """
                    DELETE FROM publications_keywords
                    WHERE publication_handle = %s
                    """,
                    (test_handle,)
                )

                cur.execute(
                    """
                    DELETE FROM publications
                    WHERE handle = %s
                    """,
                    (test_handle,)
                )

                cur.execute(
                    """
                    DELETE FROM authors
                    WHERE id = %s
                    """,
                    (test_author_id,)
                )

                cur.execute(
                    """
                    DELETE FROM keywords
                    WHERE name IN (%s, %s)
                    """,
                    (
                        test_keyword_1.lower(),
                        test_keyword_2.lower()
                    )
                )

            con.commit()