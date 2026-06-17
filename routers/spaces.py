# File modificato: regesta/routers/spaces.py
from fastapi import APIRouter, HTTPException
from config import load_db, save_db
from models import SpaceCreate

router = APIRouter(prefix="/api/spaces", tags=["Spaces"])

@router.get("")
def get_spaces(capacity: int = 0, name: str = "", location: str = ""):
    data = load_db()
    # Filtra sia sulla capienza minima che sulla corrispondenza parziale del nome e luogo
    return [
        s for s in data["spaces"] 
        if s.get("active", True)
        and s["capacity"] >= capacity 
        and (name.lower() in s["name"].lower() if name else True)
        and (location.lower() == s.get("location", "").lower() if location else True)
    ]

@router.get("/all-admin")
def get_all_spaces_admin():
    data = load_db()
    return data["spaces"]

@router.post("")
def create_space(space_data: SpaceCreate):
    if not (1 <= space_data.capacity <= 40):
        raise HTTPException(status_code=400, detail="La capienza deve essere compresa tra 1 e 40 persone.")
        
    data = load_db()
    # Controllo univocità del nome nel luogo selezionato
    if any(s["name"].lower() == space_data.name.lower() and s.get("location", "").lower() == space_data.location.lower() for s in data["spaces"]):
        raise HTTPException(status_code=400, detail="Esiste già uno spazio con questo nome in questa sede.")

    new_id = max([s["id"] for s in data["spaces"]], default=0) + 1
    new_space = {
        "id": new_id,
        "name": space_data.name,
        "capacity": space_data.capacity,
        "equipment": space_data.equipment,
        "location": space_data.location,
        "active": True
    }
    data["spaces"].append(new_space)
    save_db(data)
    return {"message": "Spazio creato con successo", "space": new_space}

@router.put("/{id}")
def update_space(id: int, space_data: SpaceCreate):
    if not (1 <= space_data.capacity <= 40):
        raise HTTPException(status_code=400, detail="La capienza deve essere compresa tra 1 e 40 persone.")
    
    data = load_db()
    space = next((s for s in data["spaces"] if s["id"] == id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato.")
        
    # Controllo univocità del nome nello stesso luogo (escludendo se stesso)
    if any(s["name"].lower() == space_data.name.lower() and s.get("location", "").lower() == space_data.location.lower() and s["id"] != id for s in data["spaces"]):
        raise HTTPException(status_code=400, detail="Esiste già un altro spazio con questo nome in questa sede.")
        
    space["name"] = space_data.name
    space["capacity"] = space_data.capacity
    space["equipment"] = space_data.equipment
    space["location"] = space_data.location
    save_db(data)
    return {"message": "Spazio aggiornato con successo", "space": space}

@router.delete("/{id}")
def delete_space(id: int):
    data = load_db()
    space = next((s for s in data["spaces"] if s["id"] == id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato")
        
    prenotazioni_da_cancellare = [b for b in data["bookings"] if b["space_id"] == id]
    if prenotazioni_da_cancellare:
        data["bookings"] = [b for b in data["bookings"] if b["space_id"] != id]
        if "notifications" not in data:
            data["notifications"] = []
        for b in prenotazioni_da_cancellare:
            data["notifications"].append({
                "user": b["user"],
                "message": f"ATTENZIONE: Lo spazio '{space['name']}' è stato eliminato dall'amministratore. La tua prenotazione in data {b['start_time']} è stata annullata."
            })
            
    data["spaces"] = [s for s in data["spaces"] if s["id"] != id]
    save_db(data)
    return {"message": f"Spazio '{space['name']}' eliminato definitivamente dal sistema."}

@router.patch("/{id}/toggle")
def toggle_space(id: int):
    data = load_db()
    space = next((s for s in data["spaces"] if s["id"] == id), None)
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato")
    
    if "active" not in space:
        space["active"] = True
    space["active"] = not space["active"]

    if "notifications" not in data:
        data["notifications"] = []

    if space["active"]:
        message = f"Spazio '{space['name']}' attivato con successo!"
        for user in data["users"]:
            data["notifications"].append({
                "user": user["username"],
                "message": f"Lo spazio '{space['name']}' è di nuovo disponibile."
            })
    else:
        message = f"Spazio '{space['name']}' messo in manutenzione. "
        for user in data["users"]:
            data["notifications"].append({
                "user": user["username"],
                "message": f"Lo spazio '{space['name']}' è stato messo in manutenzione e non è più prenotabile."
            })
        prenotazioni_da_cancellare = [b for b in data["bookings"] if b["space_id"] == id]

        if prenotazioni_da_cancellare:
            data["bookings"] = [b for b in data["bookings"] if b["space_id"] != id]
            for b in prenotazioni_da_cancellare:
                avviso = {
                    "user": b["user"],
                    "message": f"ATTENZIONE: La tua prenotazione per lo spazio '{space['name']}' in data {b['start_time']} è stata cancellata perché la stanza è stata messa in manutenzione dall'amministratore."
                }
                data["notifications"].append(avviso)
            message += f" Cancellate {len(prenotazioni_da_cancellare)} prenotazioni attive. Gli utenti riceveranno un avviso al login."

    save_db(data)
    return {"message": message, "active": space["active"]}