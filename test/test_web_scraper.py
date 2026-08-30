"""
========================================================
Nome File: test_web_scraper.py
AUTORE: Test User

DESCRIZIONE:
Test automatici con pytest per verificare le funzioni
del modulo web_scraper.

I test utilizzano monkeypatch per simulare le dipendenze
esterne, come le richieste HTTP e il database, evitando
chiamate reali durante i test.

========================================================
"""

from web_scraper.web_scraper import extract_author_details
from web_scraper.web_scraper import extract_handle
from web_scraper.web_scraper import extract_authors
from web_scraper.web_scraper import upsert_publication
from web_scraper.web_scraper import sync_pubblication

import web_scraper.web_scraper as web_scraper

from bs4 import BeautifulSoup
import json


# =====================================================
# ESTRAZIONE HANDLE
# Verifica l'estrazione corretta dell'handle dalla pagina.
# =====================================================
def test_extract_handle():
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", class_="accordion-body")

    result = extract_handle(div)

    assert result == "745321"


# =====================================================
# HANDLE ASSENTE
# Verifica che venga restituito None quando manca l'handle.
# =====================================================
def test_extract_handle_bad_input():
    html = """
    <div class="accordion-body">
        Nessun handle presente
    </div>
    """

    div = BeautifulSoup(html, "html.parser").find("div")

    assert extract_handle(div) is None


# =====================================================
# ESTRAZIONE DATI AUTORE
# Verifica l'estrazione corretta di nome e cognome.
# =====================================================
def test_extract_author_details(monkeypatch):

    class FakeResponse:
        status_code = 200
        text = """
        <html>
            <body>
                <p id="displayValue">FERRARI, ELENA</p>
            </body>
        </html>
        """

    def fake_get(url):
        return FakeResponse()

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    result = extract_author_details(
        "https://example.org/cris/rp/rp54321"
    )

    assert result == {
        "name": "Elena",
        "surname": "Ferrari"
    }


# =====================================================
# ERRORE HTTP AUTORE
# Verifica che venga restituito None in caso di errore HTTP.
# =====================================================
def test_extract_author_details_http_error(monkeypatch):

    class FakeResponse:
        status_code = 404
        text = ""

    def fake_get(url):
        return FakeResponse()

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    result = extract_author_details(
        "https://example.org/cris/rp/rp54321"
    )

    assert result is None


# =====================================================
# NOME AUTORE ASSENTE
# Verifica che venga restituito None quando manca il nome.
# =====================================================
def test_extract_author_details_without_name_tag(monkeypatch):

    class FakeResponse:
        status_code = 200
        text = """
        <html>
            <body>
                <p>Nessun nome presente</p>
            </body>
        </html>
        """

    def fake_get(url):
        return FakeResponse()

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    result = extract_author_details(
        "https://example.org/cris/rp/rp54321"
    )

    assert result is None


# =====================================================
# AUTORE SENZA VIRGOLA
# Verifica la gestione di un nome senza separatore.
# =====================================================
def test_extract_author_details_without_comma(monkeypatch):

    class FakeResponse:
        status_code = 200
        text = """
        <html>
            <body>
                <p id="displayValue">COLOMBO</p>
            </body>
        </html>
        """

    def fake_get(url):
        return FakeResponse()

    monkeypatch.setattr(web_scraper.requests, "get", fake_get)

    result = extract_author_details(
        "https://example.org/cris/rp/rp54321"
    )

    assert result == {
        "name": None,
        "surname": "Colombo"
    }


# =====================================================
# ESTRAZIONE AUTORI
# Verifica l'estrazione di più autori.
# =====================================================
def test_extract_authors(monkeypatch):
    html = """
    <a class="authority author" href="/cris/rp/rp54321">Ferrari, E</a>
    <a class="authority author" href="/cris/rp/rp67890">Colombo, P</a>
    """

    authors_links = BeautifulSoup(html, "html.parser").find_all(
        "a", class_="authority author"
    )

    def fake_extract_author_details(url):
        if url.endswith("rp54321"):
            return {
                "name": "Elena",
                "surname": "Ferrari"
            }

        if url.endswith("rp67890"):
            return {
                "name": "Paolo",
                "surname": "Colombo"
            }

    monkeypatch.setattr(
        web_scraper,
        "extract_author_details",
        fake_extract_author_details
    )

    result = extract_authors(authors_links)

    assert result == [
        {
            "id": "rp54321",
            "name": "Elena",
            "surname": "Ferrari"
        },
        {
            "id": "rp67890",
            "name": "Paolo",
            "surname": "Colombo"
        }
    ]


