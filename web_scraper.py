"""
========================================================
PROGETTO: Web Scraper
AUTORE: Francesco Posteraro
DESCRIZIONE:
Script per recupero dati dal sito Iris Boa, 
traduzione dei dati in file json 

========================================================
"""

from bs4 import BeautifulSoup   #Libreria per il parsing di HMTL, utilizzato per estrarre dati dalla pagina web
import requests, webbrowser, json, os, time
from urllib.parse import urlparse, parse_qs
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

#Path del file publications.json (per il momento é solo il path nel mio pc)
JSON_PATH = BASE_DIR / "publications.json"
#Path del file seconds che contiene tutti i tempi di esecuzione di tutte le esecuzioni
SECONDS_PATH = BASE_DIR / "EXTRA" / "seconds.txt"

LAST_UPDATE_PATH = BASE_DIR / "EXTRA" /"last_update.json"

#dizionario di conversione per tradurre i nome che arrivano dal sito i nomi piu' semplici da leggere
FIELD_MAPPING = {
    "dc.identifier.doi": "doi",
    "dc.title": "title",
    "dc.date.issued": "year",
    "dc.identifier.uri": "url",
    "dc.type.driver": "type_driver",
    "iris.orcid.lastModifiedMillisecond": "last_update"
}


#Funzione utilizzata per recuperare il nome e il cognome dalla pagina dell'autore
def extract_author_details(author_url):
    response = requests.get(author_url)     #Richiesta HTTP della pagina

    if response.status_code != 200:     #controllo che la richiesta sai andata a buon fine
        return None

    soup = BeautifulSoup(response.text, "html.parser")      #Parsing HTML della pagina

    name_tag = soup.find("p", id="displayValue")

    if not name_tag:
        return None

    full_name = name_tag.get_text(strip=True)       #recupero nome e cognome

    #Divido il nome completo usando la virgola come separatore.
    #Il parametro 1 indica di effettuare al massimo una divisione,
    #quindi otteniamo sempre al massimo due parti: cognome e nome.
    parts = full_name.split(",", 1)


    #Se la divisione ha prodotto due elementi, significa che il formato è:
    #"COGNOME, NOME"
    if len(parts) == 2:
        #La prima parte contiene il cognome
        #strip() rimuove eventuali spazi vuoti
        #title() converte il testo in formato Nome Cognome (es. MALTAGLIATI -> Maltagliati)
        surname = parts[0].strip().title()

        #La seconda parte contiene il nome
        name = parts[1].strip().title()
    else:
        #Se non c'è la virgola, non è possibile separare nome e cognome.
        #Salvo comunque il valore completo come cognome
        #e imposto il nome a None.
        surname = full_name.title()
        name = None

    return {
        "name": name,
        "surname": surname
    }


#Questa funziona recupera id, nome e cognome degli autori e li restituisce
def extract_authors(authors_links):

    authors_list = []

    for author in authors_links:

        href = author.get("href")

        if not href:
            continue

        author_id = href.split("/")[-1]     #recupero l'id

        details = extract_author_details("https://boa.unimib.it" + href)        #chiamo una funzione per recuperare il nome ed il cognome

        authors_list.append({
            "id": author_id,
            "name": details["name"],
            "surname": details["surname"]
        })

    return authors_list

#Funzione utilizzata per l'estrazione dell'handle
def extract_handle(div):

    handle_link = div.find("code").get_text(strip=True) if div and div.find("code") else None
    handle= handle_link.split("/")[-1]

    return handle



