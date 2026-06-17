import os
import json

DB_FILE = "database.json"

INITIAL_DATA = {
    "users": [
        {"username": "admin", "role": "admin", "password": "nimdA", "display_name": "Admin"},
        {"username": "studente1", "role": "user", "password": "password123", "display_name": "Studente1"},
        {"username": "studente2", "role": "user", "password": "password456", "display_name": "Studente2"}
    ],
    "spaces": [
        {"id": 1, "name": "Aula Studio A", "capacity": 10, "equipment": "Lavagna, Wi-Fi", "location": "Regesta", "active": True},
        {"id": 2, "name": "Sala Riunioni Alpha", "capacity": 6, "equipment": "Proiettore, Monitor", "location": "Biblioteca", "active": True}
    ],
    "bookings": [],
    "notifications": []
}

def next_notification_id(data):
    if "notifications" not in data or not data["notifications"]:
        return 1
    return max((n.get("id", 0) for n in data["notifications"]), default=0) + 1

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(INITIAL_DATA, f, indent=4)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)