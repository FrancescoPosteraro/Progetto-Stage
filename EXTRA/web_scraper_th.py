"""
========================================================
PROGETTO: Web Scraper
AUTORE: Francesco Posteraro
DESCRIZIONE:
Script per recupero dati dal sito Iris Boa, 
traduzione dei dati in file json 

========================================================
"""
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup   #Libreria per il parsing di HMTL, utilizzato per estrarre dati dalla pagina web
import requests, webbrowser, json, os, time
from urllib.parse import urlparse, parse_qs
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

#Path del file publications.json
JSON_PATH = r"C:\Users\franc\Desktop\Progetto-Stage\publications.json"

#Path del file seconds che contiene tutti i tempi di esecuzione di tutte le esecuzioni
SECONDS_PATH = BASE_DIR / "seconds.txt"

LAST_UPDATE_PATH = BASE_DIR / "last_update.json"

#Set creato per distiguere i metadati delle pubblicazioni con ripetizioni
multi_fields = {
    "dc.authority.people",
    "dc.authority.academicField2024",
    "dc.contributor.area",
    "dc.subject.singlekeyword",
    "isi.category",
    "isi.contributor.affiliation",
    "isi.contributor.country", 
    "isi.contributor.name",
    "isi.contributor.researcherId",
    "isi.contributor.subaffiliation",
    "isi.contributor.surname",
    "scopus.contributor.affiliation",
    "scopus.contributor.afid",
    "scopus.contributor.auid",
    "scopus.contributor.country",
    "scopus.contributor.dptid",
    "scopus.contributor.name",
    "scopus.contributor.subaffiliation",
    "scopus.contributor.surname",
    "scopus.differences",  
}


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

    
    # Dizionario che conterrà i dati della singola pubblicazione
    pub_dict = {}

    #Ricerca del blocco HTML che il linki handle
    div = pub.find("div", class_="accordion-body")

    handle = extract_handle(div)

    
    # se non c'è handle, salta
    if not handle:
        return data
    
    #Inserisco l'handle nel dizionario
    pub_dict["handle"] = handle
    
    #estraggo la tabella che contiene i metadati della publicazione
    table = pub.find("table", class_ = "card-body table itemDisplayTable")
    metadata_rows = table.find_all("tr")

    #for utilizzato per estrarre riga per riga tutti i metadati
    for tr in metadata_rows:
        label_td = tr.find("td", class_="metadataFieldLabel")
        value_td = tr.find("td", class_="metadataFieldValue")

        #se manca la label o il valore salto la riga
        if not label_td or not value_td:
            continue
        

        #Estraggo la chiave del metadato
        key = label_td.get_text(strip=True)
        #Estraggo il valore del metadato
        value = value_td.get_text(strip=True)

        #Se la chiave rientra nelle chiavi che prevedono piu' di un valore li salvo in una lsita
        if key in multi_fields:
            pub_dict.setdefault(key, []).append(value)
        else:
            pub_dict[key] = value

    #Estraggo l'ultimo aggiornamento dalla pubblicazione appena recuperata dal sito in millisecondi
    pub_last_update = int(pub_dict.get("iris.orcid.lastModifiedMillisecond", 0))    

    for i, p in enumerate(data):    #Scorro le pubblicazioni con indice per poterle eventualmente aggiornare nella lista
        if p["handle"] == handle:
            #Estraggo la data dell'ultimo aggiornamento della stessa pubblicazione aggiornata all'ultima esecuzione dello script
            old_last = int(p.get("iris.orcid.lastModifiedMillisecond", 0))

            #Se la pubblicazione non è stata aggiornata rispetto alla versione salvata, non faccio nulla
            if pub_last_update <= old_last:     
                print("not updating..", end = " ")
                return data

            
            #Se è cambiata sovrascrivo
            print("updating..", end = " ")
            data[i] = pub_dict
            return data

    
    #Aggiungo la pubblicazione a data e lo ritorno
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
    rpp = 50        #Variabile che indica il numero di pubblicazioni viste per pagine
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

                data = upsert_publication(data,soup)

                print(count)
                count += 1    

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