from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class HCP(Base):
    """Healthcare Professional (doctor) that reps interact with."""
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    """A single logged interaction between a rep and an HCP."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String, default="Meeting")  # Meeting, Call, Email
    interaction_date = Column(DateTime, default=datetime.utcnow)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)
    samples_distributed = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)  # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    followup_actions = Column(Text, nullable=True)

    # AI-detected fields
    ae_flagged = Column(Boolean, default=False)
    ae_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")