"""
    Questo modulo contiene le rotte dell'API relative alle pubblicazioni.

    Utilizza il router di FastAPI per definire le rotte e i metodi HTTP associati.

    Le rotte permettono di recuperare le ultime pubblicazioni con paginazione,
    le pubblicazioni di un autore specifico e altre informazioni relative
    alle pubblicazioni.

    Le rotte utilizzano i servizi definiti nel modulo
    services/publication_service.py per gestire la logica delle richieste
    e recuperare i dati dal database.

    Le rotte sono documentate automaticamente da FastAPI e possono essere
    testate tramite l'interfaccia Swagger disponibile all'indirizzo /docs.
"""

from fastapi import APIRouter   #API Router è una classe di FastAPI che consente di creare un router per gestire le rotte dell'API. La utilizzo per raggruppare le rotte relative alle pubblicazioni in un unico router.
from services import publication_service


router = APIRouter()


"""
    Endpoint per prelevare le ultime pubblicazioni N pubblicazioni oppure le pubblicazioni di una pagina specifica.
    Se non viene fornito nessun parametro, restituisce le ultime 10 pubblicazioni.
    Se viene fornito un parametro vuoto, restituisce un errore.
    Se viene fornito un parametro negativo o uguale a 0, restituisce un errore.
"""
@router.get("/publications/latest")
def get_latest_publications(page: int = 1, per_page: int = 10):
    return publication_service.get_latest_publications(page, per_page)

"""
    Endpoint per prelevare gli autori in base al nome e/o cognome.
    Se non viene fornito nessun parametro, restituisce un errore.
    Se viene fornito un parametro vuoto, restituisce un errore.
"""
@router.get("/publications/authors")
def get_publications_by_author(name: str = None, surname: str = None):
    name = name.strip() if name else None
    surname = surname.strip() if surname else None
    return publication_service.get_publications_by_author(name, surname)
