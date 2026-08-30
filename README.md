# Sistema di gestione delle pubblicazioni

## 1. Descrizione del progetto

Il progetto realizza un sistema per il recupero, la gestione e l'esposizione tramite API di alcune pubblicazioni presenti sulla piattaforma IRIS.

Il sistema è composto principalmente da tre componenti:

- **Web Scraper**: recupera le informazioni relative alle pubblicazioni e ne gestisce l'aggiornamento, inoltre sincronizza il database con appositi moduli.
- **Database PostgreSQL**: memorizza le pubblicazioni, gli autori e le parole chiave.
- **API REST**: permette di consultare tramite endpoint HTTP le pubblicazioni presenti nel database.

---

## 2. Architettura

L'architettura del sistema è organizzata secondo il seguente flusso:

```text
                    ┌─────────────────┐
                    │      IRIS       │
                    │  Web Scraping   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Web Scraper    │
                    │                 │
                    │ Recupero dati   │
                    │ Aggiornamento   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │    Database     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   FastAPI       │
                    │      API        │
                    └────────┬────────┘
                             │
                             ▼
                       Client HTTP
```

Il Web Scraper è il componente responsabile del recupero e dell'aggiornamento dei dati.

Il database viene utilizzato internamente dal Web Scraper per la persistenza dei dati.

L'API permette invece ai client di consultare i dati memorizzati nel database.

L'esecuzione automatica del Web Scraper può essere gestita tramite un **cron job** su Ubuntu Server.

---

## 3. Requisiti

Per l'esecuzione del sistema sono necessari:

- Python 3.14.6
- PostgreSQL
- dipendenze Python presenti in `requirements.txt`

---

## 4. Installazione

Clonare la repository sulla macchina di destinazione.

Installare le dipendenze:

```bash
pip install -r requirements.txt
```

Il database PostgreSQL deve essere configurato sulla macchina e devono essere disponibili le credenziali necessarie al collegamento.

## Variabili d'ambiente e Cron Job

### Variabili d'ambiente

Il progetto utilizza la variabile `DB_PASSWORD` per la connessione al database PostgreSQL.

Creare il file `.env` a partire dal file `.env.example`:

```bash
cp .env.example .env
```

Inserire nel file `.env` la password dell'utente PostgreSQL:

```env
DB_PASSWORD=la_password_del_database
```

Il file `.env` contiene informazioni sensibili e non viene incluso nel repository.

### Cron Job

Per configurare l'esecuzione automatica dello scraper su Linux, eseguire:

```bash
bash install_cron.sh
```

Lo script configura automaticamente il cron job per eseguire lo scraper ogni domenica alle **03:00**.

L'output dello scraper viene salvato nel file `cron.log`.

---

## 5. Esecuzione

Il file `run.py` costituisce il punto di ingresso principale del progetto.

Sono disponibili tre comandi:

### Web Scraper

Per avviare manualmente il Web Scraper:

```bash
python run.py scraper
```

Il comando avvia il modulo:

```text
web_scraper.web_scraper
```

Il Web Scraper recupera le pubblicazioni e aggiorna i dati gestiti dal sistema.

### API

Per avviare l'API:

```bash
python run.py api
```

L'API viene avviata tramite Uvicorn utilizzando l'applicazione FastAPI definita in:

```text
api.main:app
```

### Test

Per eseguire tutti i test:

```bash
python run.py test
```

Il comando esegue la suite di test tramite `pytest`.

---

## 6. Database

Il sistema utilizza PostgreSQL per la persistenza dei dati.

Il database contiene le informazioni relative alle pubblicazioni e alle entità collegate, tra cui:

- pubblicazioni;
- autori;
- parole chiave;
- associazioni tra pubblicazioni e autori;
- associazioni tra pubblicazioni e parole chiave.

La gestione delle connessioni e delle operazioni sul database è centralizzata nel modulo:

```text
database/database_manager.py
```

Il Web Scraper utilizza direttamente il modulo di gestione del database durante la sincronizzazione.

---

# API 7

## Architettura dell'API

L'API è stata sviluppata utilizzando **FastAPI** e segue una struttura a **tre livelli**, con una separazione delle responsabilità:

```text
Client
  |
  v
Presentation Layer
(api/main.py - api/publications.py)
  |
  v
Business Logic Layer
(publication_service)
  |
  v
Data Access Layer
(database_manager)
  |
  v
PostgreSQL
```