################################################################
#           Funzione upsert_publication(data, pub)             #       
################################################################
#Questa funzione viene usata per inserire in data la singola pubblicazione, oppure aggiorna la pubblicazione 
#in base all'Handle e al metadato della pubblicazione "iris.orcid.lastModifiedMillisecond"
def upsert_publication(data, pub):

    #Dizionario che conterrà i dati della singola pubblicazione
    pub_dict = {
        "handle": None,
        "title": None,
        "doi": None,
        "year": None,
        "authors": [],
        "type": None,
        "type_driver": None,
        "venue": None,
        "url": None,
        "keywords": [],
        "last_update": None
    }


    #Ricerca del blocco HTML che contiene l'handle
    div = pub.find("div", class_="accordion-body")

    handle = extract_handle(div)

    #se non c'è handle, salta
    if not handle:
        return data
    
    #Inserisco l'handle nel dizionario
    pub_dict["handle"] = handle


    #Estraggo la tabella che contiene i metadati della pubblicazione
    table = pub.find("table", class_="card-body table itemDisplayTable")

    if not table:
        return data


    #Controllo che la pubblicazione sia di tipo 01 o 02
    field = table.find("td", string="dc.type")
    if field:
        value = field.find_next_sibling("td").get_text(strip=True)

        #salvo il tipo
        pub_dict["type"] = value

        #Se non é nessunaq delle due viene fatto il reutnr e non viene aggiunto niente,
        #se invece si tratta del tipo 1 o 2 viene aggiunto al dizionario, e viene anche aggiunto il neue
        #in base al tipo di pubblicazione, diverso per i due tipi
        if value == "Intervento su rivista":
            pub_dict["type"] = value

            field_vanue = table.find("td", string="dc.authority.ancejournal")
            pub_dict["venue"] = field_vanue.find_next_sibling("td").get_text(strip=True)
        elif value == "Intervento a convegno":
            pub_dict["type"] = value

            field_vanue = table.find("td", string="dc.relation.conferencename")
            pub_dict["venue"] = field_vanue.find_next_sibling("td").get_text(strip=True)
        
        else:
            print("skipping..", end=" ")
            return data

    else:
        print("skipping..", end=" ")
        return data

    #Gli autori vengono trattati in modo diverso, poichè non si trova nella table ma viene fatto uno scraping aggiuntivo
    author_links = pub.find_all("a", class_="authority author")
    pub_dict["authors"] = extract_authors(author_links)

    metadata_rows = table.find_all("tr")


    #Scorro tutti i metadati della tabella
    for tr in metadata_rows:

        label_td = tr.find("td", class_="metadataFieldLabel")
        value_td = tr.find("td", class_="metadataFieldValue")


        #se manca la label o il valore salto la riga
        if not label_td or not value_td:
            continue


        key = label_td.get_text(strip=True)
        value = value_td.get_text(strip=True)

        #Questa if particolare serve per il campo keyword per creare una lista di keyword ad ogni passaggio del for
        if key == "dc.subject.singlekeyword":
            pub_dict["keywords"].append(value)

        elif key in FIELD_MAPPING:
            #Se il metadato trovato nella pagina IRIS è presente nel mapping,
            #salvo il valore nel dizionario finale usando il nome della chiave
            pub_dict[FIELD_MAPPING[key]] = value



    #Estraggo l'ultimo aggiornamento della pubblicazione
    pub_last_update = int(pub_dict.get("last_update") or 0)



    #Controllo se la pubblicazione esiste già
    for i, p in enumerate(data):

        if p["handle"] == handle:

            old_last = int(p.get("last_update") or 0)


            #Se non è cambiata non faccio nulla
            if pub_last_update <= old_last:
                print("not updating..", end=" ")
                return data


            #Se è cambiata aggiorno
            print("updating..", end=" ")
            data[i] = pub_dict
            return data



    #Pubblicazione nuova
    print("adding..", end=" ")
    data.append(pub_dict)

    return data



################################################################
#               Funzione sync_pubblication()                   #
################################################################
#Funzione che ricerca la table nella pagina HTML e analizza riga per riga tutte le pubblicazioni
#Inserendole in data oppure no tramite la funzione upsert_publication(data, pub) e successivamente scrivendo tutto il data nel file json

def sync_pubblication():

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []       #lista che conterrà tutte le pubblicazioni con relativi dati
          
    start = 0       #Variabile usata per indicare il punto di partenza nella pagina di ricerca su Iris Bosa
    rpp = 25        #Variabile che indica il numero di pubblicazioni viste per pagine
    count = 1       #Per il momento variabile usata per monitorare il progresso di creazione

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
        if response.status_code != 200:     #controllo che la richiesta sai andata a buon fine
            return None
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

            #Costruzione URL della pagina dettaglio pubblicazione
            pub_url = "https://boa.unimib.it" + href + "?mode=full"


            #scarico pagina della singola pubblicazione
            response = requests.get(pub_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()

            #Parsing HTML della pubblicazione
            soup = BeautifulSoup(response.text, "html.parser")

            #Richiamo la funzione upsert_publication che inserirà nel json la pubblicazione, passando data e soup
            data = upsert_publication(data, soup)

            #Print usato per visualizzare la progressione della creazione
            print(count)

            count += 1
            tr += 1     #aumento count per passare alla riga successiva

        #ultima pagina (meno di 25 risultati)
        if len(links) < rpp:
            break

        start += rpp
        
    #scrivo sul file json tutte le pubblicazioni come ultima cosa
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)




# Avvio del programma:
# viene determinato se eseguire un aggiornamento oppure una creazione
# in base alla presenza del file "publications.json"
    #Prendo il tempo di partenza solo per calcolare il tempo di esecuzione del programma
start_time = time.time()

print("Avvio");
sync_pubblication()

last_update = int(time.time() * 1000)

LAST_UPDATE_PATH.write_text(
json.dumps({"last_update_ms": last_update}, indent=2),
    encoding="utf-8"
)

    #Questa parte é sempre legata al solo scopo di sapere i tempi di esecuzione
end_time = time.time()

tempo_esecuzione = end_time - start_time


with open(SECONDS_PATH, "a") as file:
    file.write(f"{tempo_esecuzione}\n")

print(f"Tempo di esecuzione: {tempo_esecuzione:.4f} secondi")