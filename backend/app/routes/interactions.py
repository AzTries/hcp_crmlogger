from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.get("/interactions")
def list_interactions(db: Session = Depends(get_db)):
    interactions = (
        db.query(models.Interaction)
        .order_by(models.Interaction.id.desc())
        .limit(8)
        .all()
    )
    return interactions


@router.get("/interactions/{interaction_id}")
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.post("/interactions", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    # Confirm the HCP exists before logging against it
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    interaction = models.Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.put("/interactions/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    updates = payload.model_dump(exclude_unset=True)  # only fields actually sent
    for field, value in updates.items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/interactions/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    db.delete(interaction)
    db.commit()
    return {"detail": f"Interaction {interaction_id} deleted"}