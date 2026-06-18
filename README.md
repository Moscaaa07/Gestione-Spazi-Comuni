# Gestione Spazi Comuni — Backend Python

## Struttura del progetto

```
app/
├── main.py              # Entry point FastAPI
├── database.py          # Modelli SQLAlchemy + configurazione SQLite
├── seed.py              # Script per popolare il DB con dati iniziali
├── requirements.txt
├── routers/
│   ├── auth.py          # Login, registrazione, profilo, amici, notifiche, chat
│   ├── spaces.py        # CRUD spazi/aule
│   └── bookings.py      # Prenotazioni + inviti
└── static/
    └── index.html       # ← copia qui il tuo index.html
```

## Installazione

```bash
pip install -r requirements.txt
```

## Primo avvio

```bash
# 1. Crea il DB e inserisci dati di esempio
python seed.py

# 2. Avvia il server
python -m uvicorn main:app --reload --port 8000
```

Apri il browser su: **http://localhost:8000**

## Credenziali di default (dopo seed.py)

| Email                  | Password   | Ruolo |
|------------------------|------------|-------|
| marco@scuola.it        | marco2026  | User  |
| elena@scuola.it        | elena2026  | User  |

## API principali

### Auth
| Metodo | Endpoint                          | Descrizione                    |
|--------|-----------------------------------|--------------------------------|
| POST   | /api/auth/login                   | Login                          |
| POST   | /api/auth/register                | Registrazione                  |
| POST   | /api/auth/reset-password          | Reset password                 |
| POST   | /api/auth/change-password         | Cambio password                |
| POST   | /api/auth/update-displayname      | Aggiorna nome visualizzato     |
| GET    | /api/auth/profile?user=X          | Profilo utente                 |
| POST   | /api/auth/friend-requests         | Invia richiesta amicizia       |
| POST   | /api/auth/friend-requests/respond | Accetta/rifiuta amicizia       |
| POST   | /api/auth/remove-friend           | Rimuovi amico                  |
| GET    | /api/auth/notifications?user=X    | Lista notifiche                |
| POST   | /api/auth/notifications/mark-read | Segna notifiche come lette     |
| DELETE | /api/auth/notifications           | Elimina notifiche              |
| GET    | /api/auth/invitations?user=X      | Inviti prenotazione pendenti   |
| POST   | /api/auth/invitations/respond     | Rispondi a un invito           |
| GET    | /api/auth/conversations?user=X    | Lista conversazioni chat       |
| GET    | /api/auth/messages?user=X&with_user=Y | Messaggi tra due utenti   |
| POST   | /api/auth/send-message            | Invia messaggio                |
| PUT    | /api/auth/messages/read           | Segna messaggi come letti      |

### Spazi
| Metodo | Endpoint                     | Descrizione                         |
|--------|------------------------------|-------------------------------------|
| GET    | /api/spaces                  | Lista spazi attivi (con filtri)     |
| GET    | /api/spaces/all-admin        | Tutti gli spazi (admin)             |
| POST   | /api/spaces                  | Crea nuovo spazio                   |
| PUT    | /api/spaces/{id}             | Aggiorna spazio                     |
| PATCH  | /api/spaces/{id}/toggle      | Attiva/disattiva spazio             |
| DELETE | /api/spaces/{id}             | Elimina spazio                      |

### Prenotazioni
| Metodo | Endpoint                  | Descrizione                              |
|--------|---------------------------|------------------------------------------|
| GET    | /api/bookings             | Tutte le prenotazioni (admin)            |
| GET    | /api/bookings?user=X      | Prenotazioni utente X                    |
| GET    | /api/bookings?space_id=N  | Prenotazioni per spazio (timeline)       |
| POST   | /api/bookings             | Crea prenotazione                        |
| DELETE | /api/bookings/{id}?user=X | Cancella prenotazione                    |

## Documentazione interattiva

Con il server avviato:  
**http://localhost:8000/** (Swagger UI)
