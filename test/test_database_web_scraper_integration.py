"""
========================================================
Nome File: test_database_web_scraper_integration.py
AUTORE: Francesco Posteraro

DESCRIZIONE:
Test di integrazione tra web_scraper e database_manager.

Il test esegue lo scraping simulato di una pubblicazione,
salva i dati nel file JSON e verifica che gli stessi dati
vengano sincronizzati correttamente nel database.

Al termine del test i dati inseriti nel database vengono
rimossi.
========================================================
"""

import json
import web_scraper.web_scraper as web_scraper
from database import database_manager


def test_web_scraper_database_integration(monkeypatch, tmp_path):

    json_path = tmp_path / "publications.json"
    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    search_html = """
    <html>
        <table class="table table-striped table-hover">
            <tr>
                <th>Intestazione</th>
            </tr>
            <tr>
                <td id="t_2_1">
                    <a href="/cris/item/TEST_ITEM_B7">Elemento di test</a>
                </td>
            </tr>
        </table>
    </html>
    """

    publication_html = """
    <html>
        <div class="accordion-body">
            <code>https://hdl.handle.net/10281/TEST_ITEM_B7</code>
        </div>

        <a class="authority author" href="/cris/rp/TEST_AUTHOR_B7">
            Test, Autore
        </a>

        <table class="card-body table itemDisplayTable">
            <tr>
                <td class="metadataFieldLabel">dc.type</td>
                <td class="metadataFieldValue">Articolo su rivista</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.authority.ancejournal</td>
                <td class="metadataFieldValue">Test Journal</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.title</td>
                <td class="metadataFieldValue">Pubblicazione di test database</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.doi</td>
                <td class="metadataFieldValue">10.0000/test.database</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.date.issued</td>
                <td class="metadataFieldValue">2026</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.uri</td>
                <td class="metadataFieldValue">https://example.com/test-database</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.type.driver</td>
                <td class="metadataFieldValue">test-driver</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">
                    iris.orcid.lastModifiedMillisecond
                </td>
                <td class="metadataFieldValue">2000</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">keyword_gamma_test</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">keyword_delta_test</td>
            </tr>
        </table>
    </html>
    """

    author_html = """
    <html>
        <p id="displayValue">TEST, AUTORE</p>
    </html>
    """

    class FakeResponse:

        def __init__(self, text):
            self.status_code = 200
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, *args, **kwargs):

        if "simple-search" in url:
            return FakeResponse(search_html)

        if "/cris/rp/TEST_AUTHOR_B7" in url:
            return FakeResponse(author_html)

        return FakeResponse(publication_html)

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    web_scraper.sync_pubblication()

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    assert len(json_data) == 1

    json_publication = json_data[0]

    try:
        with database_manager.get_connection() as con:
            with con.cursor() as cur:

                db_publication = database_manager.get_publication(
                    cur,
                    json_publication["handle"]
                )

                db_author_ids = database_manager.get_publication_authors(
                    cur,
                    json_publication["handle"]
                )

                db_keyword_ids = database_manager.get_publication_keywords(
                    cur,
                    json_publication["handle"]
                )

                cur.execute(
                    """
                    SELECT id, name, surname
                    FROM authors
                    WHERE id = ANY(%s)
                    """,
                    (list(db_author_ids),)
                )

                db_authors_rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT id, name
                    FROM keywords
                    WHERE id = ANY(%s)
                    """,
                    (list(db_keyword_ids),)
                )

                db_keywords_rows = cur.fetchall()

                db_authors = [
                    {
                        "id": str(row[0]),
                        "name": row[1],
                        "surname": row[2]
                    }
                    for row in db_authors_rows
                ]

                db_keywords = [
                    row[1]
                    for row in db_keywords_rows
                ]

                db_reconstructed = {
                    "handle": db_publication["handle"],
                    "title": db_publication["title"],
                    "doi": db_publication["doi"],
                    "year": str(db_publication["year"]),
                    "type": db_publication["type"],
                    "type_driver": db_publication["type_driver"],
                    "venue": db_publication["venue"],
                    "url": db_publication["url"],
                    "last_update": str(db_publication["last_update"]),
                    "authors": db_authors,
                    "keywords": db_keywords
                }

                def normalize(value):

                    if isinstance(value, dict):
                        return {
                            key: normalize(val)
                            for key, val in value.items()
                        }

                    if isinstance(value, list):
                        normalized = [normalize(item) for item in value]

                        if all(isinstance(item, dict) for item in normalized):
                            return sorted(
                                normalized,
                                key=lambda item: str(item)
                            )

                        return sorted(normalized, key=str)

                    if isinstance(value, str):
                        return value.strip().lower()

                    return value

                assert normalize(json_publication) == normalize(
                    db_reconstructed
                )

    finally:

        with database_manager.get_connection() as con:
            with con.cursor() as cur:

                cur.execute(
                    """
                    DELETE FROM publications_keywords
                    WHERE publication_handle = %s
                    """,
                    (json_publication["handle"],)
                )

                cur.execute(
                    """
                    DELETE FROM publications_authors
                    WHERE publication_handle = %s
                    """,
                    (json_publication["handle"],)
                )

                cur.execute(
                    """
                    DELETE FROM publications
                    WHERE handle = %s
                    """,
                    (json_publication["handle"],)
                )

                cur.execute(
                    """
                    DELETE FROM keywords
                    WHERE LOWER(name) IN (%s, %s)
                    """,
                    ("keyword_gamma_test", "keyword_delta_test")
                )

                cur.execute(
                    """
                    DELETE FROM authors
                    WHERE id = %s
                    """,
                    ("TEST_AUTHOR_B7",)
                )

            con.commit()