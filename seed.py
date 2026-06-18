"""
seed.py — Popola il database da zero (safe: non duplica dati esistenti).
Esegui con:  python seed.py
"""
from database import create_tables, SessionLocal, User, Space

create_tables()
db = SessionLocal()

# ─── Admin ──────────────────────────────────────────────────────────────────
for email, pwd, nome in [
    ("mosca@admin.com",  "nimdA", "Mosca Admin"),
    ("andrea@admin.com", "nimdA", "Andrea Admin"),
]:
    if not db.query(User).filter(User.username == email).first():
        db.add(User(username=email, password=pwd, role="admin", display_name=nome))

# ─── Utenti ─────────────────────────────────────────────────────────────────
for email, pwd, nome in [
    ("chiara@scuola.it",  "chiara2024",  "Chiara Martini"),
    ("davide@scuola.it",  "davide2024",  "Davide Romano"),
    ("elena@scuola.it",   "elena2024",   "Elena Conti"),
    ("marco@scuola.it",   "marco2024",   "Marco Esposito"),
]:
    if not db.query(User).filter(User.username == email).first():
        db.add(User(username=email, password=pwd, role="user", display_name=nome))

# ─── Stanze ─────────────────────────────────────────────────────────────────
stanze = [
    # Regesta
    ("Sala Executive",          12, "Proiettore 4K, Videoconferenza HD, Lavagna Smart",     "Regesta"),
    ("Sala Brainstorming",      10, "Lavagne Multiple, Post-it, Wi-Fi, Musica Ambient",      "Regesta"),
    ("Sala Formazione Pro",     25, "Proiettore, PC per docente, Wi-Fi, Microfono",          "Regesta"),
    ("Auditorium Regesta",      80, "Palco, Impianto Audio, Proiettore, Microfono Cordless", "Regesta"),
    ("Open Space Alpha",        20, "Schermi Multipli, Wi-Fi, Prese USB, Stampante",         "Regesta"),
    ("Sala Riunioni Piccola",    6, 'TV 55", Videoconferenza, Lavagna',                      "Regesta"),
    # Scuola
    ("Laboratorio Digitale",    20, "PC, Stampante 3D, Arduino Kit, Proiettore",             "Scuola"),
    ("Aula Studio A",           18, "Wi-Fi, Prese Elettriche, Luce Naturale, Silenzio",      "Scuola"),
    ("Aula Studio B",           18, "Wi-Fi, Prese Elettriche, Luce Naturale",                "Scuola"),
    ("Laboratorio Lingue",      24, "PC, Cuffie, Microfono, Proiettore, Lavagna Digitale",   "Scuola"),
    ("Palestra Piccola",        30, "Attrezzi, Tappeti, Specchi, Impianto Audio",             "Scuola"),
    ("Aula Arte e Design",      16, "Tavoli Tecnici, Lavandino, Cavalletti, Proiettore",      "Scuola"),
    # Biblioteca
    ("Sala Consultazione",      20, "Wi-Fi, Prese, Scaffali di Riferimento, Silenzio",       "Biblioteca"),
    ("Sala Ricerca Digitale",   12, "PC, Scanner, Stampante, Wi-Fi Alta Velocità",            "Biblioteca"),
    ("Sala Seminari",           30, "Proiettore, Microfono, Lavagna, Wi-Fi",                 "Biblioteca"),
    ("Angolo Studio Privato",    4, "Wi-Fi, Presa, Luce Regolabile, Privacy",                "Biblioteca"),
    # Altro
    ("Terrazzo Panoramico",     40, "Wi-Fi Esterno, Gazebo, Prese Esterne, Vista Città",     "Altro"),
    ("Sala Polivalente Sud",    50, "Proiettore, Impianto Audio, Cucina Attrezzata, Wi-Fi",  "Altro"),
    ("Sala Mostre Temporanee",  60, "Illuminazione Professionale, Wi-Fi, Pannelli Mobili",   "Altro"),
    ("Spazio Maker",            15, "Stampante 3D, Laser Cutter, Arduino, Wi-Fi",             "Altro"),
]
for nome, cap, dotaz, sede in stanze:
    if not db.query(Space).filter(Space.name == nome).first():
        db.add(Space(name=nome, capacity=cap, equipment=dotaz, location=sede))

db.commit()
db.close()
print("✅ Seed completato.")
print()
print("  ADMIN:")
print("    mosca@admin.com   /  nimdA")
print("    andrea@admin.com  /  nimdA")
print()
print("  UTENTI:")
print("    chiara@scuola.it  /  chiara2024   (Chiara Martini)")
print("    davide@scuola.it  /  davide2024   (Davide Romano)")
print("    elena@scuola.it   /  elena2024    (Elena Conti)")
print("    marco@scuola.it   /  marco2024    (Marco Esposito)")
print()
print("  STANZE: 20 (Regesta:6 | Scuola:6 | Biblioteca:4 | Altro:4)")
