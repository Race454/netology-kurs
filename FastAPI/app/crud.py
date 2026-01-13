from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from . import models, schemas
from typing import Optional, Tuple
from decimal import Decimal

def create_advertisement(db: Session, advertisement: schemas.AdvertisementCreate):
    db_advertisement = models.Advertisement(
        title=advertisement.title,
        description=advertisement.description,
        price=advertisement.price,
        author=advertisement.author
    )
    db.add(db_advertisement)
    db.commit()
    db.refresh(db_advertisement)
    return db_advertisement

def get_advertisement(db: Session, advertisement_id: int):
    return db.query(models.Advertisement).filter(models.Advertisement.id == advertisement_id).first()

def update_advertisement(db: Session, advertisement_id: int, advertisement_update: schemas.AdvertisementUpdate):
    db_advertisement = get_advertisement(db, advertisement_id)
    if db_advertisement:
        update_data = advertisement_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_advertisement, key, value)
        db.commit()
        db.refresh(db_advertisement)
    return db_advertisement

def delete_advertisement(db: Session, advertisement_id: int):
    db_advertisement = get_advertisement(db, advertisement_id)
    if db_advertisement:
        db.delete(db_advertisement)
        db.commit()
        return True
    return False

def search_advertisements(
    db: Session, 
    search_params: schemas.AdvertisementSearch, 
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[models.Advertisement], int]:
    
    query = db.query(models.Advertisement)
    
    count_query = db.query(func.count(models.Advertisement.id))
    
    filters = []
    
    if search_params.title:
        filters.append(models.Advertisement.title.ilike(f"%{search_params.title}%"))
    
    if search_params.description:
        filters.append(models.Advertisement.description.ilike(f"%{search_params.description}%"))
    
    if search_params.author:
        filters.append(models.Advertisement.author.ilike(f"%{search_params.author}%"))
    
    if search_params.min_price is not None:
        filters.append(models.Advertisement.price >= search_params.min_price)
    
    if search_params.max_price is not None:
        filters.append(models.Advertisement.price <= search_params.max_price)
    
    if search_params.created_after:
        filters.append(models.Advertisement.created_at >= search_params.created_after)
    
    if search_params.created_before:
        filters.append(models.Advertisement.created_at <= search_params.created_before)
    
    if filters:
        query = query.filter(and_(*filters))
        count_query = count_query.filter(and_(*filters))

    total = count_query.scalar()
    
    items = query.order_by(models.Advertisement.created_at.desc()).offset(skip).limit(limit).all()
    
    return items, total