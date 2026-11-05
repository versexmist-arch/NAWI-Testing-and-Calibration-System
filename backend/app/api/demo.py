from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.demo_data_service import reset_demo_data, seed_demo_data

router = APIRouter(prefix="/demo", tags=["Demonstration Data"])


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    return reset_demo_data(db)


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
    return seed_demo_data(db)

