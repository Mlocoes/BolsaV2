from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from ..core.database import get_db
from ..core.middleware import require_auth
from ..models.usuario import Usuario
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/users", tags=["users"])


# Schemas
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


# Endpoints
@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Listar todos los usuarios (solo admin)
    """
    # Verificar si el usuario es admin
    current_user = db.query(Usuario).filter(Usuario.id == UUID(user["user_id"])).first()
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )
    
    users = db.query(Usuario).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Obtener un usuario por ID (solo admin o el mismo usuario)
    """
    current_user_id = UUID(user["user_id"])
    current_user = db.query(Usuario).filter(Usuario.id == current_user_id).first()
    
    # Solo admin puede ver otros usuarios
    if str(current_user_id) != str(user_id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    target_user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return target_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Actualizar un usuario (solo admin)
    """
    # Verificar si el usuario actual es admin
    current_user = db.query(Usuario).filter(Usuario.id == UUID(user["user_id"])).first()
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update users"
        )
    
    # Buscar usuario a actualizar
    target_user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Actualizar campos
    if user_update.is_active is not None:
        target_user.is_active = user_update.is_active
    if user_update.is_admin is not None:
        target_user.is_admin = user_update.is_admin
    
    db.commit()
    db.refresh(target_user)
    
    return target_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Eliminar un usuario (solo admin)
    No se puede eliminar a sí mismo
    """
    # Verificar si el usuario actual es admin
    current_user_id = UUID(user["user_id"])
    current_user = db.query(Usuario).filter(Usuario.id == current_user_id).first()
    
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    # No permitir auto-eliminación
    if str(current_user_id) == str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Buscar usuario a eliminar
    target_user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(target_user)
    db.commit()
    
    return {"message": "User deleted successfully"}
