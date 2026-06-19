"""
seed.py — Popola il database con dati iniziali.
Rieseguibile: non duplica i dati esistenti.
"""
from database import create_tables, SessionLocal, User, Space

create_tables()
db = SessionLocal()

# ─── Admin ufficiali ────────────────────────────────────────────────────────
admins = [
    ("mosca@admin.com",  "nimdA", "Mosca Admin"),
    ("andrea@admin.com", "nimdA", "Andrea Admin"),
]
for email, pwd, name in admins:
    if not db.query(User).filter(User.username == email).first():
        db.add(User(username=email, password=pwd, role="admin", display_name=name))

# ─── Utenti di esempio ──────────────────────────────────────────────────────
users = [
]
for email, pwd, name in users:
    if not db.query(User).filter(User.username == email).first():
        db.add(User(username=email, password=pwd, role="user", display_name=name))

# ─── Spazi ──────────────────────────────────────────────────────────────────
# (nome, capienza, dotazioni, sede)
spaces = [
    # Regesta
    ("Aula Magna",           40, "Proiettore, Microfono, Impianto Audio, Palco",   "Regesta"),
    ("Sala Riunioni A",      10, "TV, Lavagna, Videoconferenza",                   "Regesta"),
    ("Sala Riunioni B",       8, "Lavagna, TV",                                    "Regesta"),
    ("Sala Conferenze",      35, "Proiettore, Microfono, TV, Wi-Fi",               "Regesta"),
    ("Sala Relax",           12, "Divani, Macchina Caffè, Frigorifero",            "Regesta"),
    ("Sala Formazione",      20, "Proiettore, Lavagna, PC, Wi-Fi",                 "Regesta"),
    ("Open Space Creativo",  25, "Lavagne Multiple, PC, Stampante 3D",             "Regesta"),
    # Scuola
    ("Aula Informatica 1",   24, "PC, Proiettore, Wi-Fi, Stampante",               "Scuola"),
    ("Aula Informatica 2",   20, "PC, Proiettore, Wi-Fi",                          "Scuola"),
    ("Laboratorio Scienze",  25, "Microscopi, Proiettore, Cappe, Lavandino",       "Scuola"),
    ("Laboratorio Arte",     18, "Cavalletti, Lavandino, Armadietti",              "Scuola"),
    ("Palestra",             40, "Attrezzi Ginnici, Spogliatoi, Docce",            "Scuola"),
    ("Aula Musica",          20, "Pianoforte, Impianto Audio, Leggii",             "Scuola"),
    ("Aula Disegno Tecnico", 22, "Tavoli Tecnici, Proiettore, Lavagna",            "Scuola"),
    # Biblioteca
    ("Sala Studio Silenziosa", 15, "Wi-Fi, Prese Elettriche, Luce Naturale",       "Biblioteca"),
    ("Sala Studio Gruppo",     20, "Wi-Fi, Lavagna, Proiettore, Prese Elettriche", "Biblioteca"),
    ("Sala Lettura",           30, "Wi-Fi, Luce Naturale, Scaffali",               "Biblioteca"),
    ("Sala Multimediale",      12, "PC, Cuffie, Wi-Fi, Scanner",                   "Biblioteca"),
    # Altro
    ("Spazio Esterno A",     50, "Gazebo, Prese Esterne, Wi-Fi Esterno",           "Altro"),
    ("Spazio Esterno B",     30, "Gazebo, Barbecue",                               "Altro"),
    ("Sala Polivalente",     45, "Proiettore, Impianto Audio, Cucina, Wi-Fi",      "Altro"),
    ("Sala Mostre",          60, "Illuminazione Regolabile, Wi-Fi, Pareti Espositive", "Altro"),
]

for name, cap, equip, loc in spaces:
    if not db.query(Space).filter(Space.name == name).first():
        db.add(Space(name=name, capacity=cap, equipment=equip, location=loc))

db.commit()
db.close()
print("✅ Seed completato.")
print(f"   {len(admins)} admin | {len(users)} utenti | {len(spaces)} spazi inseriti/verificati")
print("   Admin: mosca@admin.com / andrea@admin.com  →  password: nimdA")
