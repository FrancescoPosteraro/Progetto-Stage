"""
    Questo modulo contiene le funzioni per l'accesso al database delle pubblicazioni.

    Le funzioni del repository eseguono le query SQL necessarie per recuperare
    i dati relativi alle pubblicazioni, agli autori e alle parole chiave.

    Il repository gestisce le connessioni al database e restituisce i risultati
    ai servizi.

    Il repository utilizza get_connection, importato da
    database.database_manager, per gestire le connessioni al database.
"""
from database.database_manager import get_connection

"""
    Recupero le pubblicazioni più recenti, con paginazione.
    Restituisco una tupla contenente la lista delle pubblicazioni e informazioni sulla paginazione.
"""
def get_latest_publications(page: int, per_page: int):

    offset = (page - 1) * per_page

    with get_connection() as con:
        with con.cursor() as cur:

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
                WHERE active = TRUE
                ORDER BY year DESC
                LIMIT %s
                OFFSET %s
                """,
                (per_page, offset),
            )

            rows = cur.fetchall()

            publications = []

            for row in rows:

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
                    "authors": [],
                    "keywords": []
                }

                # Recupero degli autori
                cur.execute(
                    """
                    SELECT
                        a.id,
                        a.name,
                        a.surname
                    FROM authors a
                    JOIN publications_authors pa
                        ON a.id = pa.author_id
                    WHERE pa.publication_handle = %s
                    """,
                    (publication["handle"],)
                )

                authors = cur.fetchall()

                for author in authors:
                    publication["authors"].append({
                        "id": author[0],
                        "name": author[1],
                        "surname": author[2]
                    })

                
                cur.execute(
                    """
                    SELECT
                        k.name
                    FROM keywords k
                    JOIN publications_keywords pk
                        ON k.id = pk.keyword_id
                    WHERE pk.publication_handle = %s
                    """,
                    (publication["handle"],)
                )

                keywords = cur.fetchall()

                for keyword in keywords:
                    publication["keywords"].append(keyword[0])

                publications.append(publication)

            
            cur.execute(
                """
                SELECT COUNT(*)
                FROM publications
                WHERE active = TRUE
                """
            )

            total = cur.fetchone()[0]

            return publications, total


"""
    Recupero le pubblicazione tramite nome e cognome di un autore.
    Se non viene trovato nessun autore con quel nome e cognome, restituisco None.
"""
def get_publications_by_author(name: str, surname: str):
    
    with get_connection() as con:
        with con.cursor() as cur:

            if name:
                cur.execute(
                    """
                    SELECT id
                    FROM authors
                    WHERE LOWER(name) = LOWER(%s)
                    AND LOWER(surname) = LOWER(%s)
                    """,
                    (name, surname),
                )
            else:
                cur.execute(
                    """
                    SELECT id
                    FROM authors
                    WHERE name IS NULL
                    AND LOWER(surname) = LOWER(%s)
                    """,
                    (surname,),
                )

            author = cur.fetchone()

            
            if author is None:
                return None

            author_id = author[0]

            cur.execute(
                """
                SELECT
                    p.handle,
                    p.title,
                    p.doi,
                    p.year,
                    p.type,
                    p.type_driver,
                    p.venue,
                    p.url,
                    p.last_update
                FROM publications p
                JOIN publications_authors pa
                    ON p.handle = pa.publication_handle
                WHERE pa.author_id = %s
                AND p.active = TRUE
                """,
                (author_id,),
            )

            rows = cur.fetchall()

            publications = []

            for row in rows:

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
                    "authors": [],
                    "keywords": []
                }

                
                cur.execute(
                    """
                    SELECT
                        a.id,
                        a.name,
                        a.surname
                    FROM authors a
                    JOIN publications_authors pa
                        ON a.id = pa.author_id
                    WHERE pa.publication_handle = %s
                    """,
                    (publication["handle"],)
                )

                authors = cur.fetchall()

                for author in authors:
                    publication["authors"].append({
                        "id": author[0],
                        "name": author[1],
                        "surname": author[2]
                    })

                
                cur.execute(
                    """
                    SELECT
                        k.name
                    FROM keywords k
                    JOIN publications_keywords pk
                        ON k.id = pk.keyword_id
                    WHERE pk.publication_handle = %s
                    """,
                    (publication["handle"],)
                )

                keywords = cur.fetchall()

                for keyword in keywords:
                    publication["keywords"].append(keyword[0])

                publications.append(publication)

            return publications  
