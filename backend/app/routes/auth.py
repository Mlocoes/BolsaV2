from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from uuid import UUID
from ..core.database import get_db
from ..core.security import verify_password, hash_password
from ..core.session import session_manager
from ..core.middleware import require_auth, optional_auth
from ..models.usuario import Usuario
from ..core.config import settings
from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    session_id: Optional[str] = None  # Solo en desarrollo

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login con sesión en cookie HttpOnly
    
    Args:
        response: Response de FastAPI para setear cookie
        form_data: Credenciales del usuario
        db: Sesión de base de datos
    
    Returns:
        LoginResponse con datos del usuario
    """
    # Buscar usuario
    user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Actualizar último login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Crear sesión en Redis
    session_id = await session_manager.create_session(
        user_id=str(user.id),
        user_data={
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    )
    
    # Setear cookie HttpOnly segura
    response.set_cookie(
        key="session_id",
        value=session_id,
        domain=None,  # Sin dominio para que funcione en misma IP
        httponly=True,  # No accesible desde JavaScript
        secure=False,   # False para desarrollo HTTP, True para producción HTTPS
        samesite="lax",  # lax funciona en HTTP y permite navegación normal
        max_age=86400,  # 24 horas
        path="/",       # Cookie válida para toda la aplicación
    )
    
    # En desarrollo, también devolver el session_id en el body para permitir
    # autenticación cross-port cuando las cookies no funcionan
    return {
        "message": "Login exitoso",
        "user": user,
        "session_id": session_id if settings.ENVIRONMENT == "development" else None
    }

@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    user: dict = Depends(require_auth)
):
    """
    Logout - destruir sesión
    
    Args:
        response: Response de FastAPI para eliminar cookie
        request: Request para obtener session_id
        user: Usuario actual (dependency)
    
    Returns:
        Mensaje de confirmación
    """
    # Obtener session_id de la cookie
    session_id = request.cookies.get("session_id")
    
    if session_id:
        # Eliminar sesión de Redis
        await session_manager.delete_session(session_id)
    
    # Eliminar cookie
    response.delete_cookie(
        key="session_id",
        domain=None,
        path="/",
        samesite="lax",
    )
    
    return {"message": "Logout exitoso"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Obtener usuario actual desde sesión
    
    Args:
        user: Datos del usuario desde sesión
        db: Sesión de base de datos
    
    Returns:
        UserResponse con datos actualizados
    """
    # Obtener usuario actualizado de la BD
    db_user = db.query(Usuario).filter(Usuario.id == UUID(user["user_id"])).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    return db_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registrar nuevo usuario
    
    Args:
        user_data: Datos del nuevo usuario
        db: Sesión de base de datos
    
    Returns:
        UserResponse con datos del usuario creado
    """
    # Verificar si el usuario ya existe
    existing_user = db.query(Usuario).filter(
        (Usuario.username == user_data.username) | (Usuario.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario o email ya registrado"
        )
    
    # Crear nuevo usuario
    new_user = Usuario(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
