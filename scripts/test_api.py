"""
Script de testes E2E para a API MeraKia.

Uso:
    python scripts/test_api.py
    python scripts/test_api.py --base-url http://localhost:8000
    python scripts/test_api.py --skip-cleanup  (mantem usuarios criados no banco)

Requer: requests, psycopg2 (opcional, para ler codigo de verificacao do banco).
"""

from __future__ import annotations

import argparse
import io
import os
import random
import string
import sys
import time
from typing import Any, Dict, Optional, Tuple

import requests

# PNG 1x1 transparente valido (67 bytes) - usado como fixture de imagem
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c63000100000005000100"
    "0d0a2db40000000049454e44ae426082"
)

# JPG/JPEG nao-imagem (txt) para testar rejeicao
FAKE_TXT = b"este nao e uma imagem"


# Cores ANSI para terminal
class C:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# ============================================================
# Helpers
# ============================================================

class TestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/api/v1"
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.failures: list[str] = []

    def _print_header(self, title: str):
        print(f"\n{C.BOLD}{C.INFO}{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}{C.END}")

    def _print_subheader(self, title: str):
        print(f"\n{C.BOLD}--- {title} ---{C.END}")

    def assert_status(
        self,
        name: str,
        response: requests.Response,
        expected: int,
        show_body: bool = False,
    ) -> bool:
        actual = response.status_code
        if actual == expected:
            print(f"  {C.OK}[PASS]{C.END} {name} -> {actual}")
            if show_body:
                try:
                    print(f"        {C.DIM}{response.json()}{C.END}")
                except Exception:
                    pass
            self.passed += 1
            return True
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} {name} -> esperado {expected}, recebido {actual}")
            try:
                print(f"        {C.DIM}{response.json()}{C.END}")
            except Exception:
                print(f"        {C.DIM}{response.text[:200]}{C.END}")
            self.failed += 1
            self.failures.append(f"{name} (esperado {expected}, recebido {actual})")
            return False

    def skip(self, name: str, reason: str):
        print(f"  {C.WARN}[SKIP]{C.END} {name} -> {reason}")
        self.skipped += 1

    def summary(self) -> int:
        total = self.passed + self.failed
        print(f"\n{C.BOLD}{'=' * 70}")
        print(f"  RESUMO")
        print(f"{'=' * 70}{C.END}")
        print(f"  Total executados:  {total}")
        print(f"  {C.OK}Passou: {self.passed}{C.END}")
        print(f"  {C.FAIL}Falhou: {self.failed}{C.END}")
        print(f"  {C.WARN}Pulou:  {self.skipped}{C.END}")

        if self.failures:
            print(f"\n{C.FAIL}{C.BOLD}Falhas:{C.END}")
            for f in self.failures:
                print(f"  - {f}")

        if self.failed == 0:
            print(f"\n{C.OK}{C.BOLD}TODOS OS TESTES PASSARAM!{C.END}\n")
            return 0
        else:
            print(f"\n{C.FAIL}{C.BOLD}{self.failed} TESTE(S) FALHARAM{C.END}\n")
            return 1


def random_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def random_email() -> str:
    return f"test_{random_str(10)}@example.com"


# ============================================================
# Helper: ler codigo de verificacao direto do banco
# ============================================================

def get_verification_code_from_db(email: str) -> Optional[str]:
    """Tenta ler o codigo de verificacao do banco. Requer .env carregado."""
    try:
        import os
        import psycopg2
        from dotenv import load_dotenv

        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=os.getenv("POSTGRES_DB"),
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT email_verification_code FROM users WHERE email = %s",
                    (email,),
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        print(f"  {C.WARN}[WARN]{C.END} Nao foi possivel ler codigo do DB: {e}")
        return None


# ============================================================
# Test Suites
# ============================================================

STRONG_PASSWORD = "Casa#Verde2024!Forte"


def test_health_and_root(t: TestRunner):
    t._print_header("HEALTH & ROOT")

    r = requests.get(f"{t.base_url}/")
    t.assert_status("GET /", r, 200, show_body=True)

    r = requests.get(f"{t.base_url}/health")
    t.assert_status("GET /health", r, 200, show_body=True)

    r = requests.get(f"{t.base_url}/docs")
    t.assert_status("GET /docs", r, 200)


def test_auth_register(t: TestRunner) -> Dict[str, Any]:
    """Testa registro e retorna usuarios criados."""
    t._print_header("AUTH - REGISTER")

    users = {}

    # 1. Registro de client com sucesso
    t._print_subheader("Cliente valido")
    client_email = random_email()
    payload = {
        "name": "Cliente Teste",
        "email": client_email,
        "password": STRONG_PASSWORD,
        "phone": "11999998888",
        "role": "client",
    }
    r = requests.post(f"{t.api}/auth/register", json=payload)
    if t.assert_status("POST /auth/register (client)", r, 201):
        users["client"] = {**payload, "id": r.json().get("id")}

    # 2. Registro de seller com sucesso
    t._print_subheader("Seller valido")
    seller_email = random_email()
    payload = {
        "name": "Loja Teste",
        "email": seller_email,
        "password": STRONG_PASSWORD,
        "phone": "11988887777",
        "role": "seller",
    }
    r = requests.post(f"{t.api}/auth/register", json=payload)
    if t.assert_status("POST /auth/register (seller)", r, 201):
        users["seller"] = {**payload, "id": r.json().get("id")}

    # 3. Senha fraca
    t._print_subheader("Validacoes")
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "Fraco",
            "email": random_email(),
            "password": "12345678",
            "role": "client",
        },
    )
    t.assert_status("POST /auth/register (senha fraca)", r, 422)

    # 4. Senha curta
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "Curto",
            "email": random_email(),
            "password": "abc",
            "role": "client",
        },
    )
    t.assert_status("POST /auth/register (senha curta)", r, 422)

    # 5. Email invalido
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "Mail",
            "email": "nao-eh-email",
            "password": STRONG_PASSWORD,
            "role": "client",
        },
    )
    t.assert_status("POST /auth/register (email invalido)", r, 422)

    # 6. Email duplicado
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "Duplicado",
            "email": client_email,
            "password": STRONG_PASSWORD,
            "role": "client",
        },
    )
    t.assert_status("POST /auth/register (email duplicado)", r, 409)

    # 7. Tentativa de registrar admin
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "Admin",
            "email": random_email(),
            "password": STRONG_PASSWORD,
            "role": "admin",
        },
    )
    # role=admin pode falhar como 422 (enum) ou 409 (validacao no service)
    if r.status_code in (409, 422):
        print(f"  {C.OK}[PASS]{C.END} POST /auth/register (admin bloqueado) -> {r.status_code}")
        t.passed += 1
    else:
        print(f"  {C.FAIL}[FAIL]{C.END} POST /auth/register (admin) -> esperado 409/422, recebido {r.status_code}")
        t.failed += 1
        t.failures.append("registro de admin nao foi bloqueado")

    # 8. Nome muito curto
    r = requests.post(
        f"{t.api}/auth/register",
        json={
            "name": "A",
            "email": random_email(),
            "password": STRONG_PASSWORD,
            "role": "client",
        },
    )
    t.assert_status("POST /auth/register (nome curto)", r, 422)

    return users


