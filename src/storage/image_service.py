from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional

from config.logger import logger
from config.settings import settings
from src.storage.base import StoredFile
from src.storage.factory import get_storage


class ImageCategory(str, Enum):
    """Categorias de imagens (define a estrutura de pastas)."""
    USER_AVATAR = "users"
    SELLER_LOGO = "sellers/logos"
    SELLER_BANNER = "sellers/banners"
    PRODUCT = "products"
    AI_GENERATED = "ai-generated"
    ORDER = "orders"


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIMETYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


class ImageService:
    """
    Servico de alto nivel para upload/gestao de imagens.
    Usa o StorageBackend configurado (local ou s3).
    """

    def __init__(self) -> None:
        self._storage = None  # lazy init

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage()
        return self._storage

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    def _validate_image(self, filename: str, content_type: str, size_bytes: int) -> None:
        """Valida extensao, mimetype e tamanho."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Extensao nao suportada: {ext}. "
                f"Permitidas: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )

        if content_type not in ALLOWED_IMAGE_MIMETYPES:
            raise ValueError(
                f"Tipo de imagem nao suportado: {content_type}. "
                f"Permitidos: {', '.join(sorted(ALLOWED_IMAGE_MIMETYPES))}"
            )

        max_bytes = settings.STORAGE_MAX_UPLOAD_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(
                f"Arquivo muito grande ({size_bytes / 1024 / 1024:.1f}MB). "
                f"Maximo: {settings.STORAGE_MAX_UPLOAD_MB}MB."
            )

    def _build_key(
        self,
        category: ImageCategory,
        owner_id: str,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> str:
        """Gera chave unica: {category}/{owner_id}/{subfolder?}/{uuid}.{ext}"""
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"

        parts = [category.value, str(owner_id)]
        if subfolder:
            parts.append(subfolder)
        parts.append(unique_name)
        return "/".join(parts)

    # ------------------------------------------------------------
    # Upload generico
    # ------------------------------------------------------------

    def upload_image(
        self,
        *,
        category: ImageCategory,
        owner_id: str,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
        subfolder: Optional[str] = None,
        public: bool = True,
    ) -> StoredFile:
        """Upload de imagem para qualquer categoria."""
        # Detecta content_type se nao informado
        if not content_type:
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Calcula tamanho se nao informado
        if size_bytes is None:
            try:
                file.seek(0, 2)  # vai pro fim
                size_bytes = file.tell()
                file.seek(0)
            except Exception:
                size_bytes = 0

        self._validate_image(filename, content_type, size_bytes)

        key = self._build_key(category, owner_id, filename, subfolder)
        stored = self.storage.save(key, file, content_type=content_type, public=public)
        logger.info(
            "Imagem salva: category=%s owner=%s key=%s",
            category.value,
            owner_id,
            stored.key,
        )
        return stored

    # ------------------------------------------------------------
    # Helpers especificos por categoria
    # ------------------------------------------------------------

    def upload_user_avatar(
        self, user_id: str, file: BinaryIO, filename: str, content_type: Optional[str] = None
    ) -> StoredFile:
        return self.upload_image(
            category=ImageCategory.USER_AVATAR,
            owner_id=user_id,
            file=file,
            filename=filename,
            content_type=content_type,
            subfolder="avatar",
        )

    def upload_seller_logo(
        self, seller_id: str, file: BinaryIO, filename: str, content_type: Optional[str] = None
    ) -> StoredFile:
        return self.upload_image(
            category=ImageCategory.SELLER_LOGO,
            owner_id=seller_id,
            file=file,
            filename=filename,
            content_type=content_type,
        )

    def upload_seller_banner(
        self, seller_id: str, file: BinaryIO, filename: str, content_type: Optional[str] = None
    ) -> StoredFile:
        return self.upload_image(
            category=ImageCategory.SELLER_BANNER,
            owner_id=seller_id,
            file=file,
            filename=filename,
            content_type=content_type,
        )

    def upload_product_image(
        self,
        product_id: str,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
    ) -> StoredFile:
        return self.upload_image(
            category=ImageCategory.PRODUCT,
            owner_id=product_id,
            file=file,
            filename=filename,
            content_type=content_type,
        )

    def upload_ai_generated(
        self,
        owner_id: str,
        file: BinaryIO,
        filename: str = "generated.png",
        content_type: str = "image/png",
    ) -> StoredFile:
        # Organiza por data: ai-generated/{user_id}/2026-04-28/{uuid}.png
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.upload_image(
            category=ImageCategory.AI_GENERATED,
            owner_id=owner_id,
            file=file,
            filename=filename,
            content_type=content_type,
            subfolder=today,
        )

    def upload_order_reference(
        self,
        order_id: str,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
    ) -> StoredFile:
        return self.upload_image(
            category=ImageCategory.ORDER,
            owner_id=order_id,
            file=file,
            filename=filename,
            content_type=content_type,
            subfolder="references",
        )

    # ------------------------------------------------------------
    # Operacoes gerais
    # ------------------------------------------------------------

    def delete(self, key: str) -> bool:
        return self.storage.delete(key)

    def get_url(self, key: str) -> str:
        return self.storage.get_url(key)

    def get_signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self.storage.get_signed_url(key, expires_seconds)

    def exists(self, key: str) -> bool:
        return self.storage.exists(key)


image_service = ImageService()
