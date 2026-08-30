"""
    Questo modulo contiene i servizi relativi alle pubblicazioni.

    I servizi contengono la logica di business dell'applicazione e si occupano
    di coordinare le operazioni tra le rotte dell'API e i repository.

    I servizi gestiscono la validazione dei dati, la gestione degli errori
    e la logica necessaria per elaborare i risultati restituiti dai repository,
    come la paginazione delle pubblicazioni.

    I servizi sono utilizzati dalle rotte dell'API per fornire le funzionalità
    richieste dagli utenti.
"""

from fastapi import HTTPException
from repositories import publication_repository

"""
    Recupero le pubblicazioni più recenti, con paginazione.
    Restituisco una tupla contenente la lista delle pubblicazioni e informaztioni sulla paginazione.
"""
def get_latest_publications(page: int = 1, per_page: int = 10):

    if page < 1 and per_page < 1:
        raise HTTPException(status_code=400, detail="Il numero della pagina e il numero di elementi per pagina devono essere maggiori di 0.")

    if page < 1:
        raise HTTPException(status_code=400, detail="Il numero della pagina deve essere maggiore di 0.")

    if per_page < 1:
        raise HTTPException(status_code=400, detail="Il numero di elementi per pagina deve essere maggiore di 0.")

    publications, total = publication_repository.get_latest_publications(page, per_page)

    pages = (total + per_page - 1) // per_page

    return {
        "data": publications,
        "meta": {
            "total": total,
            "count": len(publications),
            "pages": pages,
            "page": page,
            "per_page": per_page
        }
    }


"""
    Recupera le pubblicazioni in base al nome e al cognome dell'autore.
    Se non viene fornito nessun parametro, restituisce un errore.
    Se viene fornito un parametro vuoto, restituisce un errore.
"""
def get_publications_by_author(name: str = None, surname: str = None):

    if not surname:
        raise HTTPException(status_code=400, detail="Cognome è obbligatorio")

    publications = publication_repository.get_publications_by_author(name, surname)

    if publications is None:
        raise HTTPException(status_code=404, detail="Autore non trovato")

    return publications