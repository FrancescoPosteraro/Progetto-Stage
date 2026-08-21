Per il funzionamento di tutto il progetto basta avviare il file "web_scraper.py".
Con questo file verranno prelevati dati dal sito web IRIS BOA, inoltre verrà gestito il file publication.json insieme al database(tramite database_manager.py).

La sottocartella Extra contiene file utilizzati per lo studio dei metadati delle pubblicazioni e script aggiuntivi dedicati all'analisi delle performance dello script principale.

La sottocartella database contiene i file relativi alla gestione del database, tra cui il file principale database_manager.py, alcuni script per i test e il diagramma della struttura del database.

Il file schema.sql contiene gli script SQL necessari alla creazione del database e delle relative tabelle.

Il progetto utilizza FastAPI per esporre le funzionalità dell'applicazione tramite API REST.
L'API rappresenta il livello di accesso al sistema e permette di interagire con la logica applicativa attraverso specifici endpoint HTTP.