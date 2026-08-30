"""
========================================================
NOME FILE: database_manager.py

AUTORE: Francesco Posteraro

DESCRIZIONE:
Modulo per la gestione della sincronizzazione tra le pubblicazioni
ottenute dallo scraper e il database PostgreSQL.

Contiene funzioni per la sincronizzazione del database con il file publications.json.

========================================================
"""


import os
import psycopg      #Libreria utile per la connessione e la gestione del database PostgreSQL
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

#export DB_PASSWORD="la_password_del_database"

#Parametri per la connessione con il database
DB_CONFIG = {
    "host": "localhost",                    #indirizzo del server PostgreSQL
    "port": 5432,                           #porta utilizzata dal servizio di PostgreSQL
    "dbname": "publications_IRIS_BOA",      #nome del database
    "user": "postgres",                     #Utente PostgreSQL utilizzato per l'accesso
    "password": os.getenv("DB_PASSWORD")               #password dell'utente
}


# ==========================================================
# Nome funzione: get_connection
#
# Descrizione:
# Crea e restituisce una connessione al database PostgreSQL.
# ==========================================================
def get_connection():
    return psycopg.connect(**DB_CONFIG)

# ==========================================================
# Nome funzione: insert_publication_table
#
# Descrizione:
# Inserisce i dati principali di una pubblicazione nella tabella
# publications del database.
#
# La funzione gestisce solamente le informazioni relative alla
# pubblicazione (titolo, DOI, anno, tipologia, URL, ecc.).
#
# Autori e keyword vengono gestiti separatamente attraverso
# le rispettive tabelle associative per le relazioni N:N.
# ==========================================================
def insert_publication_table(cur, pub):

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
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            pub["handle"],      #handle
            pub["title"],       #titolo
            pub["doi"],         #doi
            pub["year"],        #anno di pubblicazione
            pub["type"],        #tipologia di pubblicazione
            pub["type_driver"], #classificazione IRIS del tipo
            pub["venue"],       #nome rivista o nome conferenza
            pub["url"],         #link della risorsa
            pub["last_update"]  #ultimo aggiornamento IRIS
        )
    )


# ==========================================================
# Nome funzione: insert_author
#
# Descrizione:
# Inserisce i dati di un autore nella tabella authors.
#
# La funzione controlla automaticamente la presenza di un
# autore con lo stesso identificativo per evitare duplicati.
#
# In caso di inserimento di un nuovo autore restituisce il suo id.
# Se l'autore è già presente nel database, restituisce comunque
# il suo identificativo per permettere la creazione del collegamento
# con la pubblicazione nella tabella associativa N:N.
# ==========================================================
def insert_author(cur, author):

    #inserisce l'autore nella tabella, se già presenta non verrà duplicato tramite "ON CONFLICT (id) DO NOTHING"
    cur.execute(
        """
        INSERT INTO authors
        (
            id,
            name,
            surname
        )

        VALUES
        (
            %s,
            %s,
            %s
        )

        ON CONFLICT (id) DO NOTHING

        RETURNING id
        """,
        (
            author["id"],       #id
            author["name"],     #nome
            author["surname"]   #cognome
        )
    )


    result = cur.fetchone()


    #Se l'autore è stato appena inserito,
    #restituisce l'id ottenuto dal database
    if result:
        return result[0]


    #Se l'autore era già presente,
    #restituisce direttamente il suo id
    return author["id"]


# ==========================================================
# Nome funzione: link_author_publication
#
# Descrizione:
# Crea il collegamento tra una pubblicazione e un autore
# nella tabella associativa publications_authors.
#
# La tabella gestisce la relazione molti-a-molti (N:N)
# tra publications e authors.
#
# Se il collegamento tra autore e pubblicazione esiste già,
# evita la duplicazione tramite ON CONFLICT DO NOTHING.
# ==========================================================
def link_author_publication(cur, handle, author_id):

    cur.execute(
        """
        INSERT INTO publications_authors
        (
            publication_handle,
            author_id
        )

        VALUES
        (
            %s,
            %s
        )

        ON CONFLICT DO NOTHING
        """,
        (
            handle,         #identificativo della pubblicazione
            author_id       #id dell'autore
        )
    )

