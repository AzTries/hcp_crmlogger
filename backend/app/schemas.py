from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str = "Meeting"
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    """All fields optional - only send what you want to change."""
    interaction_type: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    interaction_date: datetime
    ae_flagged: bool
    ae_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageItem]