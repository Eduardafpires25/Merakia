from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config.logger import logger
from config.settings import settings

# Silenciar loggers de terceiros para manter apenas os logs da aplicação
for _name in ("uvicorn", "uvicorn.access", "uvicorn.error", "alembic", "alembic.runtime.migration"):
    logging.getLogger(_name).setLevel(logging.WARNING)

from src.database.migration import run_migrations
from src.api.routes.auth import router as auth_router
from src.api.routes.email_verification import router as email_verification_router
from src.api.routes.sellers_public import router as sellers_public_router
from src.api.routes.sellers_me import router as sellers_me_router
from src.api.routes.users_me import router as users_me_router
from src.api.routes.orders import router as orders_router, seller_router as seller_orders_router
from src.api.routes.cart import router as cart_router
from src.api.routes.payments import router as payments_router
from src.api.routes.reviews import router as reviews_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando API MeraKia (DEV_MODE=%s)...", settings.DEV_MODE)
    try:
        run_migrations()
    except Exception as e:
        logger.error("Falha ao executar migrations: %s", e)
    yield
    logger.info("Encerrando API MeraKia...")


app = FastAPI(
    title="MeraKia API",
    description="API do MeraKia",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Retorna mensagens de erro de validação mais claras."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])
        msg = error["msg"]

        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "", 1)

        if field in {"password", "new_password"}:
            if "at least 8 characters" in msg or "Senha deve ter no mínimo 8 caracteres" in msg:
                msg = "Senha deve ter no mínimo 8 caracteres."
            elif "String should have at least" in msg:
                msg = "Senha deve ter no mínimo 8 caracteres."

        errors.append({"field": field, "message": msg})

    return JSONResponse(
        status_code=422,
        content={"detail": "Erro de validação", "errors": errors},
    )


app.include_router(auth_router, prefix="/api/v1")
app.include_router(email_verification_router, prefix="/api/v1")
app.include_router(users_me_router, prefix="/api/v1")
app.include_router(sellers_me_router, prefix="/api/v1")
app.include_router(seller_orders_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(sellers_public_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")


# Mount static files para imagens quando usando storage local
if settings.STORAGE_BACKEND.lower() == "local":
    import os
    os.makedirs(settings.IMAGES_DIR, exist_ok=True)
    mount_path = settings.STORAGE_PUBLIC_URL_BASE
    # Só adiciona barra no início se for caminho relativo (não URL absoluta)
    if not mount_path.startswith("/") and not mount_path.startswith("http"):
        mount_path = "/" + mount_path
    # Se for URL absoluta (http://...), só monta o caminho relativo
    if mount_path.startswith("http://") or mount_path.startswith("https://"):
        mount_path = "/" + mount_path.split("/", 3)[-1] if mount_path.count("/") >= 3 else "/images"
    app.mount(mount_path, StaticFiles(directory=settings.IMAGES_DIR), name="images")
    logger.info("Imagens servidas em %s -> %s", mount_path, settings.IMAGES_DIR)


@app.get("/")
def root():
    return {
        "message": "MeraKia API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
