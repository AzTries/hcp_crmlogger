from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.get("/hcps", response_model=list[schemas.HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(models.HCP).order_by(models.HCP.name).all()


@router.post("/hcps", response_model=schemas.HCPOut)
def create_hcp(payload: schemas.HCPCreate, db: Session = Depends(get_db)):
    existing = db.query(models.HCP).filter(models.HCP.name.ilike(payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="HCP with this name already exists")

    hcp = models.HCP(**payload.model_dump())
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp