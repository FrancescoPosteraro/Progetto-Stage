from bs4 import BeautifulSoup   #Libreria per il parsing di HMTL, utilizzato per estrarre dati dalla pagina web
import requests, webbrowser, json, os, time
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


BASE_DIR = Path(__file__).resolve().parent

#Path del file publications.json (per il momento é solo il path nel mio pc)
JSON_PATH = BASE_DIR / "dati_occurance.json"

def scrape_single_publication(pub_url):
    """
    Scarica e fa il parsing di una singola pubblicazione.
    """
    response = requests.get(
        pub_url,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    return soup

def count_dati(data, pub):

    table = pub.find("table", class_="card-body table itemDisplayTable")
    metadata_rows = table.find_all("tr")

    metadati_pubblicazione = set()

    for tr in metadata_rows:

        label_td = tr.find("td", class_="metadataFieldLabel")

        if not label_td:
            continue

        key = label_td.get_text(strip=True)

        # aggiunge il metadato una sola volta nella pubblicazione
        metadati_pubblicazione.add(key)


    # ora aggiorno il conteggio globale
    for key in metadati_pubblicazione:

        trovato = False

        for elemento in data:

            if elemento["campo"] == key:
                elemento["count"] += 1
                trovato = True
                break

        if not trovato:
            data.append(
                {
                    "campo": key,
                    "count": 1
                }
            )

    return data



start = 0       #Variabile usata per indicare il punto di partenza nella pagina di ricerca su Iris Bosa
rpp = 50        #Variabile che indica il numero di pubblicazioni viste per pagine
count = 1       #Per il momento variabile usata per monitorare il progresso di creazione
data = []

    #Ciclo principale che si ferma solo quando saranno finite le pubblicazioni con i break
while True:

    tr = 2  #indice utilizzato per scorrere la table all'interno della pagina HTML

        # Costruzione URL di ricerca su IRIS BOA
    url = (
        "https://boa.unimib.it/simple-search?"
        "query=&"
        "filter_field=author&"
        "filter_type=authority&"
        "filter_value=rp02409&"
        "filter_value_display=MICUCCI%2c+DANIELA&"
        f"sort_by=dc.date.issued_dt&"
        f"order=desc&"
        f"rpp={rpp}&"
        f"etal=0&"
        f"start={start}"
    )

        #Richiesta HTTP della pagina
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

        #Parsing HTML della pagina
    soup = BeautifulSoup(response.text, "html.parser")

        #Ricerco la tabella contenente le pubblicazioni
    table = soup.find("table", class_="table table-striped table-hover")

        #Estraggo le righe della tabella, se non ce ne sono, per errore o per aver finito le pubblicazioni, links sarà vuota
    if table:
        links = table.find_all("tr")[1:]
    else:
        links = []

        # STOP condizione (pagina vuota)
    if not links:
        break
        

    pub_urls = []

        #for utilizzato per scorrere tutte le righe trovate nella pagina
    for link in links:
        #individue il tag <td> che contiene il link alla publicazione
            #la riga che contiene il link avrà sempre id = "t_*numero della riga*_1
        td = link.find("td", id="t_" + str(tr) + "_1")

            #Estrazione del link della pubblicazione dalla cella della tabella HTML:
            #-verifica che la cella (td) esista
            #-cerca al suo interno un tag <a> contenente un attributo href
            #-se presente, estrae il valore del link della pubblicazione
        if td:
            a_tag = td.find("a", href=True)
            if a_tag:
                href = a_tag["href"]

                pub_url = (
                    "https://boa.unimib.it"
                    + href
                    + "?mode=full"
                )

                pub_urls.append(pub_url)

        tr += 1     #aumento count per passare alla riga successiva

        # -------------------------------
        # MULTITHREADING
        # -------------------------------

    with ThreadPoolExecutor(max_workers=10) as executor:

            #executor.map mantiene l'ordine degli URL originali
        soups = executor.map(scrape_single_publication, pub_urls)


            #aggiornamento JSON fatto dal thread principale
        for soup in soups:

            data = count_dati(data,soup)

            print(count)
            count += 1    

        #ultima pagina (meno di 25 risultati)
    if len(links) < rpp:
        break

    start += rpp

data = sorted(data, key=lambda x: x["count"], reverse=True)

with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)