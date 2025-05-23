from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import schemas, models, jwt
from ..database import get_db
from .dependencies import get_current_active_user, get_current_superuser
from ..config import get_settings

settings = get_settings()
auth_handler = jwt.AuthHandler(settings.dict())
router = APIRouter()

@router.post("/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth_handler.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_handler.create_access_token(data={"sub": user.username})
    refresh_token = auth_handler.create_refresh_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/users", response_model=schemas.UserInDB)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superuser)
):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth_handler.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/me", response_model=schemas.UserInDB)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user

@router.put("/users/me", response_model=schemas.UserInDB)
async def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if user_update.password is not None:
        current_user.hashed_password = auth_handler.get_password_hash(user_update.password)
    if user_update.email is not None:
        current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    return current_user 