# ==========================================================
# Nome funzione: insert_keyword
#
# Descrizione:
# Inserisce una keyword nella tabella keywords del database.
#
# La funzione evita la creazione di duplicati controllando
# il nome della keyword tramite il vincolo ON CONFLICT (name).
#
# Se la keyword viene inserita restituisce il nuovo id.
# Se invece la keyword è già presente nel database, recupera
# e restituisce il suo identificativo esistente.
# ==========================================================
def insert_keyword(cur, keyword):

    #inserisce la keyword nella tabella, se già presenta non verrà duplicato tramite "ON CONFLICT (id) DO NOTHING"
    cur.execute(
        """
        INSERT INTO keywords
        (
            name
        )

        VALUES
        (
            %s
        )

        ON CONFLICT (name) DO NOTHING

        RETURNING id
        """,
        (keyword,)
    )


    result = cur.fetchone()

    #Se la keyword é stata inserita adesso restituisce l'id
    if result:
        return result[0]

    #Se la keyword era già presente nel database recupera l'id
    cur.execute(
        """
        SELECT id
        FROM keywords
        WHERE name = %s
        """,
        (keyword,)
    )

    #restituisce l'id della keyword cercata
    return cur.fetchone()[0]

# ==========================================================
# Nome funzione: link_keyword_publication
#
# Descrizione:
# Crea il collegamento tra una pubblicazione e una keyword
# nella tabella associativa publications_keywords.
#
# La tabella gestisce la relazione molti-a-molti (N:N)
# tra publications e keywords.
#
# Se il collegamento esiste già, evita la duplicazione.
# ==========================================================
def link_keyword_publication(cur, handle, keyword_id):

    cur.execute(
        """
        INSERT INTO publications_keywords
        (
            publication_handle,
            keyword_id
        )

        VALUES
        (
            %s,
            %s
        )

        ON CONFLICT DO NOTHING
        """,
        (
            handle,         #handle pubblicazione
            keyword_id      #id keyword
        )
    )

# ==========================================================
# Nome funzione: insert_publication
#
# Descrizione:
# Inserisce una nuova pubblicazione nel database.
#
# La funzione gestisce:
#   - inserimento dei dati principali della pubblicazione
#   - inserimento degli autori e dei collegamenti N:N
#   - inserimento delle keyword e dei collegamenti N:N
#
# ==========================================================
def insert_publication(pub):

    #Apertura della connessione al database
    with get_connection() as con:
        #Creazione del cursore cur per eseguire le query SQL
        with con.cursor() as cur:

            # 1) Inserimento dati della pubblicazione nella tabella publications
            insert_publication_table(cur, pub)


            # 2) Inserimento dati degli autori nella tabella authors
            for author in pub["authors"]:
                author_id = insert_author(cur, author)  #inserimento, se non presente, di ogni autore

                link_author_publication(cur, pub["handle"], author_id)      #creo il collegamento tra autori e la pubblicazione nella tabella associativa publications_authors


            # 3) Inserimento delle keyword nella tabella keywords
            for keyword in pub["keywords"]:
                keyword_id = insert_keyword(cur, keyword)   #inserimento delle keyword nella tabella keywords

                link_keyword_publication(cur, pub["handle"], keyword_id)    #creo il collegamento, nella tabella associativa publications_keywords, tra la pubblicazione e le keyword

        #Conferma definitiva delle modifiche al database
        con.commit()

# ==========================================================
# Nome funzione: get_publication
#
# Descrizione:
# Recupera una pubblicazione dal database tramite il suo handle.
#
# La funzione esegue una query sulla tabella publications
# e ricostruisce un dizionario con la struttura utilizzata
# dal sistema di sincronizzazione.
#
# Se la pubblicazione non viene trovata, restituisce None.
# ==========================================================
def get_publication(cur, handle):

    #recupero i dati tramite handle
    cur.execute(
        """
        SELECT
            handle,
            title,
            doi,
            year,
            type,
            type_driver,
            venue,
            url,
            last_update

        FROM publications

        WHERE handle = %s
        """,
        (handle,)
    )


    row = cur.fetchone()

    #Se non esiste una pubblicazione con questo handle,
    #restituisce None
    if row is None:
        return None

    #Costruisce il dizionario della pubblicazione
    #con la stessa struttura utilizzata dal pub_dict
    publication = {
        "handle": row[0],
        "title": row[1],
        "doi": row[2],
        "year": row[3],
        "type": row[4],
        "type_driver": row[5],
        "venue": row[6],
        "url": row[7],
        "last_update": row[8],
        
        #Questi campi vengono gestiti in modo separato in altre funzioni
        "authors": [],
        "keywords": []
    }

    #ritorno la pubblicazione
    return publication