def test_auth_login(t: TestRunner, users: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Testa login e retorna tokens."""
    t._print_header("AUTH - LOGIN")

    tokens: Dict[str, Dict[str, str]] = {}

    if "client" not in users or "seller" not in users:
        t.skip("Login tests", "usuarios nao foram criados")
        return tokens

    # Login client
    t._print_subheader("Login valido")
    r = requests.post(
        f"{t.api}/auth/login",
        json={"email": users["client"]["email"], "password": STRONG_PASSWORD},
    )
    if t.assert_status("POST /auth/login (client)", r, 200):
        tokens["client"] = r.json()

    # Login seller
    r = requests.post(
        f"{t.api}/auth/login",
        json={"email": users["seller"]["email"], "password": STRONG_PASSWORD},
    )
    if t.assert_status("POST /auth/login (seller)", r, 200):
        tokens["seller"] = r.json()

    # Login senha errada
    t._print_subheader("Login invalido")
    r = requests.post(
        f"{t.api}/auth/login",
        json={"email": users["client"]["email"], "password": "errada123XYZ#"},
    )
    t.assert_status("POST /auth/login (senha errada)", r, 401)

    # Login email inexistente
    r = requests.post(
        f"{t.api}/auth/login",
        json={"email": "nao_existe@nada.com", "password": STRONG_PASSWORD},
    )
    t.assert_status("POST /auth/login (usuario inexistente)", r, 401)

    return tokens


def test_auth_me_and_refresh(t: TestRunner, tokens: Dict[str, Dict[str, str]]):
    t._print_header("AUTH - /me, /refresh, /logout")

    if "client" not in tokens:
        t.skip("Auth /me tests", "tokens nao foram obtidos")
        return

    access = tokens["client"]["access_token"]
    refresh = tokens["client"]["refresh_token"]

    # GET /me com token
    r = requests.get(
        f"{t.api}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    t.assert_status("GET /auth/me (com token)", r, 200, show_body=True)

    # GET /me sem token
    r = requests.get(f"{t.api}/auth/me")
    t.assert_status("GET /auth/me (sem token)", r, 401)

    # GET /me com token invalido
    r = requests.get(
        f"{t.api}/auth/me",
        headers={"Authorization": "Bearer token-invalido-12345"},
    )
    t.assert_status("GET /auth/me (token invalido)", r, 401)

    # POST /refresh
    r = requests.post(f"{t.api}/auth/refresh", json={"refresh_token": refresh})
    t.assert_status("POST /auth/refresh (valido)", r, 200)

    # POST /refresh invalido
    r = requests.post(f"{t.api}/auth/refresh", json={"refresh_token": "invalido"})
    t.assert_status("POST /auth/refresh (invalido)", r, 401)


def test_email_verification(t: TestRunner, tokens: Dict[str, Dict[str, str]], seller_email: str):
    t._print_header("EMAIL VERIFICATION")

    if "seller" not in tokens:
        t.skip("Email verification tests", "seller token nao disponivel")
        return

    access = tokens["seller"]["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    # GET status (deve ser nao verificado)
    r = requests.get(f"{t.api}/email/status", headers=headers)
    t.assert_status("GET /email/status (nao verificado)", r, 200, show_body=True)

    # POST verify com codigo errado
    r = requests.post(
        f"{t.api}/email/verify",
        headers=headers,
        json={"code": "000000"},
    )
    t.assert_status("POST /email/verify (codigo errado)", r, 400)

    # Tentar pegar o codigo do banco e verificar de verdade
    code = get_verification_code_from_db(seller_email)
    if code:
        print(f"  {C.INFO}[INFO]{C.END} Codigo encontrado no DB: {code}")
        r = requests.post(
            f"{t.api}/email/verify",
            headers=headers,
            json={"code": code},
        )
        t.assert_status("POST /email/verify (codigo correto)", r, 200, show_body=True)

        # Tentar verificar de novo (ja verificado)
        r = requests.post(
            f"{t.api}/email/verify",
            headers=headers,
            json={"code": code},
        )
        t.assert_status("POST /email/verify (ja verificado)", r, 400)

        # Status agora deve ser verificado
        r = requests.get(f"{t.api}/email/status", headers=headers)
        t.assert_status("GET /email/status (apos verificacao)", r, 200, show_body=True)
    else:
        t.skip("POST /email/verify (codigo correto)", "codigo nao encontrado no DB")


def test_sellers_public_empty(t: TestRunner):
    t._print_header("SELLERS PUBLIC - SEM DADOS")

    r = requests.get(f"{t.api}/sellers/")
    t.assert_status("GET /sellers/ (lista)", r, 200)

    r = requests.get(f"{t.api}/sellers/categories")
    t.assert_status("GET /sellers/categories", r, 200, show_body=True)

    # ID inexistente
    r = requests.get(f"{t.api}/sellers/00000000-0000-0000-0000-000000000000")
    t.assert_status("GET /sellers/{id-inexistente}", r, 404)

    # Slug inexistente
    r = requests.get(f"{t.api}/sellers/by-slug/nao-existe-essa-loja")
    t.assert_status("GET /sellers/by-slug/{inexistente}", r, 404)


def test_sellers_me_unauthorized(t: TestRunner, client_token: Optional[str]):
    t._print_header("SELLERS /me - PERMISSOES")

    # Sem token
    r = requests.get(f"{t.api}/sellers/me/profile")
    t.assert_status("GET /sellers/me/profile (sem token)", r, 401)

    # Com token de client (deve ser bloqueado)
    if client_token:
        r = requests.get(
            f"{t.api}/sellers/me/profile",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        t.assert_status("GET /sellers/me/profile (token de client)", r, 403)


def test_sellers_me_full_flow(
    t: TestRunner,
    seller_token: Optional[str],
    email_verified: bool,
) -> Optional[Tuple[str, str]]:
    """Fluxo completo de criacao de profile + produtos. Retorna seller_id, product_id se criado."""
    t._print_header("SELLERS /me - FLUXO COMPLETO (CRUD)")

    if not seller_token:
        t.skip("Sellers /me full flow", "seller token nao disponivel")
        return None

    headers = {"Authorization": f"Bearer {seller_token}"}

    # GET profile (deve ser 404 - nao tem profile)
    r = requests.get(f"{t.api}/sellers/me/profile", headers=headers)
    t.assert_status("GET /sellers/me/profile (sem profile criado)", r, 404)

    # POST profile (sem email verificado - deve dar 403)
    profile_payload = {
        "store_name": f"Loja Teste {random_str(4)}",
        "description": "Loja de canecas personalizadas",
        "category": "mug",
        "whatsapp": "+5511999998888",
        "instagram": "@lojateste",
        "city": "Sao Paulo",
        "state": "SP",
        "accepts_custom_designs": True,
        "min_order_quantity": 1,
        "estimated_days": 7,
    }

    if not email_verified:
        r = requests.post(f"{t.api}/sellers/me/profile", headers=headers, json=profile_payload)
        t.assert_status("POST /sellers/me/profile (email NAO verificado)", r, 403)
        t.skip("Restante do fluxo de seller", "email nao verificado")
        return None

    # POST profile (com email verificado)
    r = requests.post(f"{t.api}/sellers/me/profile", headers=headers, json=profile_payload)
    seller_id = None
    if t.assert_status("POST /sellers/me/profile (criar)", r, 201, show_body=True):
        seller_id = r.json().get("id")

    # POST profile duplicado (deve falhar)
    r = requests.post(f"{t.api}/sellers/me/profile", headers=headers, json=profile_payload)
    t.assert_status("POST /sellers/me/profile (duplicado)", r, 409)

    # GET profile
    r = requests.get(f"{t.api}/sellers/me/profile", headers=headers)
    t.assert_status("GET /sellers/me/profile (existente)", r, 200)

    # PATCH profile
    r = requests.patch(
        f"{t.api}/sellers/me/profile",
        headers=headers,
        json={"description": "Descricao atualizada"},
    )
    t.assert_status("PATCH /sellers/me/profile", r, 200)

    # PATCH profile vazio (deve dar 400)
    r = requests.patch(f"{t.api}/sellers/me/profile", headers=headers, json={})
    t.assert_status("PATCH /sellers/me/profile (vazio)", r, 400)

    # =========== Produtos ===========
    t._print_subheader("Produtos")

    # GET products (lista vazia)
    r = requests.get(f"{t.api}/sellers/me/products", headers=headers)
    t.assert_status("GET /sellers/me/products (vazio)", r, 200)

    # POST product
    product_payload = {
        "name": "Caneca 250ml Branca",
        "description": "Caneca de ceramica branca, ideal para sublimacao",
        "attributes": {"volume_ml": 250, "color": "white", "material": "ceramic"},
        "base_price": 25.90,
    }
    r = requests.post(f"{t.api}/sellers/me/products", headers=headers, json=product_payload)
    product_id = None
    if t.assert_status("POST /sellers/me/products (criar)", r, 201, show_body=True):
        product_id = r.json().get("id")

    # POST product duplicado (mesmo nome)
    r = requests.post(f"{t.api}/sellers/me/products", headers=headers, json=product_payload)
    t.assert_status("POST /sellers/me/products (nome duplicado)", r, 409)

    # POST outro produto valido
    r = requests.post(
        f"{t.api}/sellers/me/products",
        headers=headers,
        json={
            "name": "Caneca 350ml Preta",
            "description": "Caneca preta",
            "attributes": {"volume_ml": 350, "color": "black"},
            "base_price": 29.90,
        },
    )
    t.assert_status("POST /sellers/me/products (outro)", r, 201)

    # GET products (com 2 itens)
    r = requests.get(f"{t.api}/sellers/me/products", headers=headers)
    if t.assert_status("GET /sellers/me/products (com itens)", r, 200):
        body = r.json()
        if body.get("total") != 2:
            print(f"  {C.WARN}[WARN]{C.END} Esperado total=2, recebido total={body.get('total')}")

    if product_id:
        # GET product especifico
        r = requests.get(f"{t.api}/sellers/me/products/{product_id}", headers=headers)
        t.assert_status("GET /sellers/me/products/{id}", r, 200)

        # PATCH product
        r = requests.patch(
            f"{t.api}/sellers/me/products/{product_id}",
            headers=headers,
            json={"base_price": 30.00},
        )
        t.assert_status("PATCH /sellers/me/products/{id}", r, 200)

    # GET product inexistente
    r = requests.get(
        f"{t.api}/sellers/me/products/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    t.assert_status("GET /sellers/me/products/{inexistente}", r, 404)

    # NAO deletamos product_id aqui porque sera usado nos testes de imagens
    return seller_id, product_id


# ============================================================
# Image tests
# ============================================================

def _verify_image_url(t: TestRunner, name: str, url: str, base_url: str) -> bool:
    """Baixa a URL e verifica que retorna bytes de imagem (>= 67 bytes)."""
    if not url:
        print(f"  {C.FAIL}[FAIL]{C.END} {name}: URL vazia")
        t.failed += 1
        t.failures.append(f"{name} (URL vazia)")
        return False

    full_url = url if url.startswith("http") else base_url.rstrip("/") + url
    try:
        r = requests.get(full_url, timeout=5)
    except requests.RequestException as e:
        print(f"  {C.FAIL}[FAIL]{C.END} {name}: erro ao baixar {full_url}: {e}")
        t.failed += 1
        t.failures.append(f"{name} (erro download)")
        return False

    if r.status_code == 200 and len(r.content) >= len(TINY_PNG):
        print(f"  {C.OK}[PASS]{C.END} {name} -> downloaded {len(r.content)} bytes from {full_url}")
        t.passed += 1
        return True
    else:
        print(f"  {C.FAIL}[FAIL]{C.END} {name}: status={r.status_code}, bytes={len(r.content)} ({full_url})")
        t.failed += 1
        t.failures.append(f"{name} (download status {r.status_code})")
        return False


def test_user_avatar(t: TestRunner, client_token: Optional[str]):
    t._print_header("USER AVATAR (upload/delete)")

    if not client_token:
        t.skip("User avatar tests", "client token nao disponivel")
        return

    headers = {"Authorization": f"Bearer {client_token}"}

    # DELETE sem avatar -> 404
    r = requests.delete(f"{t.api}/users/me/avatar", headers=headers)
    t.assert_status("DELETE /users/me/avatar (sem avatar)", r, 404)

    # Upload tipo invalido (txt) -> 400
    r = requests.post(
        f"{t.api}/users/me/avatar",
        headers=headers,
        files={"file": ("fake.txt", FAKE_TXT, "text/plain")},
    )
    t.assert_status("POST /users/me/avatar (tipo invalido)", r, 400)

    # Upload sem arquivo -> 422
    r = requests.post(f"{t.api}/users/me/avatar", headers=headers)
    t.assert_status("POST /users/me/avatar (sem arquivo)", r, 422)

    # Upload valido
    r = requests.post(
        f"{t.api}/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", TINY_PNG, "image/png")},
    )
    avatar_url = None
    if t.assert_status("POST /users/me/avatar (valido)", r, 200, show_body=True):
        avatar_url = r.json().get("avatar_url")

    # Download da imagem
    if avatar_url:
        _verify_image_url(t, "GET avatar URL (download)", avatar_url, t.base_url)

    # Substituir avatar (upload novo deve substituir o antigo)
    r = requests.post(
        f"{t.api}/users/me/avatar",
        headers=headers,
        files={"file": ("avatar2.png", TINY_PNG, "image/png")},
    )
    t.assert_status("POST /users/me/avatar (substituir)", r, 200)

    # GET /me deve mostrar avatar (se a resposta incluir)
    r = requests.get(f"{t.api}/auth/me", headers=headers)
    t.assert_status("GET /auth/me (apos avatar)", r, 200)

    # DELETE avatar
    r = requests.delete(f"{t.api}/users/me/avatar", headers=headers)
    t.assert_status("DELETE /users/me/avatar", r, 204)

    # DELETE de novo -> 404
    r = requests.delete(f"{t.api}/users/me/avatar", headers=headers)
    t.assert_status("DELETE /users/me/avatar (ja removido)", r, 404)


def test_seller_logo_banner(t: TestRunner, seller_token: Optional[str], seller_id: Optional[str]):
    t._print_header("SELLER LOGO & BANNER")

    if not seller_token or not seller_id:
        t.skip("Seller logo/banner tests", "requer seller com profile")
        return

    headers = {"Authorization": f"Bearer {seller_token}"}

    # DELETE logo sem ter -> 404
    r = requests.delete(f"{t.api}/sellers/me/profile/logo", headers=headers)
    t.assert_status("DELETE /profile/logo (sem logo)", r, 404)

    # Upload logo invalido
    r = requests.post(
        f"{t.api}/sellers/me/profile/logo",
        headers=headers,
        files={"file": ("fake.txt", FAKE_TXT, "text/plain")},
    )
    t.assert_status("POST /profile/logo (tipo invalido)", r, 400)

    # Upload logo valido
    r = requests.post(
        f"{t.api}/sellers/me/profile/logo",
        headers=headers,
        files={"file": ("logo.png", TINY_PNG, "image/png")},
    )
    logo_url = None
    if t.assert_status("POST /profile/logo (valido)", r, 200):
        logo_url = r.json().get("logo_url")
        print(f"        {C.DIM}logo_url={logo_url}{C.END}")

    if logo_url:
        _verify_image_url(t, "GET logo URL (download)", logo_url, t.base_url)

    # Upload banner valido
    r = requests.post(
        f"{t.api}/sellers/me/profile/banner",
        headers=headers,
        files={"file": ("banner.png", TINY_PNG, "image/png")},
    )
    banner_url = None
    if t.assert_status("POST /profile/banner (valido)", r, 200):
        banner_url = r.json().get("banner_url")
        print(f"        {C.DIM}banner_url={banner_url}{C.END}")

    if banner_url:
        _verify_image_url(t, "GET banner URL (download)", banner_url, t.base_url)

    # GET profile deve retornar URLs
    r = requests.get(f"{t.api}/sellers/me/profile", headers=headers)
    if t.assert_status("GET /profile (com logo+banner)", r, 200):
        body = r.json()
        if not body.get("logo_url"):
            print(f"  {C.WARN}[WARN]{C.END} logo_url ausente na resposta")
        if not body.get("banner_url"):
            print(f"  {C.WARN}[WARN]{C.END} banner_url ausente na resposta")

    # Substituir logo (deve deletar o antigo)
    r = requests.post(
        f"{t.api}/sellers/me/profile/logo",
        headers=headers,
        files={"file": ("logo2.png", TINY_PNG, "image/png")},
    )
    t.assert_status("POST /profile/logo (substituir)", r, 200)

    # DELETE logo
    r = requests.delete(f"{t.api}/sellers/me/profile/logo", headers=headers)
    t.assert_status("DELETE /profile/logo", r, 204)

    # DELETE banner
    r = requests.delete(f"{t.api}/sellers/me/profile/banner", headers=headers)
    t.assert_status("DELETE /profile/banner", r, 204)


def test_product_images(
    t: TestRunner,
    seller_token: Optional[str],
    product_id: Optional[str],
) -> Optional[str]:
    """Testa CRUD completo de imagens de produto. Retorna o product_id usado."""
    t._print_header("PRODUCT IMAGES (CRUD completo)")

    if not seller_token or not product_id:
        t.skip("Product image tests", "requer product_id")
        return None

    headers = {"Authorization": f"Bearer {seller_token}"}
    base = f"{t.api}/sellers/me/products/{product_id}/images"

    # Lista vazia
    r = requests.get(base, headers=headers)
    if t.assert_status("GET images (lista vazia)", r, 200):
        if r.json() != []:
            print(f"  {C.WARN}[WARN]{C.END} Esperava lista vazia, recebeu {len(r.json())} itens")

    # Upload primeira imagem (deve virar capa automatica)
    r = requests.post(
        base,
        headers=headers,
        files={"file": ("img1.png", TINY_PNG, "image/png")},
        data={"alt_text": "Primeira imagem"},
    )
    img1_id = None
    img1_url = None
    if t.assert_status("POST images (1a - vira capa)", r, 201, show_body=True):
        body = r.json()
        img1_id = body.get("id")
        img1_url = body.get("url")
        if not body.get("is_cover"):
            print(f"  {C.FAIL}[FAIL]{C.END} 1a imagem deveria ser capa automaticamente")
            t.failed += 1
            t.failures.append("1a imagem nao virou capa")
        else:
            print(f"  {C.OK}[PASS]{C.END} 1a imagem marcada como capa")
            t.passed += 1

    if img1_url:
        _verify_image_url(t, "GET image URL (download)", img1_url, t.base_url)

    # Upload segunda imagem (nao capa)
    r = requests.post(
        base,
        headers=headers,
        files={"file": ("img2.png", TINY_PNG, "image/png")},
        data={"alt_text": "Segunda imagem", "is_cover": "false"},
    )
    img2_id = None
    if t.assert_status("POST images (2a)", r, 201):
        img2_id = r.json().get("id")

    # Upload terceira marcada como capa - deve mover capa
    r = requests.post(
        base,
        headers=headers,
        files={"file": ("img3.png", TINY_PNG, "image/png")},
        data={"is_cover": "true"},
    )
    img3_id = None
    if t.assert_status("POST images (3a - vira nova capa)", r, 201):
        img3_id = r.json().get("id")

    # Lista deve ter 3, e apenas 1 com is_cover=True
    r = requests.get(base, headers=headers)
    if t.assert_status("GET images (3 itens)", r, 200):
        body = r.json()
        if len(body) != 3:
            print(f"  {C.WARN}[WARN]{C.END} esperado 3 imagens, recebido {len(body)}")
        covers = [i for i in body if i.get("is_cover")]
        if len(covers) == 1 and covers[0].get("id") == img3_id:
            print(f"  {C.OK}[PASS]{C.END} apenas img3 e capa")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} esperado apenas img3 como capa, capas={[c.get('id') for c in covers]}")
            t.failed += 1
            t.failures.append("flag de capa unica nao respeitada")

    # PATCH alt_text
    if img2_id:
        r = requests.patch(
            f"{base}/{img2_id}",
            headers=headers,
            json={"alt_text": "Texto atualizado", "position": 5},
        )
        t.assert_status("PATCH image (alt_text+position)", r, 200)

    # PATCH set is_cover na img1 - deve tirar de img3
    if img1_id:
        r = requests.patch(
            f"{base}/{img1_id}",
            headers=headers,
            json={"is_cover": True},
        )
        t.assert_status("PATCH image (set is_cover)", r, 200)

        r = requests.get(base, headers=headers)
        if r.status_code == 200:
            covers = [i for i in r.json() if i.get("is_cover")]
            if len(covers) == 1 and covers[0].get("id") == img1_id:
                print(f"  {C.OK}[PASS]{C.END} capa transferida para img1")
                t.passed += 1
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} transferencia de capa falhou")
                t.failed += 1
                t.failures.append("transferencia de capa")

    # PATCH vazio -> 400
    if img1_id:
        r = requests.patch(f"{base}/{img1_id}", headers=headers, json={})
        t.assert_status("PATCH image (body vazio)", r, 400)

    # PATCH imagem inexistente
    r = requests.patch(
        f"{base}/00000000-0000-0000-0000-000000000000",
        headers=headers,
        json={"alt_text": "x"},
    )
    t.assert_status("PATCH image (inexistente)", r, 404)

    # Upload de tipo invalido
    r = requests.post(
        base,
        headers=headers,
        files={"file": ("fake.txt", FAKE_TXT, "text/plain")},
    )
    t.assert_status("POST images (tipo invalido)", r, 400)

    # DELETE img1 (era capa) - capa deve ir pra outra automaticamente
    if img1_id:
        r = requests.delete(f"{base}/{img1_id}", headers=headers)
        t.assert_status("DELETE image (capa)", r, 204)

        r = requests.get(base, headers=headers)
        if r.status_code == 200:
            body = r.json()
            covers = [i for i in body if i.get("is_cover")]
            if len(body) == 2 and len(covers) == 1:
                print(f"  {C.OK}[PASS]{C.END} capa promovida automaticamente apos delete")
                t.passed += 1
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} esperava 2 imagens com 1 capa, recebeu {len(body)}/{len(covers)}")
                t.failed += 1
                t.failures.append("promocao automatica de capa")

    # DELETE imagem inexistente
    r = requests.delete(
        f"{base}/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    t.assert_status("DELETE image (inexistente)", r, 404)

    return product_id


def test_public_image_urls(
    t: TestRunner,
    seller_id: Optional[str],
    product_id: Optional[str],
):
    """Verifica que rotas publicas retornam URLs de imagens corretamente."""
    t._print_header("PUBLIC ENDPOINTS - URLs de imagens")

    if not seller_id or not product_id:
        t.skip("Public image URLs", "requer seller_id e product_id")
        return

    # Detalhe publico do seller
    r = requests.get(f"{t.api}/sellers/{seller_id}")
    if t.assert_status("GET /sellers/{id} (publico)", r, 200):
        body = r.json()
        products = body.get("products", [])
        for p in products:
            if p.get("id") == product_id and p.get("cover_url"):
                print(f"  {C.OK}[PASS]{C.END} produto retorna cover_url no detalhe publico")
                t.passed += 1
                _verify_image_url(t, "download cover_url publica", p["cover_url"], t.base_url)
                break
        else:
            if products:
                print(f"  {C.WARN}[WARN]{C.END} cover_url nao retornado no detalhe publico")

    # Lista publica de imagens do produto
    r = requests.get(f"{t.api}/sellers/products/{product_id}/images")
    if t.assert_status("GET /sellers/products/{id}/images (publico)", r, 200):
        body = r.json()
        if body and body[0].get("url"):
            print(f"  {C.OK}[PASS]{C.END} imagens publicas tem URL")
            t.passed += 1
            _verify_image_url(t, "download imagem publica", body[0]["url"], t.base_url)


# ============================================================
# Customizable Products tests
# ============================================================

def test_customizable_products(t: TestRunner, seller_token: Optional[str]):
    """Testa criacao e atualizacao de produtos personalizaveis."""
    t._print_header("CUSTOMIZABLE PRODUCTS")

    if not seller_token:
        t.skip("Customizable products tests", "seller token nao disponivel")
        return

    headers = {"Authorization": f"Bearer {seller_token}"}

    # Criar produto personalizavel
    t._print_subheader("Criar produto personalizavel")
    custom_product_payload = {
        "name": "Caneca Personalizavel Premium",
        "description": "Caneca de ceramica premium com opcoes de tamanho e material",
        "attributes": {"material": "ceramic"},
        "is_customizable": True,
        "customization_options": {
            "sizes": ["250ml", "350ml", "500ml"],
            "materials": ["ceramic", "glass"],
            "colors": ["white", "black", "red"]
        },
        "base_price": 35.90,
    }
    r = requests.post(f"{t.api}/sellers/me/products", headers=headers, json=custom_product_payload)
    custom_product_id = None
    if t.assert_status("POST /sellers/me/products (personalizavel)", r, 201, show_body=True):
        body = r.json()
        custom_product_id = body.get("id")
        # Verifica que os campos foram salvos
        if body.get("is_customizable") == True:
            print(f"  {C.OK}[PASS]{C.END} is_customizable = True")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} is_customizable nao foi True")
            t.failed += 1
            t.failures.append("is_customizable field")
        if body.get("customization_options"):
            print(f"  {C.OK}[PASS]{C.END} customization_options presente")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} customization_options ausente")
            t.failed += 1
            t.failures.append("customization_options field")

    # Criar produto nao personalizavel
    t._print_subheader("Criar produto nao personalizavel")
    normal_product_payload = {
        "name": "Caneca Simples",
        "description": "Caneca simples sem opcoes",
        "attributes": {},
        "is_customizable": False,
        "customization_options": {},
        "base_price": 19.90,
    }
    r = requests.post(f"{t.api}/sellers/me/products", headers=headers, json=normal_product_payload)
    normal_product_id = None
    if t.assert_status("POST /sellers/me/products (nao personalizavel)", r, 201):
        normal_product_id = r.json().get("id")

    # Listar produtos e verificar campos
    if custom_product_id:
        r = requests.get(f"{t.api}/sellers/me/products", headers=headers)
        if t.assert_status("GET /sellers/me/products (verificar campos)", r, 200):
            body = r.json()
            items = body.get("items", [])
            custom_prod = next((p for p in items if p.get("id") == custom_product_id), None)
            if custom_prod:
                if custom_prod.get("is_customizable") == True and custom_prod.get("customization_options"):
                    print(f"  {C.OK}[PASS]{C.END} Lista retorna campos de customizacao")
                    t.passed += 1
                else:
                    print(f"  {C.FAIL}[FAIL]{C.END} Lista nao retorna campos de customizacao")
                    t.failed += 1
                    t.failures.append("lista customizacao fields")

        # Atualizar produto para personalizavel
        if normal_product_id:
            r = requests.patch(
                f"{t.api}/sellers/me/products/{normal_product_id}",
                headers=headers,
                json={
                    "is_customizable": True,
                    "customization_options": {"sizes": ["300ml"]}
                }
            )
            if t.assert_status("PATCH /sellers/me/products/{id} (tornar personalizavel)", r, 200):
                body = r.json()
                if body.get("is_customizable") == True:
                    print(f"  {C.OK}[PASS]{C.END} Atualizacao de is_customizable funcionou")
                    t.passed += 1
                else:
                    print(f"  {C.FAIL}[FAIL]{C.END} Atualizacao de is_customizable falhou")
                    t.failed += 1
                    t.failures.append("update is_customizable")


def test_orders_with_product_options(
    t: TestRunner,
    client_token: Optional[str],
    seller_user_id: Optional[str],
):
    """Testa criacao de pedidos com product_options."""
    t._print_header("ORDERS - PRODUCT OPTIONS")

    if not client_token or not seller_user_id:
        t.skip("Orders with product_options tests", "requer client_token e seller_user_id")
        return

    headers = {"Authorization": f"Bearer {client_token}"}

    # Criar pedido com product_options
    t._print_subheader("Criar pedido com product_options")
    payload = {
        "seller_id": seller_user_id,
        "title": "Caneca personalizada com opcoes",
        "description": "Quero uma caneca com as opcoes selecionadas",
        "product_type": "caneca 350ml",
        "product_options": {
            "size": "350ml",
            "material": "ceramic",
            "color": "white"
        },
        "quantity": 1,
    }
    r = requests.post(f"{t.api}/orders/", headers=headers, json=payload)
    order_id = None
    if t.assert_status("POST /orders (com product_options)", r, 201, show_body=True):
        body = r.json()
        order_id = body.get("id")
        if body.get("product_options") == payload["product_options"]:
            print(f"  {C.OK}[PASS]{C.END} product_options retornado corretamente")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} product_options nao retornado ou incorreto")
            t.failed += 1
            t.failures.append("product_options response")

    # Criar pedido sem product_options (opcional)
    payload_no_options = {
        "seller_id": seller_user_id,
        "title": "Caneca simples",
        "description": "Sem opcoes",
        "product_type": "caneca 250ml",
        "quantity": 1,
    }
    r = requests.post(f"{t.api}/orders/", headers=headers, json=payload_no_options)
    if t.assert_status("POST /orders (sem product_options)", r, 201):
        body = r.json()
        if body.get("product_options") == {}:
            print(f"  {C.OK}[PASS]{C.END} product_options default para {{}}")
            t.passed += 1
        else:
            print(f"  {C.WARN}[WARN]{C.END} product_options default: {body.get('product_options')}")

    # Verificar pedido com product_options
    if order_id:
        r = requests.get(f"{t.api}/orders/{order_id}", headers=headers)
        if t.assert_status("GET /orders/{id} (com product_options)", r, 200):
            body = r.json()
            if body.get("product_options"):
                print(f"  {C.OK}[PASS]{C.END} GET retorna product_options")
                t.passed += 1
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} GET nao retorna product_options")
                t.failed += 1
                t.failures.append("GET product_options")

        # Cancelar pedidos de teste
        r = requests.post(f"{t.api}/orders/{order_id}/cancel", headers=headers, json={"note": "limpeza"})
        t.assert_status("POST /cancel (limpeza)", r, 200)


# ============================================================
# Order / Iteration tests
# ============================================================

def test_orders_full_flow(
    t: TestRunner,
    client_token: Optional[str],
    seller_token: Optional[str],
    seller_user_id: Optional[str],
):
    """Fluxo completo: criar pedido, iterar com IA, aprovar, submeter, decisao do seller, status updates."""
    t._print_header("ORDERS - FLUXO COMPLETO (cliente + seller)")

    if not client_token or not seller_token or not seller_user_id:
        t.skip("Order tests", "requer client_token, seller_token e seller_user_id")
        return

    cli_h = {"Authorization": f"Bearer {client_token}"}
    sel_h = {"Authorization": f"Bearer {seller_token}"}

    # ----------------------------------------------------------
    # 1. Criar pedido (DRAFT)
    # ----------------------------------------------------------
    t._print_subheader("Criar pedido")
    payload = {
        "seller_id": seller_user_id,
        "title": "Caneca personalizada do meu gato",
        "description": "Gostaria de uma caneca com uma ilustracao do meu gato laranja deitado em um livro",
        "product_type": "caneca 250ml branca",
        "quantity": 2,
    }
    r = requests.post(f"{t.api}/orders/", headers=cli_h, json=payload)
    order_id = None
    if t.assert_status("POST /orders (criar DRAFT)", r, 201, show_body=True):
        body = r.json()
        order_id = body.get("id")
        if body.get("status") != "draft":
            print(f"  {C.FAIL}[FAIL]{C.END} status inicial deveria ser draft")
            t.failed += 1
            t.failures.append("status inicial != draft")

    if not order_id:
        t.skip("Restante do fluxo de orders", "falha ao criar pedido")
        return

    # Pedido com seller invalido
    bad = {**payload, "seller_id": "00000000-0000-0000-0000-000000000000"}
    r = requests.post(f"{t.api}/orders/", headers=cli_h, json=bad)
    t.assert_status("POST /orders (seller inexistente)", r, 404)

    # ----------------------------------------------------------
    # 2. Listar pedidos do cliente
    # ----------------------------------------------------------
    t._print_subheader("Listar pedidos")
    r = requests.get(f"{t.api}/orders/me", headers=cli_h)
    t.assert_status("GET /orders/me", r, 200)
    if r.status_code == 200:
        if r.json().get("total", 0) < 1:
            print(f"  {C.WARN}[WARN]{C.END} lista vazia apos criar pedido")

    # Filtro por status
    r = requests.get(f"{t.api}/orders/me", headers=cli_h, params={"status": "draft"})
    t.assert_status("GET /orders/me?status=draft", r, 200)

    # GET detalhe
    r = requests.get(f"{t.api}/orders/{order_id}", headers=cli_h)
    t.assert_status("GET /orders/{id}", r, 200)

    # GET sem token -> 401
    r = requests.get(f"{t.api}/orders/{order_id}")
    t.assert_status("GET /orders/{id} (sem token)", r, 401)

    # ----------------------------------------------------------
    # 3. PATCH pedido em DRAFT
    # ----------------------------------------------------------
    r = requests.patch(
        f"{t.api}/orders/{order_id}",
        headers=cli_h,
        json={"quantity": 3},
    )
    t.assert_status("PATCH /orders/{id}", r, 200)

    r = requests.patch(f"{t.api}/orders/{order_id}", headers=cli_h, json={})
    t.assert_status("PATCH /orders/{id} (vazio)", r, 400)

    # ----------------------------------------------------------
    # 4. Submit sem iteracao aprovada -> 400
    # ----------------------------------------------------------
    r = requests.post(f"{t.api}/orders/{order_id}/submit", headers=cli_h)
    t.assert_status("POST /submit (sem iteracao aprovada)", r, 400)

    # ----------------------------------------------------------
    # 5. Criar iteracoes com IA (placeholder verde)
    # ----------------------------------------------------------
    t._print_subheader("Iteracoes com IA")
    iter_ids = []
    descriptions = [
        "Estilo aquarela com cores pasteis",
        "Estilo cartoon, fundo branco",
        "Estilo realista, gato dormindo",
    ]
    for i, desc in enumerate(descriptions, 1):
        r = requests.post(
            f"{t.api}/orders/{order_id}/iterations",
            headers=cli_h,
            json={"description": desc},
        )
        if t.assert_status(f"POST iteracao v{i}", r, 201):
            body = r.json()
            iter_ids.append(body.get("id"))
            # Verifica que tem image_url e que e baixavel
            if body.get("status") != "ready":
                print(f"  {C.WARN}[WARN]{C.END} status iteracao={body.get('status')}, esperado 'ready'")
            if body.get("image_url"):
                _verify_image_url(t, f"download iter v{i}", body["image_url"], t.base_url)
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} iteracao v{i} sem image_url")
                t.failed += 1
                t.failures.append(f"iteracao v{i} sem image_url")
            if body.get("version") != i:
                print(f"  {C.WARN}[WARN]{C.END} version={body.get('version')}, esperado {i}")

    # Listar iteracoes
    r = requests.get(f"{t.api}/orders/{order_id}/iterations", headers=cli_h)
    if t.assert_status("GET /iterations", r, 200):
        data = r.json()
        if len(data) != len(iter_ids):
            print(f"  {C.WARN}[WARN]{C.END} esperava {len(iter_ids)} iteracoes, recebeu {len(data)}")

    # Iteracao com descricao curta -> 422
    r = requests.post(
        f"{t.api}/orders/{order_id}/iterations",
        headers=cli_h,
        json={"description": "oi"},
    )
    t.assert_status("POST iteracao (descricao curta)", r, 422)

    # ----------------------------------------------------------
    # 6. Aprovar iteracao
    # ----------------------------------------------------------
    if len(iter_ids) >= 2:
        # Aprova a primeira
        r = requests.post(
            f"{t.api}/orders/{order_id}/approve-iteration/{iter_ids[0]}",
            headers=cli_h,
        )
        if t.assert_status("POST approve-iteration (1a)", r, 200):
            body = r.json()
            if body.get("approved_iteration_id") != iter_ids[0]:
                print(f"  {C.FAIL}[FAIL]{C.END} approved_iteration_id nao foi setado")
                t.failed += 1
                t.failures.append("approved_iteration_id nao setado")

        # Trocar aprovacao para a segunda
        r = requests.post(
            f"{t.api}/orders/{order_id}/approve-iteration/{iter_ids[1]}",
            headers=cli_h,
        )
        if t.assert_status("POST approve-iteration (trocar para 2a)", r, 200):
            body = r.json()
            iters = body.get("iterations", [])
            approved_count = sum(1 for it in iters if it.get("status") == "approved")
            if approved_count == 1:
                print(f"  {C.OK}[PASS]{C.END} apenas 1 iteracao com status=approved")
                t.passed += 1
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} esperava 1 approved, recebeu {approved_count}")
                t.failed += 1
                t.failures.append("multiplas iteracoes approved")

    # Aprovar iteracao inexistente
    r = requests.post(
        f"{t.api}/orders/{order_id}/approve-iteration/00000000-0000-0000-0000-000000000000",
        headers=cli_h,
    )
    t.assert_status("POST approve-iteration (inexistente)", r, 404)

    # ----------------------------------------------------------
    # 7. Permissao: client nao pode ver pedido de outro cliente
    # ----------------------------------------------------------
    t._print_subheader("Permissoes")
    # Seller pode ver (e o seller atribuido)
    r = requests.get(f"{t.api}/orders/{order_id}", headers=sel_h)
    t.assert_status("GET /orders/{id} (como seller atribuido)", r, 200)

    # Seller nao pode editar
    r = requests.patch(f"{t.api}/orders/{order_id}", headers=sel_h, json={"quantity": 99})
    t.assert_status("PATCH /orders/{id} (seller tenta editar)", r, 403)

    # Seller nao pode iterar
    r = requests.post(
        f"{t.api}/orders/{order_id}/iterations",
        headers=sel_h,
        json={"description": "tentativa do seller"},
    )
    t.assert_status("POST iteracao (seller tenta)", r, 403)

    # ----------------------------------------------------------
    # 8. Submit ao seller (DRAFT -> IN_ANALYSIS)
    # ----------------------------------------------------------
    t._print_subheader("Submit -> Seller")
    r = requests.post(f"{t.api}/orders/{order_id}/submit", headers=cli_h)
    if t.assert_status("POST /submit", r, 200):
        if r.json().get("status") != "in_analysis":
            print(f"  {C.FAIL}[FAIL]{C.END} status apos submit != in_analysis")
            t.failed += 1
            t.failures.append("status apos submit")

    # Submit duas vezes -> 409
    r = requests.post(f"{t.api}/orders/{order_id}/submit", headers=cli_h)
    t.assert_status("POST /submit (ja submetido)", r, 409)

    # PATCH apos submit -> 409
    r = requests.patch(f"{t.api}/orders/{order_id}", headers=cli_h, json={"quantity": 5})
    t.assert_status("PATCH /orders/{id} (apos submit)", r, 409)

    # Iteracao apos submit -> 409
    r = requests.post(
        f"{t.api}/orders/{order_id}/iterations",
        headers=cli_h,
        json={"description": "nova ideia"},
    )
    t.assert_status("POST iteracao (apos submit)", r, 409)

    # ----------------------------------------------------------
    # 9. Seller lista pedidos recebidos
    # ----------------------------------------------------------
    t._print_subheader("Seller acoes")
    r = requests.get(f"{t.api}/sellers/me/orders/", headers=sel_h)
    if t.assert_status("GET /sellers/me/orders/", r, 200):
        if r.json().get("total", 0) < 1:
            print(f"  {C.WARN}[WARN]{C.END} seller nao ve o pedido recebido")

    r = requests.get(f"{t.api}/sellers/me/orders/", headers=sel_h, params={"status": "in_analysis"})
    t.assert_status("GET /sellers/me/orders/?status=in_analysis", r, 200)

    # ----------------------------------------------------------
    # 10. Seller decide: aceita
    # ----------------------------------------------------------
    r = requests.post(
        f"{t.api}/orders/{order_id}/seller-decision",
        headers=sel_h,
        json={"accept": True, "note": "Posso fazer em 5 dias", "estimated_price": 89.90},
    )
    if t.assert_status("POST seller-decision (aceitar)", r, 200):
        body = r.json()
        if body.get("status") != "approved":
            print(f"  {C.FAIL}[FAIL]{C.END} status pos-aceite != approved")
            t.failed += 1
            t.failures.append("status pos-aceite")
        if str(body.get("estimated_price")) not in ("89.90", "89.9"):
            print(f"  {C.WARN}[WARN]{C.END} estimated_price={body.get('estimated_price')}")

    # Decisao de novo -> 409
    r = requests.post(
        f"{t.api}/orders/{order_id}/seller-decision",
        headers=sel_h,
        json={"accept": True},
    )
    t.assert_status("POST seller-decision (ja aceito)", r, 409)

    # ----------------------------------------------------------
    # 11. Status: APPROVED -> IN_PRODUCTION -> COMPLETED
    # ----------------------------------------------------------
    r = requests.patch(
        f"{t.api}/orders/{order_id}/status",
        headers=sel_h,
        json={"status": "completed"},
    )
    t.assert_status("PATCH status APPROVED->COMPLETED (skip producao)", r, 409)

    r = requests.patch(
        f"{t.api}/orders/{order_id}/status",
        headers=sel_h,
        json={"status": "in_production", "note": "Iniciei a producao"},
    )
    t.assert_status("PATCH status -> in_production", r, 200)

    r = requests.patch(
        f"{t.api}/orders/{order_id}/status",
        headers=sel_h,
        json={"status": "completed", "note": "Pronto para entrega"},
    )
    if t.assert_status("PATCH status -> completed", r, 200):
        body = r.json()
        if body.get("status") != "completed":
            print(f"  {C.FAIL}[FAIL]{C.END} status final != completed")
            t.failed += 1
            t.failures.append("status final")
        if not body.get("completed_at"):
            print(f"  {C.WARN}[WARN]{C.END} completed_at nao preenchido")

    # PATCH apos completed -> 409
    r = requests.patch(
        f"{t.api}/orders/{order_id}/status",
        headers=sel_h,
        json={"status": "in_production"},
    )
    t.assert_status("PATCH status (apos completed)", r, 409)

    # ----------------------------------------------------------
    # 12. Cancelamento (em outro pedido novo)
    # ----------------------------------------------------------
    t._print_subheader("Cancelamento")
    r = requests.post(
        f"{t.api}/orders/",
        headers=cli_h,
        json={**payload, "title": "Pedido pra cancelar"},
    )
    if r.status_code == 201:
        cancel_id = r.json().get("id")
        r = requests.post(
            f"{t.api}/orders/{cancel_id}/cancel",
            headers=cli_h,
            json={"note": "Mudei de ideia"},
        )
        if t.assert_status("POST /cancel (em DRAFT)", r, 200):
            if r.json().get("status") != "cancelled":
                print(f"  {C.FAIL}[FAIL]{C.END} status nao cancelou")
                t.failed += 1
                t.failures.append("cancelamento")

        # Cancelar de novo -> 409
        r = requests.post(
            f"{t.api}/orders/{cancel_id}/cancel",
            headers=cli_h,
            json={},
        )
        t.assert_status("POST /cancel (ja cancelado)", r, 409)


def test_sellers_public_with_data(t: TestRunner, seller_id: Optional[str]):
    t._print_header("SELLERS PUBLIC - COM DADOS")

    if not seller_id:
        t.skip("Sellers public com dados", "seller_id nao disponivel")
        return

    # Lista deve ter ao menos 1
    r = requests.get(f"{t.api}/sellers/")
    if t.assert_status("GET /sellers/ (com dados)", r, 200):
        body = r.json()
        if body.get("total", 0) < 1:
            print(f"  {C.WARN}[WARN]{C.END} Lista vazia mesmo com seller criado")

    # Filtro por categoria
    r = requests.get(f"{t.api}/sellers/", params={"category": "mug"})
    t.assert_status("GET /sellers/?category=mug", r, 200)

    # Busca
    r = requests.get(f"{t.api}/sellers/", params={"search": "Loja Teste"})
    t.assert_status("GET /sellers/?search=Loja", r, 200)

    # Detalhe por ID
    r = requests.get(f"{t.api}/sellers/{seller_id}")
    if t.assert_status("GET /sellers/{id}", r, 200):
        slug = r.json().get("slug")

        # Detalhe por slug
        if slug:
            r = requests.get(f"{t.api}/sellers/by-slug/{slug}")
            t.assert_status(f"GET /sellers/by-slug/{slug}", r, 200)

    # Lista de produtos
    r = requests.get(f"{t.api}/sellers/{seller_id}/products")
    t.assert_status("GET /sellers/{id}/products", r, 200)


def test_logout_flow(t: TestRunner, tokens: Dict[str, Dict[str, str]]):
    t._print_header("AUTH - LOGOUT")

    if "client" not in tokens:
        t.skip("Logout test", "tokens nao disponiveis")
        return

    access = tokens["client"]["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    r = requests.post(f"{t.api}/auth/logout", headers=headers)
    t.assert_status("POST /auth/logout", r, 200)

    # Apos logout, /me deve falhar
    r = requests.get(f"{t.api}/auth/me", headers=headers)
    t.assert_status("GET /auth/me (apos logout)", r, 401)


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Testes E2E da API MeraKia")
    parser.add_argument("--base-url", default="http://localhost:8000", help="URL base da API")
    args = parser.parse_args()

    print(f"{C.BOLD}{C.INFO}")
    print("MeraKia API - Test Suite")
    print(f"Base URL: {args.base_url}{C.END}")

    # Verificar se a API esta no ar
    try:
        r = requests.get(f"{args.base_url}/health", timeout=3)
        if r.status_code != 200:
            print(f"{C.FAIL}API nao respondeu /health corretamente: {r.status_code}{C.END}")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"{C.FAIL}Nao foi possivel conectar em {args.base_url}: {e}{C.END}")
        sys.exit(1)

    t = TestRunner(args.base_url)

    # 1. Health
    test_health_and_root(t)

    # 2. Sellers public sem dados (antes de criar)
    test_sellers_public_empty(t)

    # 3. Auth - Register
    users = test_auth_register(t)

    # 4. Auth - Login
    tokens = test_auth_login(t, users)

    # 5. Auth - /me, /refresh
    test_auth_me_and_refresh(t, tokens)

    # 6. Sellers /me sem permissao
    client_access = tokens.get("client", {}).get("access_token")
    test_sellers_me_unauthorized(t, client_access)

    # 7. Email verification (tenta verificar de verdade via DB)
    seller_email = users.get("seller", {}).get("email", "")
    test_email_verification(t, tokens, seller_email)

    # Verificar se o email do seller foi verificado
    code = get_verification_code_from_db(seller_email)
    email_verified = code is None  # se foi removido do DB, foi verificado

    # 8. Sellers /me - fluxo completo
    seller_token = tokens.get("seller", {}).get("access_token")
    result = test_sellers_me_full_flow(t, seller_token, email_verified)
    if result:
        seller_id, product_id = result
    else:
        seller_id, product_id = None, None

    # 9. Customizable products test
    test_customizable_products(t, seller_token)

    # 10. User avatar
    test_user_avatar(t, client_access)

    # 11. Seller logo & banner
    test_seller_logo_banner(t, seller_token, seller_id)

    # 12. Product images
    test_product_images(t, seller_token, product_id)

    # 13. Public endpoints com URLs de imagens
    test_public_image_urls(t, seller_id, product_id)

    # 14. Sellers public com dados
    test_sellers_public_with_data(t, seller_id)

    # 15. Orders with product_options
    seller_user_id = users.get("seller", {}).get("id")
    test_orders_with_product_options(t, client_access, seller_user_id)

    # 16. Orders (cliente cria, itera com IA, aprova, submete; seller decide e atualiza)
    test_orders_full_flow(t, client_access, seller_token, seller_user_id)

    # 17. Cart flow
    test_cart_flow(t, client_access, seller_token, product_id, seller_user_id)

    # 18. Logout (no final pra nao invalidar tokens cedo)
    test_logout_flow(t, tokens)

    sys.exit(t.summary())


def test_cart_flow(
    t: TestRunner,
    client_token: Optional[str],
    seller_token: Optional[str],
    product_id: Optional[str],
    seller_user_id: Optional[str],
):
    """Testa fluxo completo do carrinho."""
    t._print_header("CART FLOW")

    if not client_token or not seller_token or not product_id or not seller_user_id:
        t.skip("Cart flow tests", "requer client_token, seller_token, product_id e seller_user_id")
        return

    headers = {"Authorization": f"Bearer {client_token}"}

    # 1. GET /cart - carrinho vazio
    t._print_subheader("GET /cart - carrinho vazio")
    r = requests.get(f"{t.api}/cart/", headers=headers)
    if t.assert_status("GET /cart (vazio)", r, 200):
        body = r.json()
        if body.get("total_items") == 0:
            print(f"  {C.OK}[PASS]{C.END} Carrinho vazio")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Carrinho deveria estar vazio")
            t.failed += 1

    # 2. POST /cart/items - adicionar produto não personalizável
    t._print_subheader("POST /cart/items - adicionar produto")
    payload = {
        "product_spec_id": product_id,
        "quantity": 2,
    }
    r = requests.post(f"{t.api}/cart/items", headers=headers, json=payload)
    cart_item_id = None
    if t.assert_status("POST /cart/items", r, 201):
        body = r.json()
        cart_item_id = body.get("id")
        if body.get("quantity") == 2 and body.get("name"):
            print(f"  {C.OK}[PASS]{C.END} Item adicionado ao carrinho")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Item adicionado mas dados incorretos")
            t.failed += 1

    # 3. GET /cart - verificar item adicionado
    t._print_subheader("GET /cart - verificar item")
    r = requests.get(f"{t.api}/cart/", headers=headers)
    if t.assert_status("GET /cart (com item)", r, 200):
        body = r.json()
        if body.get("total_items") == 2 and len(body.get("items", [])) == 1:
            print(f"  {C.OK}[PASS]{C.END} Carrinho com 1 item (quantidade 2)")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Carrinho com dados incorretos")
            t.failed += 1

    # 4. PATCH /cart/items/{id} - atualizar quantidade
    if cart_item_id:
        t._print_subheader("PATCH /cart/items/{id} - atualizar quantidade")
        payload = {"quantity": 3}
        r = requests.patch(f"{t.api}/cart/items/{cart_item_id}", headers=headers, json=payload)
        if t.assert_status("PATCH /cart/items/{id}", r, 200):
            body = r.json()
            if body.get("quantity") == 3:
                print(f"  {C.OK}[PASS]{C.END} Quantidade atualizada para 3")
                t.passed += 1
            else:
                print(f"  {C.FAIL}[FAIL]{C.END} Quantidade não atualizada corretamente")
                t.failed += 1

    # 5. GET /cart - verificar nova quantidade
    t._print_subheader("GET /cart - verificar nova quantidade")
    r = requests.get(f"{t.api}/cart/", headers=headers)
    if t.assert_status("GET /cart (atualizado)", r, 200):
        body = r.json()
        if body.get("total_items") == 3:
            print(f"  {C.OK}[PASS]{C.END} Total de itens atualizado para 3")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Total de itens incorreto")
            t.failed += 1

    # 6. DELETE /cart/items/{id} - remover item
    if cart_item_id:
        t._print_subheader("DELETE /cart/items/{id} - remover item")
        r = requests.delete(f"{t.api}/cart/items/{cart_item_id}", headers=headers)
        if t.assert_status("DELETE /cart/items/{id}", r, 204):
            print(f"  {C.OK}[PASS]{C.END} Item removido do carrinho")
            t.passed += 1

    # 7. GET /cart - carrinho vazio novamente
    t._print_subheader("GET /cart - carrinho vazio após remoção")
    r = requests.get(f"{t.api}/cart/", headers=headers)
    if t.assert_status("GET /cart (vazio após remoção)", r, 200):
        body = r.json()
        if body.get("total_items") == 0:
            print(f"  {C.OK}[PASS]{C.END} Carrinho vazio após remoção")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Carrinho deveria estar vazio")
            t.failed += 1

    # 8. POST /cart/items - adicionar item novamente para checkout
    t._print_subheader("POST /cart/items - preparar para checkout")
    payload = {
        "product_spec_id": product_id,
        "quantity": 1,
    }
    r = requests.post(f"{t.api}/cart/items", headers=headers, json=payload)
    if t.assert_status("POST /cart/items (para checkout)", r, 201):
        print(f"  {C.OK}[PASS]{C.END} Item adicionado para checkout")
        t.passed += 1

    # 9. POST /cart/checkout - fazer checkout
    t._print_subheader("POST /cart/checkout")
    payload = {
        "seller_ids": [seller_user_id],
        "notes": "Teste de checkout",
    }
    r = requests.post(f"{t.api}/cart/checkout", headers=headers, json=payload)
    if t.assert_status("POST /cart/checkout", r, 200):
        body = r.json()
        if body.get("total_amount") and body.get("message"):
            print(f"  {C.OK}[PASS]{C.END} Checkout realizado com sucesso")
            t.passed += 1
        else:
            print(f"  {C.FAIL}[FAIL]{C.END} Response incompleta")
            t.failed += 1

    # 10. Validações - adicionar sem product_spec_id nem order_id
    t._print_subheader("Validações - campos obrigatórios")
    payload = {"quantity": 1}
    r = requests.post(f"{t.api}/cart/items", headers=headers, json=payload)
    t.assert_status("POST /cart/items (sem product_spec_id/order_id)", r, 400)

    # 11. Validações - adicionar com ambos product_spec_id e order_id
    t._print_subheader("Validações - ambos os campos")
    payload = {
        "product_spec_id": product_id,
        "order_id": "00000000-0000-0000-0000-000000000000",
        "quantity": 1,
    }
    r = requests.post(f"{t.api}/cart/items", headers=headers, json=payload)
    t.assert_status("POST /cart/items (ambos os campos)", r, 400)


if __name__ == "__main__":
    main()