### Presentation Layer

Il **Presentation Layer** gestisce le richieste HTTP ricevute dall'API e definisce gli endpoint disponibili.

Il file `api/main.py` crea l'applicazione FastAPI e registra i router, mentre `api/publications.py` contiene gli endpoint relativi alle pubblicazioni.

Questo livello si occupa quindi di ricevere i parametri della richiesta, effettuare le prime validazioni e restituire la risposta al client, senza accedere direttamente al database.

### Business Logic Layer

Il **Business Logic Layer** contiene la logica applicativa del sistema.

Gli endpoint delegano le operazioni al `publication_service`, che gestisce le richieste e applica le regole necessarie, ad esempio la gestione dei parametri e degli eventuali errori.

Il Service non esegue direttamente le query SQL: per recuperare i dati si rivolge al livello di accesso ai dati.

### Data Access Layer

Il **Data Access Layer** gestisce l'interazione con il database PostgreSQL ed è implementato tramite il `database_manager` e i repository utilizzati dall'API.

Questo livello si occupa di costruire ed eseguire le query SQL, recuperare i dati dal database e restituirli al Business Logic Layer.

La separazione dei tre livelli permette quindi di mantenere distinte le responsabilità: il **Presentation Layer** gestisce le richieste, il **Business Logic Layer** gestisce la logica applicativa e il **Data Access Layer** gestisce l'accesso ai dati. Questo rende il sistema più semplice da mantenere e modificare.

---

## Endpoint disponibili

### `GET /publications/latest`

Restituisce le pubblicazioni più recenti con paginazione.

Parametri:

- `page`: numero della pagina, default `1`
- `per_page`: numero di pubblicazioni per pagina, default `10`

Esempio:

```text
GET /publications/latest?page=1&per_page=10
```

L'endpoint delega la richiesta al service:

```python
@router.get("/publications/latest")
def get_latest_publications(page: int = 1, per_page: int = 10):
    return publication_service.get_latest_publications(page, per_page)
```

### `GET /publications/authors`

Restituisce le pubblicazioni associate a un autore.

Parametri:

- `name`: nome dell'autore
- `surname`: cognome dell'autore

È possibile utilizzare anche solo il cognome.

Esempi:

```text
GET /publications/authors?surname=Rossi
```

```text
GET /publications/authors?name=Mario&surname=Rossi
```

L'endpoint delega la richiesta al service:

```python
@router.get("/publications/authors")
def get_publications_by_author(name: str = None, surname: str = None):
    name = name.strip() if name else None
    surname = surname.strip() if surname else None

    return publication_service.get_publications_by_author(name, surname)
```

## Documentazione

FastAPI mette a disposizione la documentazione interattiva tramite Swagger UI:

```text
/docs
```

Dalla documentazione è possibile visualizzare e testare gli endpoint disponibili.

---

## 8. Cron Job

Su una macchina Ubuntu Server il Web Scraper può essere eseguito automaticamente tramite cron.

Il repository contiene lo script:

```text
install_cron.sh
```

Lo script registra il cron job sulla macchina.

L'esecuzione prevista è:

```text
Ogni domenica alle 03:00
```

Il comando eseguito automaticamente è equivalente a:

```bash
python run.py scraper
```

Il cron job permette quindi di eseguire periodicamente la sincronizzazione senza avviare manualmente il Web Scraper.

---

## 9. Test

Il progetto contiene test unitari, di integrazione e di consistenza tra i diversi componenti.

Per eseguire l'intera suite:

```bash
python run.py test
```

I test verificano, tra le altre cose:

- funzionamento del Web Scraper;
- funzionamento del database manager;
- integrazione tra Web Scraper e database;
- integrazione tra Web Scraper, database e API;
- consistenza tra dati JSON e database;
- funzionamento delle API.

---

## 10. Flusso operativo

Il funzionamento complessivo del sistema può essere riassunto nel seguente flusso:

```text
Cron Job
   │
   ▼
run.py scraper
   │
   ▼
Web Scraper
   │
   ├──────────────► publications.json
   │
   ▼
PostgreSQL
   │
   ▼
FastAPI
   │
   ▼
Client
```

Il Web Scraper rappresenta il punto di ingresso dei dati nel sistema, mentre l'API rappresenta il punto di accesso ai dati per i client.
