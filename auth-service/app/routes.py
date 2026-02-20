from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from . import schemas, models, auth
from .database import get_db
import httpx
import os

router = APIRouter()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")

@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
async def register(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
    # Call User Service to create user
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/users/register",
                json={
                    "name": request.full_name,
                    "email": request.email,
                    "password": request.password,
                    "role": "user"
                }
            )
            if response.status_code == 400:
                raise HTTPException(status_code=400, detail="Email already registered")
            elif response.status_code != 201:
                raise HTTPException(status_code=500, detail="Failed to create user")
            user_data = response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User service unavailable")

    # Create tokens for the new user
    token_data = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "role": user_data["role"]
    }
    access_token = auth.create_access_token(token_data)
    refresh_token = auth.create_refresh_token(token_data)

    # Store refresh token
    token_hash = auth.hash_token(refresh_token)
    db_token = models.RefreshToken(
        user_id=user_data["id"],
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserInfo(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["name"]
        )
    )

@router.post("/login", response_model=schemas.TokenResponse)
async def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Call User Service to get user data
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/users/by-email/{request.email}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            user_data = response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User service unavailable")

    # Verify password
    if not auth.verify_password(request.password, user_data["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user_data["is_active"]:
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Create tokens
    token_data = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "role": user_data["role"]
    }
    access_token = auth.create_access_token(token_data)
    refresh_token = auth.create_refresh_token(token_data)

    # Store refresh token
    token_hash = auth.hash_token(refresh_token)
    db_token = models.RefreshToken(
        user_id=user_data["id"],
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=schemas.UserInfo(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["name"]
        )
    )

@router.get("/verify", response_model=schemas.TokenVerifyResponse)
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = auth.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        return schemas.TokenVerifyResponse(
            user_id=int(payload["sub"]),
            email=payload["email"],
            role=payload["role"]
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.get("/me", response_model=schemas.UserInfo)
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = auth.decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Get user details from user service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/users/by-email/{payload['email']}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="User not found")
            user_data = response.json()
        
        return schemas.UserInfo(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["name"]
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = auth.decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check if token exists and not revoked
    token_hash = auth.hash_token(request.refresh_token)
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == token_hash,
        models.RefreshToken.revoked == False
    ).first()

    if not db_token:
        raise HTTPException(status_code=401, detail="Token revoked or not found")

    # Create new tokens
    token_data = {
        "sub": payload["sub"],
        "email": payload["email"],
        "role": payload["role"]
    }
    new_access_token = auth.create_access_token(token_data)
    new_refresh_token = auth.create_refresh_token(token_data)

    # Revoke old refresh token and store new one
    db_token.revoked = True
    new_token_hash = auth.hash_token(new_refresh_token)
    new_db_token = models.RefreshToken(
        user_id=int(payload["sub"]),
        token_hash=new_token_hash,
        expires_at=datetime.utcnow() + timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_db_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )

@router.post("/logout")
async def logout(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = auth.decode_token(token)
        user_id = int(payload["sub"])
        
        # Revoke all refresh tokens for this user
        db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == user_id,
            models.RefreshToken.revoked == False
        ).update({"revoked": True})
        db.commit()
        
        return {"message": "Logged out successfully"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
