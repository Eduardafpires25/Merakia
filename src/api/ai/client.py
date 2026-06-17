"""Cliente de IA do MeraKia.

Encapsula chamadas ao provider (OpenAI por padrão) para:
- gerar imagens conceituais a partir de descrições textuais (RF05/RF06)
- realizar completions estruturados conforme um schema Pydantic
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Type, TypeVar

from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel

from config.logger import logger
from config.settings import settings
import base64

from src.api.ai.schemas import (
    AIError,
    CompletionResult,
    GeneratedIterationImage,
    ImageGenerationResult,
)
from src.api.ai.placeholders import get_green_placeholder

T = TypeVar("T", bound=BaseModel)

# Tipagem leve de mensagens chat
ChatMessage = Dict[str, Any]


class AIClient:
    """Wrapper de alto nível para o SDK da OpenAI.

    Pode ser instanciado em qualquer parte do sistema, ou utilizado via a
    instância global :data:`ai_client`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        text_model: Optional[str] = None,
        image_model: Optional[str] = None,
        image_size: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.text_model = text_model or settings.OPENAI_TEXT_MODEL
        self.image_model = image_model or settings.OPENAI_IMAGE_MODEL
        self.image_size = image_size or settings.OPENAI_IMAGE_SIZE
        self.timeout = timeout or settings.OPENAI_TIMEOUT_SECONDS

        if not self.api_key:
            logger.warning("AIClient inicializado sem OPENAI_API_KEY definida.")

        self._client = OpenAI(
            api_key=self.api_key or "missing",
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        n: int = 1,
        response_format: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ImageGenerationResult:
        """Gera uma imagem conceitual a partir de uma descrição textual.

        :param prompt: descrição livre do produto desejado.
        :param model: sobrescreve o modelo padrão de imagem.
        :param size: tamanho (ex.: ``"1024x1024"``).
        :param n: número de imagens a gerar (apenas a primeira é retornada).
        :param response_format: ``"url"`` ou ``"b64_json"``. Quando ``None``,
            usa o padrão do provider.
        :param extra: kwargs adicionais passados ao SDK.
        """
        if not prompt or not prompt.strip():
            raise AIError("O prompt para geração de imagem não pode ser vazio.")

        chosen_model = model or self.image_model
        chosen_size = size or self.image_size

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "prompt": prompt,
            "size": chosen_size,
            "n": n,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        if extra:
            kwargs.update(extra)

        started = time.perf_counter()
        try:
            response = self._client.images.generate(**kwargs)
            
        except AuthenticationError as exc:
            logger.error("Chave da API OpenAI inválida ou expirada (model=%s)", chosen_model)
            raise AIError(
                "Erro de autenticação com o serviço de IA. "
                "Verifique a configuração da chave da API."
            ) from exc

        except PermissionDeniedError as exc:
            logger.error("Permissão negada pela OpenAI (model=%s): %s", chosen_model, exc)
            raise AIError(
                "Sem permissão para usar o modelo de geração de imagens. "
                "A organização pode precisar de verificação."
            ) from exc

        except NotFoundError as exc:
            logger.error("Modelo não encontrado na OpenAI (model=%s)", chosen_model)
            raise AIError(
                f"Modelo '{chosen_model}' não encontrado. "
                "Verifique a configuração do modelo de imagem."
            ) from exc

        except RateLimitError as exc:
            logger.error("Rate limit da OpenAI atingido (model=%s)", chosen_model)
            raise AIError(
                "Limite de requisições do serviço de IA atingido. "
                "Aguarde alguns segundos e tente novamente."
            ) from exc

        except BadRequestError as exc:
            exc_str = str(exc)
            if "billing_hard_limit_reached" in exc_str:
                logger.error("Limite de billing da OpenAI atingido (model=%s)", chosen_model)
                raise AIError(
                    "O serviço de geração de imagens está temporariamente indisponível. "
                    "Tente novamente mais tarde."
                ) from exc
            if "moderation_blocked" in exc_str:
                logger.warning("Conteúdo bloqueado pela moderação da OpenAI (model=%s)", chosen_model)
                raise AIError(
                    "Sua descrição foi bloqueada pelo sistema de segurança. "
                    "Tente reformular sua descrição evitando conteúdo inadequado."
                ) from exc
            logger.exception("Erro de requisição na geração de imagem (model=%s)", chosen_model)
            raise AIError(f"Falha ao gerar imagem: {exc}") from exc

        except APITimeoutError as exc:
            logger.error("Timeout na chamada à OpenAI (model=%s)", chosen_model)
            raise AIError(
                "A geração de imagem demorou muito. "
                "Tente novamente."
            ) from exc

        except APIConnectionError as exc:
            logger.error("Erro de conexão com a OpenAI (model=%s)", chosen_model)
            raise AIError(
                "Não foi possível conectar ao serviço de IA. "
                "Verifique sua conexão e tente novamente."
            ) from exc

        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha inesperada na geração de imagem (model=%s)", chosen_model)
            raise AIError(f"Falha ao gerar imagem: {exc}") from exc
        duration_ms = int((time.perf_counter() - started) * 1000)

        if not response.data:
            raise AIError("Provider retornou resposta vazia para geração de imagem.")

        item = response.data[0]
        url = getattr(item, "url", None)
        b64 = getattr(item, "b64_json", None)
        revised_prompt = getattr(item, "revised_prompt", None)

        try:
            raw = response.model_dump()
        except Exception:  # pragma: no cover
            raw = None

        return ImageGenerationResult(
            model=chosen_model,
            prompt=prompt,
            revised_prompt=revised_prompt,
            url=url,
            b64_json=b64,
            size=chosen_size,
            duration_ms=duration_ms,
            raw=raw,
        )

    def generate_iteration_image(
        self,
        description: str,
        product_type: Optional[str] = None,
    ) -> GeneratedIterationImage:
        """
        Gera bytes de imagem para uma iteracao de pedido.

        Quando settings.AI_PLACEHOLDER_MODE=True (default em DEV),
        retorna PNG verde 512x512 sem chamar a API.

        Caso contrario, chama generate_image() e decodifica b64_json.
        """
        prompt = self._build_iteration_prompt(description, product_type)
        started = time.perf_counter()

        if settings.AI_PLACEHOLDER_MODE:
            image_bytes = get_green_placeholder(512, 512)
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "Imagem gerada (placeholder verde): prompt='%s...' duration=%dms",
                prompt[:60], duration_ms,
            )
            return GeneratedIterationImage(
                image_bytes=image_bytes,
                content_type="image/png",
                prompt=prompt,
                model="placeholder-green",
                duration_ms=duration_ms,
                cost_usd=0.0,
            )

        # Modo real: chama OpenAI
        result = self.generate_image(prompt)
        if not result.b64_json:
            raise AIError("Provider nao retornou b64_json para a imagem.")

        image_bytes = base64.b64decode(result.b64_json)
        return GeneratedIterationImage(
            image_bytes=image_bytes,
            content_type="image/png",
            prompt=result.prompt,
            model=result.model,
            duration_ms=result.duration_ms or 0,
            cost_usd=None,
        )

    @staticmethod
    def _build_iteration_prompt(description: str, product_type: Optional[str]) -> str:
        """Monta prompt final para geracao de imagem da iteracao."""
        prefix = f"Customizable {product_type} design: " if product_type else "Custom artisanal design: "
        return f"{prefix}{description.strip()}"

    def complete_with_schema(
        self,
        messages: List[ChatMessage] | str,
        schema: Type[T],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> CompletionResult[T]:
        """Executa uma chat completion forçando saída no formato de ``schema``.

        Usa ``client.beta.chat.completions.parse`` da OpenAI (Structured Outputs),
        que valida e instancia automaticamente um modelo Pydantic.

        :param messages: lista de mensagens no formato chat (``role``/``content``)
            ou uma única string que será enviada como mensagem do usuário.
        :param schema: classe Pydantic que descreve o JSON esperado.
        :param model: sobrescreve o modelo de texto padrão.
        :param system_prompt: se informado, é prependido como mensagem ``system``.
        """
        if not isinstance(schema, type) or not issubclass(schema, BaseModel):
            raise AIError("schema deve ser uma subclasse de pydantic.BaseModel.")

        chosen_model = model or self.text_model

        if isinstance(messages, str):
            normalized: List[ChatMessage] = [{"role": "user", "content": messages}]
        else:
            normalized = list(messages)

        if system_prompt:
            normalized = [{"role": "system", "content": system_prompt}, *normalized]

        kwargs: Dict[str, Any] = {
            "model": chosen_model,
            "messages": normalized,
            "temperature": temperature,
            "response_format": schema,
        }
        if extra:
            kwargs.update(extra)

        started = time.perf_counter()
        try:
            response = self._client.beta.chat.completions.parse(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha em complete_with_schema (model=%s)", chosen_model)
            raise AIError(f"Falha na completion estruturada: {exc}") from exc
        duration_ms = int((time.perf_counter() - started) * 1000)

        if not response.choices:
            raise AIError("Provider retornou resposta sem choices.")

        parsed = response.choices[0].message.parsed
        if parsed is None:
            refusal = getattr(response.choices[0].message, "refusal", None)
            raise AIError(f"Modelo recusou ou não retornou parse válido: {refusal}")

        usage = getattr(response, "usage", None)
        try:
            raw = response.model_dump()
        except Exception:  # pragma: no cover
            raw = None

        return CompletionResult[schema](
            model=chosen_model,
            parsed=parsed,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            total_tokens=getattr(usage, "total_tokens", None) if usage else None,
            duration_ms=duration_ms,
            raw=raw,
        )


ai_client = AIClient()
