"""
    Questo modulo contiene il codice principale dell'applicazione FastAPI.

    In questo modulo viene creata l'istanza dell'applicazione FastAPI e vengono registrati i router che definiscono gli endpoint dell'API. 
    I router contengono le rotte relative alle diverse funzionalità dell'applicazione e vengono inclusi nell'istanza principale di FastAPI. 
    
    L'applicazione può essere avviata tramite Uvicorn e la documentazione interattiva degli endpoint è disponibile tramite Swagger UI all'indirizzo /docs.
"""
from fastapi import FastAPI
from api.publications import router as publications_router

app = FastAPI()

app.include_router(publications_router)