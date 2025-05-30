from datetime import timedelta # Added import
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Annotated

from backend.models import database_models as models
from backend.models import schemas
from backend.crud import crud_user
from backend.core import security
from backend.models.database_models import get_db

router = APIRouter(
    prefix="/users", # Changed prefix to be relative to API_V1_STR
    tags=["users"],
)

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_username = crud_user.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    if user.email:
        db_user_by_email = crud_user.get_user_by_email(db, email=user.email)
        if db_user_by_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    return crud_user.create_user(db=db, user=user)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    user = crud_user.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response_data = {"access_token": access_token, "token_type": "bearer"}
    
    # Manually add CORS header for debugging
    from fastapi.responses import JSONResponse
    response = JSONResponse(content=response_data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true" # Needed if allow_origins is not "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: Annotated[models.User, Depends(security.get_current_active_user)]
):
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: Annotated[models.User, Depends(security.get_current_active_user)],
    db: Session = Depends(get_db)
):
    # Users should not be able to make themselves superuser or change active status directly via this endpoint
    if user_update.is_superuser is not None or user_update.is_active is not None:
        raise HTTPException(status_code=403, detail="Cannot update 'is_superuser' or 'is_active' status via this endpoint.")

    # Prevent changing username via this endpoint if desired, or add specific logic
    # For email, check if the new email is already taken by another user
    if user_update.email and user_update.email != current_user.email:
        existing_user = crud_user.get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already registered by another user.")
            
    updated_user = crud_user.update_user(db, user_id=current_user.id, user_update=user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found") # Should not happen if current_user exists
    return updated_user


# Admin/Superuser routes
@router.get("/", response_model=List[schemas.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Requires superuser
):
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Requires superuser
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user_by_admin(
    user_id: int,
    user_update: schemas.UserUpdate, # Admin can update more fields
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Requires superuser
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email and user_update.email != db_user.email:
        existing_user = crud_user.get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered by another user.")

    updated_user = crud_user.update_user(db, user_id=user_id, user_update=user_update)
    return updated_user

# Consider if hard delete is needed or if is_active flag is sufficient.
# For now, let's make this an activate/deactivate endpoint.
@router.patch("/{user_id}/activate", response_model=schemas.UserResponse)
def toggle_user_activation(
    user_id: int,
    activate: bool, # Pass as query parameter or in body
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser)
):
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.id == current_user.id and not activate: # Superuser cannot deactivate themselves
         raise HTTPException(status_code=403, detail="Cannot deactivate your own superuser account.")
    
    updated_user = crud_user.activate_user(db, user_id=user_id, activate=activate)
    if not updated_user: # Should not happen if user was found
        raise HTTPException(status_code=500, detail="Could not update user activation status.")
    return updated_user

# If hard delete is truly needed:
# @router.delete("/{user_id}", response_model=schemas.UserResponse)
# def delete_user_by_admin(
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(security.get_current_active_superuser)
# ):
#     db_user = crud_user.get_user(db, user_id=user_id)
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if db_user.id == current_user.id: # Superuser cannot delete themselves
#          raise HTTPException(status_code=403, detail="Cannot delete your own superuser account.")
#     deleted_user = crud_user.delete_user(db, user_id=user_id)
#     return deleted_user