# ==========================================================
# Nome funzione: update_publication_table
#
# Descrizione:
# Confronta i dati di una pubblicazione proveniente dallo
# scraping con quelli presenti nel database.
#
# Aggiorna solamente i campi che risultano modificati,
# evitando UPDATE inutili.
#
# Il campo last_update viene aggiornato sempre perché indica
# l'ultima modifica rilevata dalla sorgente.
#
# ==========================================================
def update_publication_table(cur, pub):

    #recupero la pubblicazione dal database tramite handle
    old_pub = get_publication(cur, pub["handle"])

    #creo un dizionario che contiene solo i campi modificati
    changes = {}

    #una serie di if per capire quali campi sono stati modificati
    if pub["title"] != old_pub["title"]:
        changes["title"] = pub["title"]

    if pub["doi"] != old_pub["doi"]:
        changes["doi"] = pub["doi"]

    if int(pub["year"]) != old_pub["year"]:
        changes["year"] = pub["year"]

    if pub["type"] != old_pub["type"]:
        changes["type"] = pub["type"]

    if pub["type_driver"] != old_pub["type_driver"]:
        changes["type_driver"] = pub["type_driver"]

    if pub["venue"] != old_pub["venue"]:
        changes["venue"] = pub["venue"]

    if pub["url"] != old_pub["url"]:
        changes["url"] = pub["url"]

    changes["last_update"] = pub["last_update"]

    #costruisco dinamicamente la query update,
    #vengono aggiunti solo i campi realmente cambiati
    fields = []
    values = []
    
    for key, value in changes.items():
        fields.append(f"{key} = %s") #utilizzo le f-string di python per inserire il valore della variabile
        values.append(value)


    #aggiorno automaticamente update_time per via delle modifiche
    fields.append("update_time = NOW()")

    #il valore finale viene usato nella clausola WHERE, per trovare la pubblicazione
    values.append(pub["handle"])

    #creo la query, usando {", ".join(fields)} posso inserire i campi che sono stati modificati in fields
    query = f"""        
        UPDATE publications
        SET {", ".join(fields)}
        WHERE handle = %s
    """


    cur.execute(query, values)  #Eseguo l'aggiornamento

# ==========================================================
# Nome funzione: get_publication_authors
#
# Descrizione:
# Recupera gli identificativi degli autori associati ad una
# pubblicazione tramite la tabella associativa
# publication_authors.
#
# Restituisce un insieme (set) contenente gli id degli autori
# collegati alla pubblicazione.
# ==========================================================
def get_publication_authors(cur, handle):

    cur.execute(
        """
        SELECT author_id
        FROM publications_authors
        WHERE publication_handle = %s
        """,
        (handle,)
    )

    #Recupera tutte le righe restituite dalla query
    rows = cur.fetchall()

    #Crea un set degli id degli autori.
    #Il set evita eventuali duplicati e permette di confrontare
    return set(row[0] for row in rows)


# ==========================================================
# Nome funzione: sync_authors
#
# Descrizione:
# Sincronizza gli autori associati ad una pubblicazione.
#
# Confronta gli autori presenti nel database con quelli
# ottenuti dallo scraping e aggiorna la tabella associativa
# publications_authors.
#
# Gestisce:
#   - aggiunta di nuovi autori
#   - creazione degli autori mancanti nella tabella authors
#   - rimozione dei collegamenti non più presenti
#
# La tabella authors viene aggiornata separatamente rispetto
# alla relazione N:N con publications.
# ==========================================================
def sync_authors(cur, pub):

    #recupero glia utori collegati alla pubblicazione
    old_authors = get_publication_authors(cur, pub["handle"])

    #creo un insieme degli autori presenti nel nuovo scraping
    #utilizzando il loro identificativo
    new_authors = set(
        author["id"]
        for author in pub["authors"]
    )


    #individua gli autori presenti nello scraping ma non ancora
    #collegati alla pubblicazione nel database
    authors_to_add = new_authors - old_authors


    #individua gli autori presenti nel database ma non più
    #presenti nello scraping
    authors_to_remove = old_authors - new_authors



    #prima di collegari gli autori con la pubblicazione 
    #inserisco eventuali nuovi autori
    for author in pub["authors"]:
        if author["id"] in authors_to_add:

            insert_author(cur, author)


    #aggiungo i collegamenti mancanti tra la pubblicazione e gli autori
    for author_id in authors_to_add:
        link_author_publication(cur, pub["handle"], author_id)



    #rimuovo i collegamenti tra autori non piu presenti e la pubblicazione
    for author_id in authors_to_remove:
        cur.execute(
            """
            DELETE FROM publications_authors

            WHERE publication_handle = %s
            AND author_id = %s
            """,
            (
                pub["handle"],
                author_id
            )
        )

# ==========================================================
# Nome funzione: get_publication_keywords
#
# Descrizione:
# Recupera gli identificativi delle keyword associate ad una
# pubblicazione tramite la tabella associativa
# publications_keywords.
#
# Restituisce un insieme (set) contenente gli id delle keyword
# collegate alla pubblicazione.
# ==========================================================
def get_publication_keywords(cur, handle):

    cur.execute(
        """
        SELECT keyword_id
        FROM publications_keywords
        WHERE publication_handle = %s
        """,
        (handle,)
    )

    rows = cur.fetchall()

    return set(row[0] for row in rows)


