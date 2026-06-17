# File ordinato: regesta/models.py
from pydantic import BaseModel, Field
from typing import List

class UserLogin(BaseModel):
    username: str
    password: str

class SpaceCreate(BaseModel):
    name: str
    capacity: int = Field(..., ge=1, le=40)  # Limita da 1 a 40
    equipment: str
    location: str

class BookingCreate(BaseModel):
    space_id: int
    user: str
    start_time: str
    duration_hours: int
    invited_users: List[str] = []  # Lista di utenti invitati alla prenotazione

class PasswordReset(BaseModel):
    username: str
    new_password: str

class PasswordChange(BaseModel):
    username: str
    old_password: str
    new_password: str

class FriendRequest(BaseModel):
    from_user: str
    target_user: str

class FriendRequestResponse(BaseModel):
    user: str
    requester: str
    status: str
