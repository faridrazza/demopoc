from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, models
from .database import get_db
from .auth_utils import verify_token, hash_password

router = APIRouter()

@router.post("/users/register", response_model=schemas.UserResponse, status_code=201)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/users/me", response_model=schemas.UserResponse)
async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/me", response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        # Check if email is already taken
        existing = db.query(models.User).filter(
            models.User.email == user_update.email,
            models.User.id != user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_update.email
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user_by_id(
    user_id: int,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/by-email/{email}", response_model=schemas.UserWithPassword)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    # Internal endpoint for auth service
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