# =====================================================
# AUTORE SENZA HREF
# Verifica che gli autori senza link vengano ignorati.
# =====================================================
def test_extract_authors_without_href(monkeypatch):
    html = """
    <a class="authority author" href="/cris/rp/rp54321">Ferrari, Elena</a>
    <a class="authority author">Colombo, Paolo</a>
    """

    authors_links = BeautifulSoup(html, "html.parser").find_all(
        "a", class_="authority author"
    )

    def fake_extract_author_details(url):
        return {
            "name": "Elena",
            "surname": "Ferrari"
        }

    monkeypatch.setattr(
        web_scraper,
        "extract_author_details",
        fake_extract_author_details
    )

    result = extract_authors(authors_links)

    assert result == [
        {
            "id": "rp54321",
            "name": "Elena",
            "surname": "Ferrari"
        }
    ]


# =====================================================
# INSERIMENTO PUBBLICAZIONE
# Verifica l'inserimento di una nuova pubblicazione.
# =====================================================
def test_upsert_publication_new(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>

    <table class="card-body table itemDisplayTable">
        <tr>
            <td class="metadataFieldLabel">dc.type</td>
            <td class="metadataFieldValue">Articolo su rivista</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.authority.ancejournal</td>
            <td class="metadataFieldValue">International Journal of Digital Systems</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.title</td>
            <td class="metadataFieldValue">Analisi dei sistemi distribuiti</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.identifier.doi</td>
            <td class="metadataFieldValue">10.0000/example-article</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.date.issued</td>
            <td class="metadataFieldValue">2025</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.identifier.uri</td>
            <td class="metadataFieldValue">https://example.org/publication</td>
        </tr>
    </table>

    <a class="authority author" href="/cris/rp/rp24680">Ferrari, Elena</a>
    """

    soup = BeautifulSoup(html, "html.parser")

    def fake_extract_authors(authors_links):
        return [
            {
                "id": "rp24680",
                "name": "Elena",
                "surname": "Ferrari"
            }
        ]

    monkeypatch.setattr(
        web_scraper,
        "extract_authors",
        fake_extract_authors
    )

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    data = []

    result = upsert_publication(data, soup)

    assert len(result) == 1
    assert result[0]["handle"] == "745321"
    assert result[0]["title"] == "Analisi dei sistemi distribuiti"
    assert result[0]["doi"] == "10.0000/example-article"
    assert result[0]["year"] == "2025"
    assert result[0]["type"] == "Articolo su rivista"
    assert result[0]["venue"] == "International Journal of Digital Systems"
    assert result[0]["authors"] == [
        {
            "id": "rp24680",
            "name": "Elena",
            "surname": "Ferrari"
        }
    ]


# =====================================================
# PUBBLICAZIONE NON AGGIORNATA
# Verifica che una pubblicazione non venga modificata
# quando il last_update non è cambiato.
# =====================================================
def test_upsert_publication_not_updated(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>

    <table class="card-body table itemDisplayTable">
        <tr>
            <td class="metadataFieldLabel">dc.type</td>
            <td class="metadataFieldValue">Articolo su rivista</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.authority.ancejournal</td>
            <td class="metadataFieldValue">International Journal of Digital Systems</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.title</td>
            <td class="metadataFieldValue">Titolo nuovo</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">iris.orcid.lastModifiedMillisecond</td>
            <td class="metadataFieldValue">1000</td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    monkeypatch.setattr(
        web_scraper,
        "extract_authors",
        lambda links: []
    )

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    data = [{
        "handle": "745321",
        "title": "Titolo precedente",
        "doi": None,
        "year": None,
        "authors": [],
        "type": "Articolo su rivista",
        "type_driver": None,
        "venue": "International Journal of Digital Systems",
        "url": None,
        "keywords": [],
        "last_update": "1000"
    }]

    result = upsert_publication(data, soup)

    assert result[0]["title"] == "Titolo precedente"


# =====================================================
# TABELLA ASSENTE
# Verifica che la pubblicazione venga ignorata senza tabella.
# =====================================================
def test_upsert_publication_without_table(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    data = []

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    result = upsert_publication(data, soup)

    assert result == []


# =====================================================
# TIPO NON SUPPORTATO
# Verifica che i tipi di pubblicazione non supportati vengano ignorati.
# =====================================================
def test_upsert_publication_unsupported_type(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>

    <table class="card-body table itemDisplayTable">
        <tr>
            <td class="metadataFieldLabel">dc.type</td>
            <td class="metadataFieldValue">Contributo in Libro</td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    data = []

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    result = upsert_publication(data, soup)

    assert result == []


# =====================================================
# PUBBLICAZIONE A CONVEGNO
# Verifica l'estrazione dei dati di un intervento a convegno.
# =====================================================
def test_upsert_publication_conference(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>

    <table class="card-body table itemDisplayTable">
        <tr>
            <td class="metadataFieldLabel">dc.type</td>
            <td class="metadataFieldValue">Intervento a convegno</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.relation.conferencename</td>
            <td class="metadataFieldValue">International Conference on Digital Technologies</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.title</td>
            <td class="metadataFieldValue">Tecnologie digitali emergenti</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.date.issued</td>
            <td class="metadataFieldValue">2025</td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    monkeypatch.setattr(
        web_scraper,
        "extract_authors",
        lambda links: [
            {
                "id": "rp13579",
                "name": "Paolo",
                "surname": "Colombo"
            }
        ]
    )

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    data = []

    result = upsert_publication(data, soup)

    assert len(result) == 1
    assert result[0]["type"] == "Intervento a convegno"
    assert result[0]["venue"] == "International Conference on Digital Technologies"
    assert result[0]["title"] == "Tecnologie digitali emergenti"
    assert result[0]["authors"] == [
        {
            "id": "rp13579",
            "name": "Paolo",
            "surname": "Colombo"
        }
    ]


# =====================================================
# AGGIORNAMENTO PUBBLICAZIONE
# Verifica l'aggiornamento di una pubblicazione modificata.
# =====================================================
def test_upsert_publication_update(monkeypatch):
    html = """
    <div class="accordion-body">
        <code>https://hdl.handle.net/99999/745321</code>
    </div>

    <table class="card-body table itemDisplayTable">
        <tr>
            <td class="metadataFieldLabel">dc.type</td>
            <td class="metadataFieldValue">Articolo su rivista</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.authority.ancejournal</td>
            <td class="metadataFieldValue">International Journal of Digital Systems</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">dc.title</td>
            <td class="metadataFieldValue">Titolo aggiornato</td>
        </tr>
        <tr>
            <td class="metadataFieldLabel">iris.orcid.lastModifiedMillisecond</td>
            <td class="metadataFieldValue">2000</td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    monkeypatch.setattr(
        web_scraper,
        "extract_authors",
        lambda links: []
    )

    monkeypatch.setattr(
        web_scraper.database_manager,
        "sync_database",
        lambda publication: None
    )

    data = [{
        "handle": "745321",
        "title": "Titolo precedente",
        "doi": None,
        "year": None,
        "authors": [],
        "type": "Articolo su rivista",
        "type_driver": None,
        "venue": "International Journal of Digital Systems",
        "url": None,
        "keywords": [],
        "last_update": "1000"
    }]

    result = upsert_publication(data, soup)

    assert len(result) == 1
    assert result[0]["handle"] == "745321"
    assert result[0]["title"] == "Titolo aggiornato"
    assert result[0]["last_update"] == "2000"


# =====================================================
# JSON ASSENTE
# Verifica la creazione del JSON quando il file non esiste.
# =====================================================
def test_sync_publication_without_json(monkeypatch, tmp_path):
    json_path = tmp_path / "publications.json"

    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    class FakeResponse:
        status_code = 200
        text = "<html></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        web_scraper.requests,
        "get",
        lambda *args, **kwargs: FakeResponse()
    )

    sync_pubblication()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data == []


