from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from zxcvbn import zxcvbn

from src.database.models.enums import UserRole


ZXCVBN_TRANSLATIONS = {
    "Add another word or two": "Adicione mais uma ou duas palavras",
    "Add another word or two. Uncommon words are better.": "Adicione mais uma ou duas palavras. Palavras incomuns são melhores.",
    "Uncommon words are better": "Palavras incomuns são melhores",
    "Avoid repeated words and characters": "Evite palavras e caracteres repetidos",
    "Avoid sequences": "Evite sequências (como 'abc', '123')",
    "Avoid recent years": "Evite anos recentes",
    "Avoid years that are associated with you": "Evite anos associados a você",
    "Avoid dates and years that are associated with you.": "Evite datas e anos associados a você",
    "Avoid user-related words": "Evite palavras relacionadas ao usuário",
    "No need for symbols, digits, or uppercase letters": "Não é necessário usar símbolos, dígitos ou letras maiúsculas",
    "No need for symbols, digits, or uppercase letters.": "Não é necessário usar símbolos, dígitos ou letras maiúsculas.",
    "Use a few words, avoid common phrases": "Use algumas palavras, evite frases comuns",
    "Use a few words, avoid common phrases.": "Use algumas palavras, evite frases comuns.",
    "Use a longer keyboard pattern with more turns.": "Use um padrão de teclado mais longo com mais voltas.",
    "All-uppercase is almost as easy to guess as all-lowercase": "Tudo em maiúsculas é quase tão fácil de adivinhar quanto tudo em minúsculas",
    "All-uppercase is almost as easy to guess as all-lowercase.": "Tudo em maiúsculas é quase tão fácil de adivinhar quanto tudo em minúsculas.",
    "Capitalization doesn't help very much": "Capitalização não ajuda muito",
    "Capitalization doesn't help very much.": "Capitalização não ajuda muito.",
    "Reversed words aren't much harder to guess": "Palavras invertidas não são muito mais difíceis de adivinhar",
    "Reversed words aren't much harder to guess.": "Palavras invertidas não são muito mais difíceis de adivinhar.",
    "Predictable substitutions like '@' instead of 'a' don't help very much": "Substituições previsíveis como '@' em vez de 'a' não ajudam muito",
    "Predictable substitutions like '@' instead of 'a' don't help very much.": "Substituições previsíveis como '@' em vez de 'a' não ajudam muito.",
    "Straight rows of keys are easy to guess.": "Linhas retas de teclas são fáceis de adivinhar.",
    "Short keyboard patterns are easy to guess.": "Padrões curtos de teclado são fáceis de adivinhar.",
    'Repeats like "aaa" are easy to guess.': "Repetições como 'aaa' são fáceis de adivinhar.",
    'Repeats like "abcabcabc" are only slightly harder to guess than "abc".': "Repetições como 'abcabcabc' são apenas um pouco mais difíceis de adivinhar que 'abc'.",
    'Sequences like "abc" or "6543" are easy to guess.': "Sequências como 'abc' ou '6543' são fáceis de adivinhar.",
    "Recent years are easy to guess.": "Anos recentes são fáceis de adivinhar.",
    "Dates are often easy to guess.": "Datas são frequentemente fáceis de adivinhar.",
    "This is a top-10 common password.": "Esta é uma das 10 senhas mais comuns.",
    "This is a top-100 common password.": "Esta é uma das 100 senhas mais comuns.",
    "This is a very common password.": "Esta é uma senha muito comum.",
    "This is similar to a commonly used password.": "Esta é semelhante a uma senha comumente usada.",
    "A word by itself is easy to guess.": "Uma palavra por si só é fácil de adivinhar.",
    "Names and surnames by themselves are easy to guess.": "Nomes e sobrenomes por si só são fáceis de adivinhar.",
    "Common names and surnames are easy to guess.": "Nomes e sobrenomes comuns são fáceis de adivinhar.",
}


def translate_zxcvbn_suggestion(suggestion: str) -> str:
    return ZXCVBN_TRANSLATIONS.get(suggestion, suggestion)


def validate_password_strength(password: str) -> str:
    if len(password.encode("utf-8")) > 1000:
        raise ValueError("Senha muito longa. Máximo 1000 bytes.")

    resultado = zxcvbn(password)
    score = resultado.get("score", 0)

    if score < 2:
        feedback = resultado.get("feedback", {})
        warning = feedback.get("warning", "")
        sugestoes = feedback.get("suggestions", [])

        mensagem = "Senha fraca."

        if warning:
            mensagem += f" {translate_zxcvbn_suggestion(warning)}"

        if sugestoes:
            traduzidas = [translate_zxcvbn_suggestion(s) for s in sugestoes[:2]]
            mensagem += " Dicas: " + "; ".join(traduzidas)
        else:
            mensagem += " Use uma combinação de maiúsculas, minúsculas, números e símbolos."

        raise ValueError(mensagem)

    return password


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=30)
    role: UserRole = Field(
        default=UserRole.CLIENT,
        description="Papel do usuário: client ou seller. Admin é criado internamente.",
    )

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de telefone internacional."""
        if v is None or v == "":
            return None
        # Remove caracteres não numéricos (incluindo o +)
        numbers_only = "".join(filter(str.isdigit, v))
        # Valida telefone: mínimo 10 dígitos (DDD + número), máximo 15 (código internacional + DDD + número)
        if len(numbers_only) < 10 or len(numbers_only) > 15:
            raise ValueError("Telefone deve ter entre 10 e 15 dígitos (incluindo código internacional).")
        return numbers_only


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def check_password_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 1000:
            raise ValueError("Senha muito longa. Máximo 1000 bytes.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Tempo de vida do access token em segundos")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    email_verified: bool
    avatar_key: Optional[str] = None
    avatar_url: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime
    iterations_remaining: int = 0

    model_config = {"from_attributes": True}



class MessageResponse(BaseModel):
    detail: str
