"""
routers/auth.py — Autenticazione, profilo utente, amici, notifiche, messaggi.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db, User, Friend, FriendRequest, Notification, Message, Booking, Space

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─── Schemi Pydantic ────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class UpdateDisplayNameRequest(BaseModel):
    username: str
    display_name: str

class FriendRequestCreate(BaseModel):
    from_user: str
    target_user: str

class FriendRequestRespond(BaseModel):
    user: str
    requester: str
    status: str   # "accepted" | "declined"

class RemoveFriendRequest(BaseModel):
    user: str
    target: str

class SendMessageRequest(BaseModel):
    from_: str = None
    to: str = None
    content: str
    # accetta anche le chiavi dal frontend
    class Config:
        populate_by_name = True

class MarkReadRequest(BaseModel):
    user: str
    with_user: str

class NotifDeleteRequest(BaseModel):
    ids: List[int]

class NotifMarkReadRequest(BaseModel):
    user: str
    ids: List[int]


# ─── Helpers ────────────────────────────────────────────────────────────────

def _are_friends(db: Session, a: str, b: str) -> bool:
    return db.query(Friend).filter(
        ((Friend.user_a == a) & (Friend.user_b == b)) |
        ((Friend.user_a == b) & (Friend.user_b == a))
    ).first() is not None


def _notify(db: Session, user: str, message: str):
    notif = Notification(user=user, message=message)
    db.add(notif)
    db.commit()


# ─── Auth endpoints ─────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="Credenziali non valide.")
    return {
        "username":     user.username,
        "role":         user.role,
        "display_name": user.display_name or user.username,
    }


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Blocca username che contengono "admin" (riservato agli amministratori)
    if "admin" in req.username.lower():
        raise HTTPException(
            status_code=403,
            detail="Non puoi registrarti con un username che contiene 'admin'. Contatta un amministratore."
        )
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username già in uso.")
    user = User(
        username=req.username,
        password=req.password,
        role="user",
        display_name=req.display_name or req.username,
    )
    db.add(user)
    db.commit()
    return {"message": "Account creato con successo!"}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    user.password = req.new_password
    db.commit()
    return {"message": "Password aggiornata con successo."}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password != req.old_password:
        raise HTTPException(status_code=401, detail="Password attuale errata.")
    user.password = req.new_password
    db.commit()
    return {"message": "Password aggiornata con successo."}


@router.post("/update-displayname")
def update_display_name(req: UpdateDisplayNameRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    user.display_name = req.display_name
    db.commit()
    return {"message": "Nome visualizzato aggiornato."}


# ─── Profilo ────────────────────────────────────────────────────────────────

@router.get("/profile")
def get_profile(user: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == user).first()
    if not u:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    friends = db.query(Friend).filter(
        (Friend.user_a == user) | (Friend.user_b == user)
    ).all()
    friend_names = [
        f.user_b if f.user_a == user else f.user_a
        for f in friends
    ]

    incoming = db.query(FriendRequest).filter(
        FriendRequest.to_user == user,
        FriendRequest.status == "pending"
    ).all()

    return {
        "user": {
            "username":     u.username,
            "display_name": u.display_name or u.username,
            "role":         u.role,
            "friends":      friend_names,
        },
        "incoming_requests": [
            {"from_user": r.from_user} for r in incoming
        ],
    }


# ─── Amicizie ────────────────────────────────────────────────────────────────

@router.post("/friend-requests")
def send_friend_request(req: FriendRequestCreate, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.username == req.target_user).first():
        raise HTTPException(status_code=404, detail="Utente target non trovato.")
    if _are_friends(db, req.from_user, req.target_user):
        raise HTTPException(status_code=400, detail="Siete già amici.")
    existing = db.query(FriendRequest).filter(
        FriendRequest.from_user == req.from_user,
        FriendRequest.to_user == req.target_user,
        FriendRequest.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Richiesta già inviata.")
    fr = FriendRequest(from_user=req.from_user, to_user=req.target_user)
    db.add(fr)
    db.commit()
    _notify(db, req.target_user, f"{req.from_user} ti ha inviato una richiesta di amicizia.")
    return {"message": "Richiesta di amicizia inviata."}


@router.post("/friend-requests/respond")
def respond_friend_request(req: FriendRequestRespond, db: Session = Depends(get_db)):
    fr = db.query(FriendRequest).filter(
        FriendRequest.from_user == req.requester,
        FriendRequest.to_user == req.user,
        FriendRequest.status == "pending"
    ).first()
    if not fr:
        raise HTTPException(status_code=404, detail="Richiesta non trovata.")
    fr.status = req.status
    if req.status == "accepted":
        db.add(Friend(user_a=req.user, user_b=req.requester))
        _notify(db, req.requester, f"{req.user} ha accettato la tua richiesta di amicizia.")
    db.commit()
    return {"message": f"Richiesta {req.status}."}


@router.post("/remove-friend")
def remove_friend(req: RemoveFriendRequest, db: Session = Depends(get_db)):
    friend = db.query(Friend).filter(
        ((Friend.user_a == req.user) & (Friend.user_b == req.target)) |
        ((Friend.user_a == req.target) & (Friend.user_b == req.user))
    ).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Amicizia non trovata.")
    db.delete(friend)
    db.commit()
    _notify(db, req.target, f"La tua amicizia con {req.user} è stata rimossa.")
    return {"message": "Amico rimosso."}


# ─── Notifiche ───────────────────────────────────────────────────────────────

@router.get("/notifications")
def get_notifications(user: str, db: Session = Depends(get_db)):
    items = db.query(Notification).filter(
        Notification.user == user
    ).order_by(Notification.created.desc()).limit(50).all()
    return [
        {"id": n.id, "message": n.message, "read": n.read, "created": str(n.created)}
        for n in items
    ]


@router.post("/notifications/mark-read")
def mark_notifications_read(req: NotifMarkReadRequest, db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.id.in_(req.ids),
        Notification.user == req.user
    ).update({"read": True}, synchronize_session=False)
    db.commit()
    return {"message": "Notifiche segnate come lette."}


@router.delete("/notifications")
def delete_notifications(req: NotifDeleteRequest, db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.id.in_(req.ids)).delete(
        synchronize_session=False
    )
    db.commit()
    return {"message": "Notifiche eliminate."}


# ─── Inviti prenotazione ─────────────────────────────────────────────────────

@router.get("/invitations")
def get_invitations(user: str, db: Session = Depends(get_db)):
    from database import Invitation
    items = db.query(Invitation).filter(
        Invitation.username == user,
        Invitation.status == "pending"
    ).all()
    result = []
    for inv in items:
        b = inv.booking
        result.append({
            "invitation_id": inv.id,
            "booking_id":    b.id,
            "space_name":    b.space.name if b.space else "?",
            "host":          b.user,
            "start_time":    str(b.start_time),
            "end_time":      str(b.end_time),
        })
    return result


@router.post("/invitations/respond")
def respond_invitation(data: dict, db: Session = Depends(get_db)):
    from database import Invitation
    inv_id = data.get("invitation_id")
    status = data.get("status")   # "accepted" | "declined"
    inv = db.query(Invitation).filter(Invitation.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invito non trovato.")
    inv.status = status
    db.commit()
    return {"message": f"Invito {status}."}


# ─── Messaggi / Chat ─────────────────────────────────────────────────────────

@router.get("/conversations")
def get_conversations(user: str, db: Session = Depends(get_db)):
    """Restituisce la lista di utenti con cui l'utente ha avuto conversazioni."""
    sent = db.query(Message.to_user).filter(Message.from_user == user).distinct().all()
    recv = db.query(Message.from_user).filter(Message.to_user == user).distinct().all()
    peers = set([r[0] for r in sent] + [r[0] for r in recv])

    result = []
    for peer in peers:
        last_msg = db.query(Message).filter(
            ((Message.from_user == user) & (Message.to_user == peer)) |
            ((Message.from_user == peer) & (Message.to_user == user))
        ).order_by(Message.timestamp.desc()).first()

        unread = db.query(Message).filter(
            Message.from_user == peer,
            Message.to_user == user,
            Message.read == False
        ).count()

        result.append({
            "user":   peer,
            "last":   last_msg.content[:40] if last_msg else "",
            "unread": unread,
        })
    return result


