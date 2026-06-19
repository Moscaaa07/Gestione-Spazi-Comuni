"""
sync_seed.py — Mantiene seed.py sincronizzato con gli account del database.
Viene chiamato automaticamente ad ogni registrazione o eliminazione account.
"""
import os
import re

SEED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed.py')


def _read_seed() -> str:
    with open(SEED_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def _write_seed(content: str):
    with open(SEED_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


def add_user_to_seed(username: str, password: str, display_name: str, role: str = "user"):
    """Aggiunge un nuovo utente alla lista corretta in seed.py (users o admins)."""
    try:
        content = _read_seed()

        if f'"{username}"' in content:
            return

        entry = f'    ("{username}", "{password}", "{display_name}"),\n'
        list_name = "admins" if role == "admin" else "users"

        pattern = rf'({list_name}\s*=\s*\[)([ \t]*\n)'

        def replacer(m):
            return m.group(1) + m.group(2) + entry

        new_content = re.sub(pattern, replacer, content, count=1)
        _write_seed(new_content)
    except Exception:
        pass


def remove_user_from_seed(username: str):
    """Rimuove un utente da seed.py (sia dalla lista users che admins)."""
    try:
        content = _read_seed()

        escaped = re.escape(username)
        content = re.sub(r'[ \t]*\("' + escaped + r'"[^\n]*\),?\n', '', content)

        content = re.sub(r'\n{3,}', '\n\n', content)

        _write_seed(content)
    except Exception:
        pass
