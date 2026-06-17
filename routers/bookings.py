# File modificato: regesta/routers/bookings.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from models import BookingCreate
from config import load_db, save_db

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

def check_overlap(space_id: int, start: datetime, end: datetime, db_data, ignore_id: Optional[int] = None) -> bool:
    for b in db_data["bookings"]:
        if b["space_id"] == space_id and (ignore_id is None or b["id"] != ignore_id):
            b_start = datetime.strptime(b["start_time"], "%Y-%m-%d %H:%M")
            b_end = datetime.strptime(b["end_time"], "%Y-%m-%d %H:%M")
            if max(start, b_start) < min(end, b_end):
                return True
    return False

@router.get("")
def get_bookings(user: Optional[str] = None):
    data = load_db()
    if user:
        user_bookings = []
        for b in data["bookings"]:
            # Mostra la prenotazione se l'utente è il proprietario o se ha accettato l'invito
            if b["user"] == user:
                user_bookings.append(b)
            elif "invitations" in b:
                if any(inv["username"] == user and inv["status"] == "accepted" for inv in b["invitations"]):
                    user_bookings.append(b)
        return user_bookings
    return data["bookings"]

@router.post("")
def create_booking(booking: BookingCreate):
    data = load_db()
    space = next((s for s in data["spaces"] if s["id"] == booking.space_id and s["active"]), None)
    if not space:
        raise HTTPException(status_code=400, detail="Spazio non disponibile o in manutenzione.")
    
    if booking.duration_hours > 2:
        raise HTTPException(status_code=400, detail="Policy Limit: Massimo 2 ore consecutive.")
    
    start_dt = datetime.strptime(booking.start_time, "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(hours=booking.duration_hours)
    
    if check_overlap(booking.space_id, start_dt, end_dt, data):
        raise HTTPException(status_code=400, detail="Conflitto: Slot già occupato.")

    max_invites = space["capacity"] - 1
    if len([u for u in booking.invited_users if u.strip() and u.strip() != booking.user]) > max_invites:
        raise HTTPException(status_code=400, detail=f"Numero massimo di invitati superato. Puoi invitare al massimo {max_invites} persone.")
    
    new_id = max([b["id"] for b in data["bookings"]], default=0) + 1
    
    # Costruzione struttura inviti pendenti
    invitations_list = []
    if booking.invited_users:
        for u in booking.invited_users:
            clean_user = u.strip()
            if clean_user and clean_user != booking.user:
                invitations_list.append({"username": clean_user, "status": "pending"})

    new_booking = {
        "id": new_id, 
        "space_id": booking.space_id, 
        "space_name": space["name"],
        "user": booking.user, 
        "start_time": booking.start_time, 
        "end_time": end_dt.strftime("%Y-%m-%d %H:%M"),
        "invitations": invitations_list
    }
    data["bookings"].append(new_booking)

    if booking.invited_users:
        if "notifications" not in data:
            data["notifications"] = []
        for u in booking.invited_users:
            clean_user = u.strip()
            if clean_user and clean_user != booking.user:
                data["notifications"].append({
                    "user": clean_user,
                    "message": f"Sei stato invitato alla prenotazione dello spazio '{space['name']}' il {booking.start_time}."
                })

    save_db(data)
    return {"message": "Prenotazione salvata con successo!", "booking": new_booking}

@router.put("/{booking_id}")
def update_booking(booking_id: int, booking: BookingCreate):
    data = load_db()
    booking_record = next((b for b in data["bookings"] if b["id"] == booking_id), None)
    if not booking_record:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")
    if booking_record["user"] != booking.user:
        raise HTTPException(status_code=403, detail="Non autorizzato a modificare questa prenotazione.")

    space = next((s for s in data["spaces"] if s["id"] == booking.space_id and s.get("active", True)), None)
    if not space:
        raise HTTPException(status_code=400, detail="Spazio non disponibile o in manutenzione.")

    start_dt = datetime.strptime(booking.start_time, "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(hours=booking.duration_hours)
    if check_overlap(booking.space_id, start_dt, end_dt, data, ignore_id=booking_id):
        raise HTTPException(status_code=400, detail="Conflitto: Slot già occupato.")

    max_invites = space["capacity"] - 1
    invited_users = [u.strip() for u in booking.invited_users if u.strip() and u.strip() != booking.user]
    if len(invited_users) > max_invites:
        raise HTTPException(status_code=400, detail=f"Numero massimo di invitati superato. Puoi invitare al massimo {max_invites} persone.")

    existing_invites = {inv["username"]: inv for inv in booking_record.get("invitations", [])}
    new_invitations = []
    if "notifications" not in data:
        data["notifications"] = []

    for invited in invited_users:
        status = existing_invites.get(invited, {}).get("status", "pending")
        if invited not in existing_invites:
            data["notifications"].append({
                "user": invited,
                "message": f"Sei stato invitato alla prenotazione dello spazio '{space['name']}' il {booking.start_time}."
            })
        new_invitations.append({"username": invited, "status": status})

    booking_record["space_id"] = booking.space_id
    booking_record["space_name"] = space["name"]
    booking_record["start_time"] = booking.start_time
    booking_record["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M")
    booking_record["invitations"] = new_invitations

    save_db(data)
    return {"message": "Prenotazione aggiornata con successo!", "booking": booking_record}

@router.get("/invitations")
def get_invitations(user: str):
    data = load_db()
    pending = []
    for b in data["bookings"]:
        if "invitations" in b:
            for inv in b["invitations"]:
                if inv["username"] == user and inv["status"] == "pending":
                    pending.append({
                        "booking_id": b["id"],
                        "space_name": b["space_name"],
                        "start_time": b["start_time"],
                        "end_time": b["end_time"],
                        "host": b["user"]
                    })
    return pending

@router.post("/invitations/{booking_id}/respond")
def respond_invitation(booking_id: int, user: str, status: str):
    if status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Stato risposta non valido.")
    
    data = load_db()
    booking = next((b for b in data["bookings"] if b["id"] == booking_id), None)
    if not booking:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")
    
    invitation = next((inv for inv in booking.get("invitations", []) if inv["username"] == user), None)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invito non trovato per questo utente.")
    
    invitation["status"] = status
    
    # Invia notifica di aggiornamento all'organizzatore della prenotazione
    if "notifications" not in data:
        data["notifications"] = []
    
    stato_it = "accettato" if status == "accepted" else "declinato"
    data["notifications"].append({
        "user": booking["user"],
        "message": f"L'utente {user} ha {stato_it} il tuo invito per l'aula '{booking['space_name']}' del {booking['start_time']}."
    })
    
    save_db(data)
    return {"message": f"Invito {stato_it} con successo."}

@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, user: str):
    data = load_db()
    booking = next((b for b in data["bookings"] if b["id"] == booking_id), None)
    if not booking:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")
    if booking["user"] != user:
        raise HTTPException(status_code=403, detail="Non autorizzato.")
        
    data["bookings"] = [b for b in data["bookings"] if b["id"] != booking_id]
    save_db(data)
    return {"message": "Prenotazione cancellata."}