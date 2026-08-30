"""
========================================================
Nome File: test_web_scraper_integration.py
AUTORE: Francesco Posteraro

DESCRIZIONE:
Test di integrazione con pytest per verificare il
funzionamento completo del modulo web_scraper.

Il test simula le chiamate HTTP per riprodurre le pagine
di IRIS e verifica il corretto recupero e salvataggio
dei dati nel file JSON.

Il database viene temporaneamente escluso dal test
e verrà verificato separatamente.

========================================================
"""

import json
import web_scraper.web_scraper as web_scraper


def test_sync_publication_full_integration(monkeypatch, tmp_path):

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
                    <a href="/cris/item/TEST_ITEM_A1">Elemento di test</a>
                </td>
            </tr>
        </table>
    </html>
    """

    publication_html = """
    <html>
        <div class="accordion-body">
            <code>https://hdl.handle.net/10281/TEST_ITEM_A1</code>
        </div>

        <a class="authority author" href="/cris/rp/TEST_AUTHOR_A1">
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
                <td class="metadataFieldValue">Pubblicazione di test</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.doi</td>
                <td class="metadataFieldValue">10.0000/test.integration</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.date.issued</td>
                <td class="metadataFieldValue">2026</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.identifier.uri</td>
                <td class="metadataFieldValue">https://example.com/test-item</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.type.driver</td>
                <td class="metadataFieldValue">test-driver</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">
                    iris.orcid.lastModifiedMillisecond
                </td>
                <td class="metadataFieldValue">1000</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">keyword_alpha_test</td>
            </tr>

            <tr>
                <td class="metadataFieldLabel">dc.subject.singlekeyword</td>
                <td class="metadataFieldValue">keyword_beta_test</td>
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

        if "/cris/rp/TEST_AUTHOR_A1" in url:
            return FakeResponse(author_html)

        return FakeResponse(publication_html)

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    web_scraper.sync_pubblication()

    with open(json_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    assert len(result) == 1

    publication = result[0]

    assert publication["handle"] == "TEST_ITEM_A1"
    assert publication["title"] == "Pubblicazione di test"
    assert publication["doi"] == "10.0000/test.integration"
    assert publication["year"] == "2026"
    assert publication["type"] == "Articolo su rivista"
    assert publication["venue"] == "Test Journal"
    assert publication["type_driver"] == "test-driver"
    assert publication["last_update"] == "1000"

    assert publication["authors"] == [
        {
            "id": "TEST_AUTHOR_A1",
            "name": "Autore",
            "surname": "Test"
        }
    ]

    assert set(publication["keywords"]) == {
        "keyword_alpha_test",
        "keyword_beta_test"
    }