# =====================================================
# JSON ESISTENTE
# Verifica il caricamento dei dati già presenti nel JSON.
# =====================================================
def test_sync_publication_with_existing_json(monkeypatch, tmp_path):
    json_path = tmp_path / "publications.json"

    existing_data = [{
        "handle": "745321",
        "title": "Titolo esistente",
        "doi": None,
        "year": None,
        "authors": [],
        "type": "Articolo su rivista",
        "type_driver": None,
        "venue": "International Journal of Digital Systems",
        "url": None,
        "keywords": [],
        "last_update": "1000"
    }]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f)

    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    class FakeResponse:
        status_code = 200
        text = "<html></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        web_scraper.requests,
        "get",
        lambda *args, **kwargs: FakeResponse()
    )

    sync_pubblication()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data == existing_data


# =====================================================
# ERRORE HTTP
# Verifica il comportamento quando la richiesta HTTP fallisce.
# =====================================================
def test_sync_publication_http_error(monkeypatch, tmp_path):
    json_path = tmp_path / "publications.json"

    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    class FakeResponse:
        status_code = 500
        text = ""

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        web_scraper.requests,
        "get",
        lambda *args, **kwargs: FakeResponse()
    )

    result = sync_pubblication()

    assert result is None


# =====================================================
# ESTRAZIONE LINK PUBBLICAZIONI
# Verifica l'elaborazione dei link presenti nella tabella.
# =====================================================
def test_sync_publication_table_with_links(monkeypatch, tmp_path):
    json_path = tmp_path / "publications.json"

    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    html = """
    <html>
        <table class="table table-striped table-hover">
            <tr>
                <th>Intestazione</th>
            </tr>

            <tr>
                <td id="t_2_1">
                    <a href="/handle/99999/111111">Pubblicazione 1</a>
                </td>
            </tr>

            <tr>
                <td id="t_3_1">
                    <a href="/handle/99999/222222">Pubblicazione 2</a>
                </td>
            </tr>
        </table>
    </html>
    """

    class FakeResponse:
        status_code = 200
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        web_scraper.requests,
        "get",
        lambda *args, **kwargs: FakeResponse()
    )

    calls = []

    def fake_upsert(data, pub):
        calls.append(pub)
        return data

    monkeypatch.setattr(
        web_scraper,
        "upsert_publication",
        fake_upsert
    )

    sync_pubblication()

    assert len(calls) == 2


