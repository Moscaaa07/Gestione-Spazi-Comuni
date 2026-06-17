from fastapi import APIRouter, HTTPException
from models import UserLogin, PasswordReset, PasswordChange, FriendRequest, FriendRequestResponse
from config import load_db, save_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
def login(user_data: UserLogin):
    data = load_db()
    user = next((u for u in data["users"] if u["username"] == user_data.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato. Registrati prima!")
    
    if user.get("password") != user_data.password:
        raise HTTPException(status_code=401, detail="Password errata.")
    return user

@router.post("/register")
def register_user(user_data: UserLogin):
    data = load_db()
    existing_user = next((u for u in data["users"] if u["username"] == user_data.username), None)
    if existing_user:
        raise HTTPException(status_code=400, detail="Questo indirizzo email è già registrato.")
    
    display_name = user_data.username.split("@")[0].capitalize()
    role = "admin" if "admin" in user_data.username.lower() else "user"
    
    new_user = {
        "username": user_data.username,
        "role": role,
        "password": user_data.password,
        "display_name": display_name
    }
    data["users"].append(new_user)
    save_db(data)
    return {"message": "Utente registrato con successo", "user": new_user}

@router.post("/reset-password")
def reset_password(reset_data: PasswordReset):
    data = load_db()
    user = next((u for u in data["users"] if u["username"] == reset_data.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    
    user["password"] = reset_data.new_password
    save_db(data)
    return {"message": "Password modificata con successo!"}

@router.post("/change-password")
def change_password(change_data: PasswordChange):
    data = load_db()
    user = next((u for u in data["users"] if u["username"] == change_data.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    if user.get("password") != change_data.old_password:
        raise HTTPException(status_code=401, detail="Password precedente non corretta.")

    user["password"] = change_data.new_password
    save_db(data)
    return {"message": "Password aggiornata con successo."}

@router.get("/profile")
def get_profile(user: str):
    data = load_db()
    user_data = next((u for u in data["users"] if u["username"] == user), None)
    if not user_data:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    if "friends" not in user_data:
        user_data["friends"] = []

    if "friend_requests" not in data:
        data["friend_requests"] = []

    profile_user = {
        "username": user_data["username"],
        "display_name": user_data.get("display_name", user_data["username"]),
        "role": user_data.get("role", "user"),
        "friends": user_data.get("friends", [])
    }

    incoming_requests = [r for r in data["friend_requests"] if r["target_user"] == user and r["status"] == "pending"]
    return {"user": profile_user, "incoming_requests": incoming_requests}

@router.get("/friend-requests")
def get_friend_requests(user: str):
    data = load_db()
    if "friend_requests" not in data:
        data["friend_requests"] = []
    return [r for r in data["friend_requests"] if r["target_user"] == user and r["status"] == "pending"]

@router.post("/friend-requests")
def send_friend_request(request: FriendRequest):
    data = load_db()
    if request.from_user == request.target_user:
        raise HTTPException(status_code=400, detail="Non puoi chiedere amicizia a te stesso.")

    source = next((u for u in data["users"] if u["username"] == request.from_user), None)
    target = next((u for u in data["users"] if u["username"] == request.target_user), None)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    source.setdefault("friends", [])
    target.setdefault("friends", [])
    if request.target_user in source["friends"]:
        raise HTTPException(status_code=400, detail="Sei già amico di questo utente.")

    if "friend_requests" not in data:
        data["friend_requests"] = []

    existing = next((r for r in data["friend_requests"] if r["from_user"] == request.from_user and r["target_user"] == request.target_user and r["status"] == "pending"), None)
    if existing:
        raise HTTPException(status_code=400, detail="Hai già inviato una richiesta di amicizia a questo utente.")

    data["friend_requests"].append({
        "from_user": request.from_user,
        "target_user": request.target_user,
        "status": "pending"
    })

    if "notifications" not in data:
        data["notifications"] = []
    data["notifications"].append({
        "user": request.target_user,
        "message": f"Ricevuta richiesta di amicizia da {request.from_user}.",
        "read": False
    })

    save_db(data)
    return {"message": "Richiesta di amicizia inviata."}

@router.post("/friend-requests/respond")
def respond_friend_request(response: FriendRequestResponse):
    data = load_db()
    if response.status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Stato risposta non valido.")

    if "friend_requests" not in data:
        data["friend_requests"] = []

    request = next((r for r in data["friend_requests"] if r["from_user"] == response.requester and r["target_user"] == response.user and r["status"] == "pending"), None)
    if not request:
        raise HTTPException(status_code=404, detail="Richiesta di amicizia non trovata.")

    request["status"] = response.status

    from_user = next((u for u in data["users"] if u["username"] == response.requester), None)
    target_user = next((u for u in data["users"] if u["username"] == response.user), None)
    if not from_user or not target_user:
        raise HTTPException(status_code=404, detail="Utenti non trovati.")

    if response.status == "accepted":
        from_user.setdefault("friends", [])
        target_user.setdefault("friends", [])
        if target_user["username"] not in from_user["friends"]:
            from_user["friends"].append(target_user["username"])
        if from_user["username"] not in target_user["friends"]:
            target_user["friends"].append(from_user["username"])

        message = f"{response.user} ha accettato la tua richiesta di amicizia."
    else:
        message = f"{response.user} ha rifiutato la tua richiesta di amicizia."

    if "notifications" not in data:
        data["notifications"] = []
    data["notifications"].append({
        "user": response.requester,
        "message": message,
        "read": False
    })

    save_db(data)
    return {"message": f"Richiesta di amicizia {response.status}."}


@router.post("/update-displayname")
def update_display_name(payload: dict):
    username = payload.get('username')
    new_name = payload.get('display_name')
    if not username or not new_name:
        raise HTTPException(status_code=400, detail="Parametri mancanti.")
    data = load_db()
    user = next((u for u in data['users'] if u['username'] == username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    user['display_name'] = new_name
    save_db(data)
    return {"message": "Nome visualizzato aggiornato con successo."}

@router.get("/notifications")
def get_notifications(user: str):
    data = load_db()
    if "notifications" not in data:
        return []

    next_id = max((n.get("id", 0) for n in data.get("notifications", [])), default=0) + 1
    updated = False
    for n in data.get("notifications", []):
        if "id" not in n:
            n["id"] = next_id
            next_id += 1
            updated = True
        if "read" not in n:
            n["read"] = False
            updated = True
    if updated:
        save_db(data)

    return [n for n in data["notifications"] if n["user"] == user]

@router.delete("/notifications")
def clear_notifications(user: str):
    data = load_db()
    if "notifications" not in data:
        return {"message": "Nessuna notifica da cancellare."}
    
    data["notifications"] = [n for n in data["notifications"] if n["user"] != user]
    save_db(data)
    return {"message": "Notifiche cancellate con successo."}

@router.put("/notifications/read")
def mark_notifications_read(user: str):
    data = load_db()
    if "notifications" not in data:
        return {"message": "Nessuna notifica da segnare come lette."}

    for n in data["notifications"]:
        if n["user"] == user:
            n["read"] = True
    save_db(data)
    return {"message": "Notifiche segnate come lette."}

@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, user: str):
    data = load_db()
    if "notifications" not in data:
        raise HTTPException(status_code=404, detail="Notifica non trovata.")

    original_len = len(data["notifications"])
    data["notifications"] = [n for n in data["notifications"] if not (n.get("id") == notification_id and n["user"] == user)]
    if len(data["notifications"]) == original_len:
        raise HTTPException(status_code=404, detail="Notifica non trovata.")
    save_db(data)
    return {"message": "Notifica eliminata con successo."}


# --- Simple user-to-user chat endpoints ---
@router.get("/conversations")
def get_conversations(user: str):
    data = load_db()
    users = [u["username"] for u in data.get("users", []) if u.get("username") != user]
    if "messages" not in data:
        data["messages"] = []

    # prepare default stats for every other user
    stats = {u: {"last": None, "timestamp": None, "unread": 0} for u in users}

    for m in data["messages"]:
        frm = m.get("from")
        to = m.get("to")
        ts = m.get("timestamp")
        content = m.get("content")
        if frm == user and to in stats:
            if stats[to]["timestamp"] is None or (ts and ts > stats[to]["timestamp"]):
                stats[to]["last"] = content
                stats[to]["timestamp"] = ts
        elif to == user and frm in stats:
            if stats[frm]["timestamp"] is None or (ts and ts > stats[frm]["timestamp"]):
                stats[frm]["last"] = content
                stats[frm]["timestamp"] = ts
            if not m.get("read", False):
                stats[frm]["unread"] += 1

    result = []
    for p in users:
        result.append({"user": p, "last": stats[p]["last"], "timestamp": stats[p]["timestamp"], "unread": stats[p]["unread"]})
    result.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return result


@router.get("/messages")
def get_messages(user: str, with_user: str):
    data = load_db()
    if "messages" not in data:
        data["messages"] = []
    conv = [m for m in data["messages"] if (m.get("from") == user and m.get("to") == with_user) or (m.get("from") == with_user and m.get("to") == user)]
    conv.sort(key=lambda x: x.get("timestamp"))
    return conv


@router.post("/send-message")
def send_message(payload: dict):
    frm = payload.get("from")
    to = payload.get("to")
    content = payload.get("content")
    if not frm or not to or content is None:
        raise HTTPException(status_code=400, detail="Parametri messaggio mancanti.")
    data = load_db()
    if "messages" not in data:
        data["messages"] = []
    new_id = max([m.get("id", 0) for m in data["messages"]], default=0) + 1
    from datetime import datetime
    msg = {
        "id": new_id,
        "from": frm,
        "to": to,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False
    }
    data["messages"].append(msg)

    # add notification to recipient
    if "notifications" not in data:
        data["notifications"] = []
    data["notifications"].append({
        "user": to,
        "message": f"Nuovo messaggio da {frm}: {content[:80]}",
        "read": False
    })

    save_db(data)
    return {"message": "Messaggio inviato.", "msg": msg}


@router.put("/messages/read")
def mark_messages_read(payload: dict):
    user = payload.get("user")
    with_user = payload.get("with_user")
    if not user or not with_user:
        raise HTTPException(status_code=400, detail="Parametri mancanti.")
    data = load_db()
    if "messages" not in data:
        data["messages"] = []
    updated = False
    for m in data["messages"]:
        if m.get("to") == user and m.get("from") == with_user and not m.get("read", False):
            m["read"] = True
            updated = True
    if updated:
        save_db(data)
    return {"message": "Messaggi marcati come letti."}