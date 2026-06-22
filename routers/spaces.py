"""
routers/spaces.py — Gestione spazi/aule (CRUD + toggle stato).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, Space

router = APIRouter(prefix="/api/spaces", tags=["spaces"])


class SpaceCreate(BaseModel):
    name: str
    capacity: int
    equipment: Optional[str] = ""
    location: Optional[str] = "Regesta"

class SpaceUpdate(BaseModel):
    name: str
    capacity: int
    equipment: Optional[str] = ""
    location: Optional[str] = "Regesta"


@router.get("")
def list_active_spaces(
    name: Optional[str] = None,
    location: Optional[str] = None,
    equipment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Restituisce gli spazi attivi, con filtri opzionali."""
    q = db.query(Space).filter(Space.active == True)
    if name:
        q = q.filter(Space.name.ilike(f"%{name}%"))
    if location:
        q = q.filter(Space.location == location)
    spaces = q.all()
    if equipment:
        eq_lower = equipment.lower()
        spaces = [
            s for s in spaces
            if any(eq_lower in part.strip().lower() for part in (s.equipment or "").split(","))
        ]
    return [_serialize(s) for s in spaces]


@router.get("/equipment")
def list_all_equipment(db: Session = Depends(get_db)):
    """Restituisce tutte le dotazioni uniche presenti nel database (da tutti gli spazi)."""
    spaces = db.query(Space).all()
    equipment_set = set()
    for s in spaces:
        if s.equipment:
            for part in s.equipment.split(","):
                item = part.strip()
                if item:
                    equipment_set.add(item)
    return sorted(equipment_set, key=lambda x: x.lower())


@router.get("/all-admin")
def list_all_spaces(db: Session = Depends(get_db)):
    """Admin: restituisce tutti gli spazi (attivi e non)."""
    return [_serialize(s) for s in db.query(Space).all()]


@router.post("")
def create_space(data: SpaceCreate, db: Session = Depends(get_db)):
    if data.capacity < 1 or data.capacity > 40:
        raise HTTPException(status_code=400, detail="Capienza deve essere tra 1 e 40.")
    space = Space(**data.model_dump())
    db.add(space)
    db.commit()
    db.refresh(space)
    return _serialize(space)


@router.put("/{space_id}")
def update_space(space_id: int, data: SpaceUpdate, db: Session = Depends(get_db)):
    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato.")
    space.name      = data.name
    space.capacity  = data.capacity
    space.equipment = data.equipment
    space.location  = data.location
    db.commit()
    return _serialize(space)


@router.patch("/{space_id}/toggle")
def toggle_space(space_id: int, db: Session = Depends(get_db)):
    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato.")
    space.active = not space.active
    db.commit()
    stato = "attivato" if space.active else "messo in manutenzione"
    return {"message": f"Spazio {stato}."}


@router.delete("/{space_id}")
def delete_space(space_id: int, db: Session = Depends(get_db)):
    from database import Booking, Invitation, Notification
    from datetime import datetime

    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Spazio non trovato.")

    # Cancella prenotazioni future e notifica gli utenti
    future_bookings = db.query(Booking).filter(
        Booking.space_id == space_id,
        Booking.start_time > datetime.utcnow()
    ).all()
    for b in future_bookings:
        for inv in b.invitations:
            db.add(Notification(
                user=inv.username,
                message=f"Lo spazio '{space.name}' è stato eliminato: la prenotazione #{b.id} è annullata."
            ))
        db.add(Notification(
            user=b.user,
            message=f"Lo spazio '{space.name}' è stato eliminato: la tua prenotazione #{b.id} è annullata."
        ))
        db.delete(b)

    db.delete(space)
    db.commit()
    return {"message": f"Spazio '{space.name}' eliminato."}


# ─── Helper ─────────────────────────────────────────────────────────────────

def _serialize(s: Space) -> dict:
    return {
        "id":        s.id,
        "name":      s.name,
        "capacity":  s.capacity,
        "equipment": s.equipment or "",
        "location":  s.location or "Regesta",
        "active":    s.active,
    }
