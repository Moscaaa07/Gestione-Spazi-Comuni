# 🏫 Portale Gestione Spazi Comuni

A web application for booking and managing shared spaces (meeting rooms, study halls, labs) within an organization. Built with **Python / FastAPI** on the backend and a **Bootstrap 5** single-page frontend.

---

## ✨ Features

### For all users
- 📅 **Space booking** — browse active spaces, check availability, and reserve a slot in a few clicks
- 👥 **Invitations** — invite colleagues to a booking; they can accept or decline from their notifications
- 🔔 **Real-time notifications** — in-app alerts for invites, messages, cancellations, and friend requests
- 💬 **Chat** — private one-to-one messaging and a shared group chat ("Everyone")
- 🤝 **Friends** — send, accept, or remove friend connections
- 👤 **Profile** — update display name, change password, view booking history, delete account
- 🎨 **Themes** — 7 visual themes (Light, Neon, Retro, Sky, Nature, Sun, Earth)

### For administrators
- 🏗️ **Space management** — create, edit, toggle maintenance mode, or delete spaces (with automatic cancellation notifications)
- 📋 **Global bookings register** — view and cancel any booking across all users
- 🛡️ **User management** — delete any user account; all admin actions are logged and other admins are notified

---

## 🛠️ Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Backend   | Python 3.10+, FastAPI, SQLAlchemy ORM           |
| Database  | PostgreSQL (hosted on Supabase — AWS eu-west-1) |
| Frontend  | HTML5, Bootstrap 5.3, Flatpickr, Bootstrap Icons |
| Server    | Uvicorn (ASGI)                                  |

---

## 📁 Project Structure

```
regesta/
├── main.py              # FastAPI entry point
├── database.py          # SQLAlchemy models + DB connection
├── seed.py              # Initial database seeding script
├── sync_seed.py         # User sync helper
├── requirements.txt
├── routers/
│   ├── auth.py          # Auth, profile, friends, notifications, chat
│   ├── spaces.py        # Spaces CRUD
│   └── bookings.py      # Bookings + invitations
└── static/
    └── index.html       # SPA frontend
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- pip
- Access to a PostgreSQL database (or a [Supabase](https://supabase.com) project)

### Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Seed the database with initial data
python seed.py

# 3. Start the development server
python -m uvicorn main:app --reload --port 8000
```

Open your browser at **http://localhost:8000**

---

## ⚙️ Configuration

The database connection string is defined in `database.py`:

```python
DATABASE_URL = "postgresql://user:password@host:port/dbname"
```

> **Production tip:** move `DATABASE_URL` to an environment variable and never commit credentials to the repository.

---

## 🗄️ Data Model

| Table              | Description                                      |
|--------------------|--------------------------------------------------|
| `users`            | Registered users (username, password, role, display name) |
| `spaces`           | Shared spaces (name, capacity, equipment, location, active) |
| `bookings`         | Reservations (space, user, start/end time)       |
| `invitations`      | Booking invitations (pending / accepted / declined) |
| `friends`          | Friend pairs                                     |
| `friend_requests`  | Pending friend requests                          |
| `notifications`    | In-app notifications                             |
| `messages`         | Private and group chat messages                  |
| `deleted_accounts` | Audit log of deleted accounts                    |

---

## 🔌 API Overview

### Authentication & Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | User login |
| `POST` | `/api/auth/register` | Register new account |
| `POST` | `/api/auth/request-reset-code` | Request password reset code |
| `POST` | `/api/auth/verify-reset-code` | Verify code and set new password |
| `POST` | `/api/auth/change-password` | Change password (authenticated) |
| `POST` | `/api/auth/update-displayname` | Update display name |
| `GET`  | `/api/auth/profile?user=X` | Get user profile and friends |
| `POST` | `/api/auth/delete-account` | Delete own account |
| `POST` | `/api/auth/admin-delete-user` | Delete any account (admin only) |

### Spaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/api/spaces` | List active spaces (with optional filters) |
| `GET`    | `/api/spaces/all-admin` | List all spaces including inactive (admin) |
| `GET`    | `/api/spaces/equipment` | List all unique equipment tags |
| `POST`   | `/api/spaces` | Create a new space (admin) |
| `PUT`    | `/api/spaces/{id}` | Update a space (admin) |
| `PATCH`  | `/api/spaces/{id}/toggle` | Toggle active / maintenance (admin) |
| `DELETE` | `/api/spaces/{id}` | Delete a space (admin) |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/api/bookings` | All bookings (admin) |
| `GET`    | `/api/bookings?user=X` | Bookings for user X |
| `GET`    | `/api/bookings?space_id=N` | Bookings for a space (timeline) |
| `POST`   | `/api/bookings` | Create a booking |
| `DELETE` | `/api/bookings/{id}?user=X` | Cancel a booking |

### Chat & Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/auth/conversations?user=X` | List private conversations |
| `GET`  | `/api/auth/messages?user=X&with_user=Y` | Messages between two users |
| `POST` | `/api/auth/send-message` | Send a private message |
| `PUT`  | `/api/auth/messages/read` | Mark messages as read |
| `GET`  | `/api/auth/group-messages` | Group chat messages |
| `POST` | `/api/auth/group-message` | Send a group message |
| `GET`  | `/api/auth/notifications?user=X` | Get notifications (latest 50) |
| `POST` | `/api/auth/notifications/mark-read` | Mark notifications as read |
| `DELETE` | `/api/auth/notifications` | Delete notifications |

---

## 🔐 Password Policy

All passwords (registration, change, reset) must meet the following requirements:

- Minimum **8 characters**
- At least one **uppercase letter**
- At least one **number**
- At least one **special character** (e.g. `!`, `@`, `#`, `$`, `%`)

---

## ⚠️ Security Notes

> This project is currently configured for **development / demo use**.

- Passwords are stored in **plain text** — in production, use a secure hashing algorithm (e.g. bcrypt, Argon2).
- There is no JWT or session token system; authentication state is managed client-side.
- The password reset code is returned directly in the API response (`demo_code` field) — in production it must be sent via email only.

---

## 👤 User Roles

| Role     | Description |
|----------|-------------|
| `user`   | Standard access — booking, chat, profile |
| `admin`  | Full access + space and user management |
| `system` | Internal virtual accounts (e.g. `__TUTTI__` for group chat) — cannot be deleted |

---

## 📄 License

This project is for internal organizational use. Please refer to your organization's policies for distribution and usage rights.
