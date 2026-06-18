"""
routers/bookings.py — Prenotazioni spazi e gestione inviti.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db, Booking, Space, Invitation, Notification

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class BookingCreate(BaseModel):
    space_id:       int
    user:           str
    start_time:     str          # "YYYY-MM-DD HH:MM"
    duration_hours: int
    invited_users:  Optional[List[str]] = []


def _parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise HTTPException(status_code=400, detail=f"Formato data non valido: {s}")


def _serialize_booking(b: Booking) -> dict:
    return {
        "id":          b.id,
        "space_id":    b.space_id,
        "space_name":  b.space.name if b.space else "?",
        "user":        b.user,
        "start_time":  b.start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time":    b.end_time.strftime("%Y-%m-%d %H:%M"),
        "invitations": [
            {"username": i.username, "status": i.status}
            for i in b.invitations
        ],
    }


@router.get("")
def list_bookings(
    user: Optional[str] = Query(None),
    space_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Senza parametri → tutte le prenotazioni (admin).
    ?user=X         → prenotazioni dell'utente X (owner + invitato accettato).
    ?space_id=N     → prenotazioni per uno spazio (timeline).
    """
    q = db.query(Booking)
    if space_id:
        q = q.filter(Booking.space_id == space_id)

    if user:
        # prenotazioni come owner
        own = q.filter(Booking.user == user).all()
        # prenotazioni come invitato accettato
        accepted_ids = [
            inv.booking_id
            for inv in db.query(Invitation).filter(
                Invitation.username == user,
                Invitation.status == "accepted"
            ).all()
        ]
        guest = db.query(Booking).filter(Booking.id.in_(accepted_ids)).all()
        seen = {b.id for b in own}
        all_bookings = own + [b for b in guest if b.id not in seen]
        return [_serialize_booking(b) for b in all_bookings]

    return [_serialize_booking(b) for b in q.all()]


@router.post("")
def create_booking(data: BookingCreate, db: Session = Depends(get_db)):
    space = db.query(Space).filter(Space.id == data.space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato.")
    if not space.active:
        raise HTTPException(status_code=400, detail="Lo spazio non è attualmente disponibile.")

    start = _parse_dt(data.start_time)
    end   = start + timedelta(hours=data.duration_hours)
    now   = datetime.utcnow()

    if start < now:
        raise HTTPException(status_code=400, detail="Non puoi prenotare nel passato.")

    # Verifica sovrapposizioni
    conflict = db.query(Booking).filter(
        Booking.space_id == data.space_id,
        Booking.start_time < end,
        Booking.end_time   > start,
    ).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Orario non disponibile: occupato da {conflict.user} fino a {conflict.end_time.strftime('%H:%M')}."
        )

    booking = Booking(
        space_id=data.space_id,
        user=data.user,
        start_time=start,
        end_time=end,
    )
    db.add(booking)
    db.flush()   # ottieni l'id prima del commit

    # Inviti
    for invited in data.invited_users:
        from database import User
        if db.query(User).filter(User.username == invited).first():
            inv = Invitation(booking_id=booking.id, username=invited)
            db.add(inv)
            db.add(Notification(
                user=invited,
                message=(
                    f"📬 INVITO | {data.user} ti ha invitato alla prenotazione di '{space.name}' "
                    f"il {start.strftime('%d/%m/%Y')} dalle {start.strftime('%H:%M')} alle {end.strftime('%H:%M')}. "
                    f"Vai nelle notifiche per accettare o declinare."
                )
            ))

    db.commit()
    db.refresh(booking)
    return {"message": "Prenotazione completata con successo!", "booking": _serialize_booking(booking)}


@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, user: str = Query(...), db: Session = Depends(get_db)):
    from database import User as UserModel
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata.")

    # Controlla se l'utente è admin
    current_user_obj = db.query(UserModel).filter(UserModel.username == user).first()
    is_admin = current_user_obj and current_user_obj.role == "admin"

    if booking.user != user and not is_admin:
        raise HTTPException(status_code=403, detail="Non hai il permesso di cancellare questa prenotazione.")

    space_name = booking.space.name if booking.space else "?"

    # Se l'admin cancella la prenotazione di un altro utente, notifica il proprietario
    if is_admin and booking.user != user:
        db.add(Notification(
            user=booking.user,
            message=(
                f"⚠️ CANCELLAZIONE ADMIN | La tua prenotazione di '{space_name}' "
                f"del {booking.start_time.strftime('%d/%m/%Y %H:%M')} "
                f"è stata cancellata dall'amministratore."
            )
        ))

    # Notifica gli invitati
    for inv in booking.invitations:
        if inv.username != user:
            db.add(Notification(
                user=inv.username,
                message=(
                    f"❌ La prenotazione di '{space_name}' "
                    f"del {booking.start_time.strftime('%d/%m/%Y %H:%M')} "
                    f"a cui eri invitato è stata cancellata."
                )
            ))

    db.delete(booking)
    db.commit()
    return {"message": "Prenotazione cancellata."}
