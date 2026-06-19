"""
database.py — Configurazione PostgreSQL + SQLAlchemy e definizione modelli.
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Sostituito SQLite con la stringa di connessione a Supabase
DATABASE_URL = "postgresql://postgres.bjoawolzjfukjlfsnjyi:9NXfHqBaR5OpsEnD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

# Per PostgreSQL rimuoviamo connect_args={"check_same_thread": False}
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Modelli ────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String, unique=True, index=True, nullable=False)
    password     = Column(String, nullable=False)
    role         = Column(String, default="user")          # "user" | "admin"
    display_name = Column(String, nullable=True)

    bookings      = relationship("Booking",      back_populates="owner",    foreign_keys="Booking.user")
    notifications = relationship("Notification", back_populates="owner")
    sent_messages = relationship("Message",      back_populates="sender",   foreign_keys="Message.from_user")
    recv_messages = relationship("Message",      back_populates="receiver", foreign_keys="Message.to_user")


class Friend(Base):
    __tablename__ = "friends"

    id      = Column(Integer, primary_key=True)
    user_a  = Column(String, ForeignKey("users.username"), nullable=False)
    user_b  = Column(String, ForeignKey("users.username"), nullable=False)


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id        = Column(Integer, primary_key=True)
    from_user = Column(String, ForeignKey("users.username"), nullable=False)
    to_user   = Column(String, ForeignKey("users.username"), nullable=False)
    status    = Column(String, default="pending")   # "pending" | "accepted" | "declined"


class Space(Base):
    __tablename__ = "spaces"

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String, nullable=False)
    capacity  = Column(Integer, nullable=False)
    equipment = Column(String, default="")
    location  = Column(String, default="Regesta")
    active    = Column(Boolean, default=True)

    bookings  = relationship("Booking", back_populates="space")


class Booking(Base):
    __tablename__ = "bookings"

    id         = Column(Integer, primary_key=True, index=True)
    space_id   = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    user       = Column(String, ForeignKey("users.username"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time   = Column(DateTime, nullable=False)

    space       = relationship("Space",      back_populates="bookings")
    owner       = relationship("User",       back_populates="bookings", foreign_keys=[user])
    invitations = relationship("Invitation", back_populates="booking", cascade="all, delete-orphan")


class Invitation(Base):
    __tablename__ = "invitations"

    id         = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    username   = Column(String,  ForeignKey("users.username"), nullable=False)
    status     = Column(String, default="pending")   # "pending" | "accepted" | "declined"

    booking    = relationship("Booking", back_populates="invitations")


class Notification(Base):
    __tablename__ = "notifications"

    id        = Column(Integer, primary_key=True)
    user      = Column(String, ForeignKey("users.username"), nullable=False)
    message   = Column(Text, nullable=False)
    read      = Column(Boolean, default=False)
    created   = Column(DateTime, default=datetime.utcnow)

    owner     = relationship("User", back_populates="notifications")


class Message(Base):
    __tablename__ = "messages"

    id        = Column(Integer, primary_key=True)
    from_user = Column(String, ForeignKey("users.username"), nullable=False)
    to_user   = Column(String, ForeignKey("users.username"), nullable=False)
    content   = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    read      = Column(Boolean, default=False)

    sender    = relationship("User", back_populates="sent_messages",  foreign_keys=[from_user])
    receiver  = relationship("User", back_populates="recv_messages",  foreign_keys=[to_user])


class DeletedAccount(Base):
    __tablename__ = "deleted_accounts"

    id         = Column(Integer, primary_key=True)
    username   = Column(String, nullable=False)
    deleted_at = Column(DateTime, default=datetime.utcnow)


# ─── Helper ─────────────────────────────────────────────────────────────────

def get_db():
    """Dependency FastAPI: fornisce una sessione DB e la chiude al termine."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