# =====================================================
# COSTRUZIONE URL PUBBLICAZIONE
# Verifica la costruzione dell'URL della pagina della pubblicazione.
# =====================================================
def test_sync_publication_builds_publication_url(monkeypatch, tmp_path):
    json_path = tmp_path / "publications.json"

    monkeypatch.setattr(web_scraper, "JSON_PATH", json_path)

    search_html = """
    <table class="table table-striped table-hover">
        <tr>
            <th>Intestazione</th>
        </tr>
        <tr>
            <td id="t_2_1">
                <a href="/handle/99999/111111">Pubblicazione 1</a>
            </td>
        </tr>
    </table>
    """

    publication_html = """
    <html>
        <div class="accordion-body">
            <code>https://hdl.handle.net/99999/111111</code>
        </div>
    </html>
    """

    class FakeResponse:
        def __init__(self, text):
            self.status_code = 200
            self.text = text

        def raise_for_status(self):
            pass

    requested_urls = []

    def fake_get(url, *args, **kwargs):
        requested_urls.append(url)

        if "simple-search" in url:
            return FakeResponse(search_html)

        return FakeResponse(publication_html)

    monkeypatch.setattr(
        web_scraper.requests,
        "get",
        fake_get
    )

    def fake_upsert(data, pub):
        return data

    monkeypatch.setattr(
        web_scraper,
        "upsert_publication",
        fake_upsert
    )

    sync_pubblication()

    assert requested_urls[1] == (
    "https://boa.unimib.it/handle/99999/111111?mode=full"
    )