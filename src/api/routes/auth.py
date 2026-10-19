from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.api.models.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.api.repositories.auth_repository import UserRepository, TokenRepository
from src.api.services.auth_service import auth_service
from src.api.dependencies.auth import (
    bearer_scheme,
    get_current_active_user,
)
from src.database.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user_repo = UserRepository(db)
    try:
        # Usa método com background email para sellers
        if body.role.value == "seller":
            user = auth_service.register_user_with_background_email(
                user_repo,
                background_tasks,
                name=body.name,
                email=body.email,
                password=body.password,
                role=body.role,
                phone=body.phone,
            )
        else:
            user = auth_service.register_user(
                user_repo,
                name=body.name,
                email=body.email,
                password=body.password,
                role=body.role,
                phone=body.phone,
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)

    user = auth_service.authenticate_user(user_repo, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    tokens = auth_service.create_user_tokens(user, token_repo)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)

    tokens = auth_service.refresh_access_token(body.refresh_token, user_repo, token_repo)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado.",
        )
    return tokens


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido.",
        )

    token_repo = TokenRepository(db)
    auth_service.logout(credentials.credentials, token_repo)
    return MessageResponse(detail="Logout realizado com sucesso.")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    from src.storage import image_service
    from src.api.services.iteration_service import iteration_service

    avatar_url = image_service.get_url(current_user.avatar_key) if current_user.avatar_key else None

    # Obter iterações restantes
    limit_data = iteration_service.get_iterations_limit(db, str(current_user.id))

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        email_verified=current_user.email_verified,
        avatar_key=current_user.avatar_key,
        avatar_url=avatar_url,
        zip_code=current_user.zip_code,
        address=current_user.address,
        number=current_user.number,
        complement=current_user.complement,
        neighborhood=current_user.neighborhood,
        city=current_user.city,
        state=current_user.state,
        created_at=current_user.created_at,
        iterations_remaining=limit_data["remaining"],
    )