# ==========================================================
# Nome funzione: sync_keywords
#
# Descrizione:
# Sincronizza le keyword associate ad una pubblicazione.
#
# Confronta le keyword presenti nel database con quelle
# ottenute dal nuovo scraping e aggiorna la tabella associativa
# publications_keywords.
#
# Gestisce:
#   - inserimento di nuove keyword nella tabella keywords
#   - aggiunta di nuovi collegamenti pubblicazione-keyword
#   - rimozione dei collegamenti non più presenti
#
# La tabella keywords mantiene le keyword esistenti nel database:
# se una keyword non è più associata ad una pubblicazione,
# viene eliminato solo il collegamento nella tabella associativa.
# ==========================================================
def sync_keywords(cur, pub):

    #recupero gli id delle keywords attualmente associate alla pubblicazione
    old_keywords = get_publication_keywords(cur, pub["handle"])


    #insieme delle keywords presenti nel nuovo scraping
    new_keywords = set()

    #inserisce eventuali nuove keyword nella tabella keywords
    #e recupera il loro identificativo
    for keyword in pub["keywords"]:
        keyword_id = insert_keyword(cur, keyword)
        new_keywords.add(keyword_id)



    #Calcola le differenze tra situazione precedente e nuova
    #keyword presenti nel nuovo scraping ma non ancora
    #collegate alla pubblicazione
    keywords_to_add = new_keywords - old_keywords

    #keywords presenti nel database ma non nel nuovo scraping
    keywords_to_remove = old_keywords - new_keywords



    #aggiungo le nuove relazioni tra keyword e pubblicazione
    for keyword_id in keywords_to_add:

        link_keyword_publication(cur, pub["handle"], keyword_id)



    #elimino le relazioni delle keyword non piu' presenti nella pubblicazione
    for keyword_id in keywords_to_remove:

        cur.execute(
            """
            DELETE FROM publications_keywords
            WHERE publication_handle = %s
            AND keyword_id = %s
            """,
            (
                pub["handle"],
                keyword_id
            )
        )

# ==========================================================
# Nome funzione: update_publication
#
# Descrizione:
# Aggiorna una pubblicazione già presente nel database.
#
# La funzione gestisce l'aggiornamento completo della
# pubblicazione attraverso tre operazioni separate:
#
#   1) aggiornamento dei campi principali della tabella
#      publications (solo quelli modificati)
#
#   2) sincronizzazione degli autori associati alla
#      pubblicazione tramite la relazione N:N
#
#   3) sincronizzazione delle keyword associate alla
#      pubblicazione tramite la relazione N:N
#
# Tutte le operazioni vengono eseguite all'interno della
# stessa transazione e confermate tramite commit finale.
# ==========================================================
def update_publication(pub):

    with get_connection() as con:
        with con.cursor() as cur:

            update_publication_table(cur, pub)      # 1)

            sync_authors(cur, pub)                  # 2)

            sync_keywords(cur, pub)                 # 3)

        con.commit()

# ==========================================================
# Nome funzione: sync_database
#
# Descrizione:
# Sincronizza una pubblicazione proveniente dallo scraping
# con il database.
#
# La funzione verifica se la pubblicazione è già presente:
#
#   - se non esiste:
#       viene eseguito un inserimento completo
#
#   - se esiste:
#       confronta il valore last_update per capire se la
#       pubblicazione è stata modificata
#
#       se è cambiata:
#           esegue l'aggiornamento dei dati e delle relazioni
#
#       se non è cambiata:
#           non esegue nessuna operazione
#
# ==========================================================
def sync_database(pub):

    with get_connection() as con:
        with con.cursor() as cur:

            #Cerca se la pubblicazione esiste già nel database
            #recuperando solamente il campo last_update,
            #necessario per il confronto
            cur.execute(
                """
                SELECT update_time
                FROM publications
                WHERE handle = %s
                """,
                (pub["handle"],)
            )

            old_pub = cur.fetchone()


    #Caso 1: pubblicazione nuova
    if old_pub is None:
        print("Nuova pubblicazione:", pub["handle"])
        insert_publication(pub)
    
    
    #Caso 2: pubblicazione già presente
    else:
        old_update_time = old_pub[0]
    
        #converte i millisecondi in datetime
        scraper_update_time = datetime.fromtimestamp(int(pub["last_update"]) / 1000)
    
        #Controllo se è cambiata
        if old_update_time < scraper_update_time:
            print("Pubblicazione modificata:", pub["handle"])
            update_publication(pub)
            #Caso 3: nessuna modifica
        else:
            print("Nessuna modifica:", pub["handle"])            