@router.get("/messages")
def get_messages(user: str, with_user: str, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(
        ((Message.from_user == user) & (Message.to_user == with_user)) |
        ((Message.from_user == with_user) & (Message.to_user == user))
    ).order_by(Message.timestamp.asc()).all()
    return [
        {
            "id":        m.id,
            "from":      m.from_user,
            "content":   m.content,
            "timestamp": m.timestamp.isoformat(),
            "read":      m.read,
        }
        for m in msgs
    ]


@router.post("/send-message")
def send_message(data: dict, db: Session = Depends(get_db)):
    from_user = data.get("from")
    to_user   = data.get("to")
    content   = data.get("content", "").strip()
    if not from_user or not to_user or not content:
        raise HTTPException(status_code=400, detail="Campi mancanti.")
    msg = Message(from_user=from_user, to_user=to_user, content=content)
    db.add(msg)
    # Notifica il destinatario del nuovo messaggio
    preview = content if len(content) <= 50 else content[:50] + "…"
    db.add(Notification(
        user=to_user,
        message=f"💬 MESSAGGIO | {from_user} ti ha scritto: \"{preview}\""
    ))
    db.commit()
    return {"message": "Messaggio inviato."}


@router.put("/messages/read")
def mark_messages_read(data: dict, db: Session = Depends(get_db)):
    user      = data.get("user")
    with_user = data.get("with_user")
    db.query(Message).filter(
        Message.from_user == with_user,
        Message.to_user == user,
        Message.read == False
    ).update({"read": True}, synchronize_session=False)
    db.commit()
    return {"message": "Messaggi segnati come letti."}


@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    """Restituisce la lista di tutti gli utenti (per la chat: scrivere a chiunque)."""
    users = db.query(User).all()
    return [
        {"username": u.username, "display_name": u.display_name or u.username, "role": u.role}
        for u in users
    ]
