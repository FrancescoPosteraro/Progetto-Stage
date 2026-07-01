from bs4 import BeautifulSoup
import requests, webbrowser, json, os, time
from urllib.parse import urlparse, parse_qs

start_time = time.time()

JSON_PATH = os.path.join("C:\\", "Users", "franc", "Desktop", "Progetto-Stage", "publications.json")
file_path = r"C:\Users\franc\Desktop\Progetto-Stage\seconds.txt"

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





def upsert_publication(data, pub):

    

    pub_dict = {}

    div = pub.find("div", class_="accordion-body")
    handle_link = div.find("code").get_text(strip=True) if div and div.find("code") else None
    handle= handle_link.split("/")[-1]

    
    # se non c'è handle, salta
    if not handle:
        return data
    
    pub_dict["handle"] = handle
    
    table = pub.find("table", class_ = "card-body table itemDisplayTable")
    metadata_rows = table.find_all("tr")

    # metadata
    for tr in metadata_rows:
        label_td = tr.find("td", class_="metadataFieldLabel")
        value_td = tr.find("td", class_="metadataFieldValue")

        if not label_td or not value_td:
            continue

        key = label_td.get_text(strip=True)
        value = value_td.get_text(strip=True)

        if key in multi_fields:
            pub_dict.setdefault(key, []).append(value)
        else:
            pub_dict[key] = value

    data.append(pub_dict)

    return data


def update_json_file():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []


def init_json_file():
    data = []
    start = 0
    rpp = 25
    count = 1

    while True:
        tr = 2
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
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", class_="table table-striped table-hover")

        if table:
            links = table.find_all("tr")[1:]
        else:
            links = []

        # STOP condizione (pagina vuota)
        if not links:
            break

        for link in links:
            td = link.find("td", id="t_" + str(tr) + "_1")

            if td:
                a_tag = td.find("a", href=True)
                if a_tag:
                    href = a_tag["href"]


            pub_url = "https://boa.unimib.it" + href + "?mode=full"
            # scarico pagina pubblicazione
            response = requests.get(pub_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            
            data = upsert_publication(data, soup)
            print(count)
            count += 1
            tr += 1

        # ultima pagina (meno di 25 risultati)
        if len(links) < rpp:
            break

        start += rpp
        

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"JSON creato con {len(data)} pubblicazioni")






if os.path.exists(JSON_PATH):
    print("Aggiornamento")

else:
    print("Creazione");
    init_json_file()




end_time = time.time()

tempo_esecuzione = end_time - start_time


with open(file_path, "a") as file:
    file.write(f"{tempo_esecuzione}\n")

print(f"Tempo di esecuzione: {tempo_esecuzione:.4f} secondi")
