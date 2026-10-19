from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models.user import User
from src.api.dependencies.auth import get_current_active_user
from src.api.repositories.auth_repository import UserRepository
from src.api.models.auth import UserResponse
from src.api.services.iteration_service import iteration_service
from src.storage import image_service
from config.logger import logger

router = APIRouter(prefix="/users/me", tags=["users-me"])


class AvatarResponse(BaseModel):
    avatar_key: str
    avatar_url: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    zip_code: str | None = None
    address: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: str | None = None


class IterationsLimitResponse(BaseModel):
    enabled: bool
    daily_limit: int
    used_today: int
    remaining: int


@router.get("/iterations-limit", response_model=IterationsLimitResponse)
def get_iterations_limit(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retorna informações sobre o limite de iterações com IA do usuário."""
    limit_data = iteration_service.get_iterations_limit(db, str(current_user.id))
    return IterationsLimitResponse(**limit_data)


@router.patch("", response_model=UserResponse)
def update_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Atualiza o perfil do usuario logado (nome, email, telefone, endereco)."""
    user_repo = UserRepository(db)
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada para atualizar.")
    
    # Verifica se email ja existe (se estiver mudando)
    if "email" in update_data and update_data["email"] != current_user.email:
        existing = user_repo.get_by_email(update_data["email"])
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado.")
    
    updated = user_repo.update(current_user, **update_data)
    logger.info("Perfil atualizado: %s", current_user.email)
    avatar_url = image_service.get_url(updated.avatar_key) if updated.avatar_key else None

    # Obter iterações restantes
    limit_data = iteration_service.get_iterations_limit(db, str(current_user.id))

    return UserResponse(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        phone=updated.phone,
        role=updated.role,
        is_active=updated.is_active,
        is_verified=updated.is_verified,
        email_verified=updated.email_verified,
        avatar_key=updated.avatar_key,
        avatar_url=avatar_url,
        zip_code=updated.zip_code,
        address=updated.address,
        number=updated.number,
        complement=updated.complement,
        neighborhood=updated.neighborhood,
        city=updated.city,
        state=updated.state,
        created_at=updated.created_at,
        iterations_remaining=limit_data["remaining"],
    )



@router.post("/avatar", response_model=AvatarResponse)
def upload_avatar(
    file: UploadFile = File(..., description="Imagem de avatar (JPG, PNG, WEBP, GIF)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Faz upload do avatar do usuario logado."""
    user_repo = UserRepository(db)

    # Remove avatar antigo se existir
    if current_user.avatar_key:
        try:
            image_service.delete(current_user.avatar_key)
        except Exception as e:
            logger.warning("Falha ao remover avatar antigo: %s", e)

    try:
        stored = image_service.upload_user_avatar(
            user_id=str(current_user.id),
            file=file.file,
            filename=file.filename or "avatar.png",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    user_repo.update(current_user, avatar_key=stored.key)
    logger.info("Avatar atualizado: %s", current_user.email)

    return AvatarResponse(avatar_key=stored.key, avatar_url=stored.url)


@router.delete("/avatar", status_code=status.HTTP_204_NO_CONTENT)
def delete_avatar(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove o avatar do usuario logado."""
    if not current_user.avatar_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao possui avatar.",
        )

    try:
        image_service.delete(current_user.avatar_key)
    except Exception as e:
        logger.warning("Falha ao remover avatar do storage: %s", e)

    user_repo = UserRepository(db)
    user_repo.update(current_user, avatar_key=None)
    logger.info("Avatar removido: %s", current_user.email)
