from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from . import crud, models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ADService API",
    description="",
    version="1.0"
)

@app.post("/advertisement", response_model=schemas.Advertisement, status_code=201)
def create_advertisement(
    advertisement: schemas.AdvertisementCreate, 
    db: Session = Depends(get_db)
):
    return crud.create_advertisement(db=db, advertisement=advertisement)

@app.get("/advertisement/{advertisement_id}", response_model=schemas.Advertisement)
def read_advertisement(advertisement_id: int, db: Session = Depends(get_db)):
    db_advertisement = crud.get_advertisement(db, advertisement_id=advertisement_id)
    if db_advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return db_advertisement

@app.patch("/advertisement/{advertisement_id}", response_model=schemas.Advertisement)
def update_advertisement(
    advertisement_id: int, 
    advertisement_update: schemas.AdvertisementUpdate, 
    db: Session = Depends(get_db)
):
    db_advertisement = crud.update_advertisement(
        db, advertisement_id=advertisement_id, advertisement_update=advertisement_update
    )
    if db_advertisement is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return db_advertisement

@app.delete("/advertisement/{advertisement_id}")
def delete_advertisement(advertisement_id: int, db: Session = Depends(get_db)):
    success = crud.delete_advertisement(db, advertisement_id=advertisement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return {"message": "Advertisement deleted successfully"}

@app.get("/advertisement", response_model=list[schemas.Advertisement])
def search_advertisements(
    title: Optional[str] = Query(None, description="Поиск по заголовку"),
    description: Optional[str] = Query(None, description="Поиск по описанию"),
    author: Optional[str] = Query(None, description="Поиск по автору"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    created_after: Optional[datetime] = Query(None, description="Создано после"),
    created_before: Optional[datetime] = Query(None, description="Создано до"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    search_params = schemas.AdvertisementSearch(
        title=title,
        description=description,
        author=author,
        min_price=min_price,
        max_price=max_price,
        created_after=created_after,
        created_before=created_before
    )
    return crud.search_advertisements(
        db, search_params=search_params, skip=skip, limit=limit
    )

@app.get("/health")
def health_check():
    return {"status": "healthy"}