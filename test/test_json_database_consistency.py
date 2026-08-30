"""
========================================================
Nome File: test_json_database_consistency.py
AUTORE: Francesco Posteraro

DESCRIZIONE:
Test di coerenza tra i dati presenti nel file JSON
e quelli presenti nel database.

Il test ricostruisce le pubblicazioni dal database,
compresi autori e keyword presenti nelle relative
tabelle, e confronta il risultato con il JSON.

Il test non modifica né il file JSON né il database.
========================================================
"""

import json
import web_scraper.web_scraper as web_scraper
from database import database_manager


def test_json_database_consistency():

    with open(web_scraper.JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    with database_manager.get_connection() as con:
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
                """
            )

            publication_rows = cur.fetchall()

            database_data = []

            for row in publication_rows:

                handle = row[0]

                publication = {
                    "handle": row[0],
                    "title": row[1],
                    "doi": row[2],
                    "year": str(row[3]) if row[3] is not None else None,
                    "type": row[4],
                    "type_driver": row[5],
                    "venue": row[6],
                    "url": row[7],
                    "last_update": (
                        str(row[8])
                        if row[8] is not None
                        else None
                    )
                }

                cur.execute(
                    """
                    SELECT a.id, a.name, a.surname
                    FROM authors a
                    JOIN publications_authors pa
                        ON pa.author_id = a.id
                    WHERE pa.publication_handle = %s
                      AND pa.active = TRUE
                      AND a.active = TRUE
                    """,
                    (handle,)
                )

                author_rows = cur.fetchall()

                publication["authors"] = [
                    {
                        "id": str(author[0]),
                        "name": author[1],
                        "surname": author[2]
                    }
                    for author in author_rows
                ]

                cur.execute(
                    """
                    SELECT k.name
                    FROM keywords k
                    JOIN publications_keywords pk
                        ON pk.keyword_id = k.id
                    WHERE pk.publication_handle = %s
                      AND pk.active = TRUE
                      AND k.active = TRUE
                    """,
                    (handle,)
                )

                keyword_rows = cur.fetchall()

                publication["keywords"] = [
                    keyword[0]
                    for keyword in keyword_rows
                ]

                database_data.append(publication)

    def normalize(value):

        if isinstance(value, dict):
            return {
                key: normalize(val)
                for key, val in value.items()
            }

        if isinstance(value, list):

            normalized = [
                normalize(item)
                for item in value
            ]

            if all(isinstance(item, dict) for item in normalized):
                return sorted(
                    normalized,
                    key=lambda item: str(item)
                )

            return sorted(normalized, key=str)

        if isinstance(value, str):
            return value.strip().lower()

        return value

    json_normalized = normalize(json_data)
    database_normalized = normalize(database_data)

    json_handles = {
        publication["handle"]
        for publication in json_normalized
    }

    database_handles = {
        publication["handle"]
        for publication in database_normalized
    }

    assert json_handles == database_handles

    json_by_handle = {
        publication["handle"]: publication
        for publication in json_normalized
    }

    database_by_handle = {
        publication["handle"]: publication
        for publication in database_normalized
    }

    for handle in json_handles:
        assert json_by_handle[handle] == database_by_handle[handle]