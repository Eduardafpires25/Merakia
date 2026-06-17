# MeraKia

MeraKia é uma plataforma de marketplace para produtos personalizados e regulares, com integração de IA para geração de imagens e sugestões de produtos. A plataforma permite que vendedores criem suas lojas, cadastrem produtos e recebam pedidos personalizados ou regulares de clientes.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack Tecnológico](#stack-tecnológico)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Executando Localmente](#executando-localmente)
- [Docker](#docker)
- [API Endpoints](#api-endpoints)
- [Testes](#testes)
- [Deploy](#deploy)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Autores](#autores)

---

## 🎯 Visão Geral

MeraKia é uma plataforma completa de e-commerce focada em produtos personalizados, com as seguintes características principais:

- **Marketplace de produtos personalizados**: Clientes podem solicitar produtos personalizados com iterações de IA
- **Produtos regulares**: Vendedores podem oferecer produtos regulares com compra direta
- **Gestão de pedidos**: Sistema completo de gerenciamento de pedidos com múltiplos status
- **Integração com IA**: Geração de imagens usando OpenAI DALL-E
- **Sistema de carrinho**: Carrinho de compras para produtos regulares
- **Autenticação segura**: Sistema de autenticação com JWT e verificação de email

---

## ✨ Funcionalidades

### Para Clientes

- **Registro e Login**: Criação de conta com verificação de email
- **Explorar Lojas**: Navegação por lojas e produtos
- **Pedidos Personalizados**: Solicitação de produtos personalizados com iterações de IA
- **Compra de Produtos Regulares**: Adição ao carrinho e checkout
- **Gerenciamento de Pedidos**: Acompanhamento do status dos pedidos
- **Confirmação de Entrega**: Confirmação de recebimento de pedidos
- **Avaliação de Pedidos**: Marcar pedidos como concluídos

### Para Vendedores

- **Criação de Loja**: Configuração de perfil de vendedor
- **Gestão de Produtos**: Cadastro e edição de produtos
- **Gerenciamento de Pedidos**: Aceitação, rejeição e atualização de status
- **Iterações de IA**: Geração de imagens para pedidos personalizados
- **Dashboard**: Visão geral de vendas e pedidos
- **Filtros de Pedidos**: Filtragem por status e tipo de pedido

### Funcionalidades Técnicas

- **API RESTful**: API completa com FastAPI
- **Validação de Dados**: Validação com Pydantic
- **Banco de Dados Relacional**: PostgreSQL com SQLAlchemy ORM
- **Migrações**: Gerenciamento de migrations com Alembic
- **Upload de Imagens**: Integração com S3 ou armazenamento local
- **Testes Automatizados**: Testes unitários e de integração com pytest
- **Coverage de Testes**: Relatórios de coverage com pytest-cov

---

## 🛠 Stack Tecnológico

### Backend

- **Python 3.12+**: Linguagem principal
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para banco de dados
- **Alembic**: Gerenciamento de migrations
- **Pydantic**: Validação de dados
- **Pydantic Settings**: Gerenciamento de configurações
- **python-jose**: Autenticação JWT
- **bcrypt**: Hash de senhas
- **zxcvbn**: Verificação de força de senhas
- **OpenAI**: API para geração de imagens
- **boto3**: Cliente AWS S3
- **python-multipart**: Upload de arquivos
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **psycopg2-binary**: Driver PostgreSQL
- **requests**: Cliente HTTP

### Frontend

- **React**: Biblioteca UI
- **TypeScript**: Tipagem estática
- **Vite**: Build tool e dev server
- **React Router**: Roteamento
- **TailwindCSS**: Estilização
- **Lucide React**: Ícones
- **Axios**: Cliente HTTP

### Banco de Dados

- **PostgreSQL**: Banco de dados relacional

### DevOps

- **Docker**: Containerização
- **Docker Compose**: Orquestração de containers
- **Git**: Controle de versão

### Testes

- **pytest**: Framework de testes
- **pytest-cov**: Coverage de testes
- **pytest-asyncio**: Testes assíncronos
- **httpx**: Cliente HTTP assíncrono

---

## 📁 Estrutura do Projeto

```
MeraKia/
├── alembic/                          # Migrations do banco de dados
│   ├── versions/                     # Arquivos de migração
│   └── env.py                        # Configuração do Alembic
├── config/                           # Configurações
│   ├── logger.py                     # Configuração de logging
│   └── settings.py                   # Configurações da aplicação
├── scripts/                          # Scripts utilitários
├── src/                              # Código fonte
│   ├── api/                          # Backend FastAPI
│   │   ├── ai/                       # Integração com IA
│   │   │   ├── __init__.py
│   │   │   └── client.py             # Cliente OpenAI
│   │   ├── dependencies/             # Dependências da API
│   │   │   └── auth.py               # Dependências de autenticação
│   │   ├── main.py                   # Entry point da API
│   │   ├── models/                   # Modelos Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Modelos de autenticação
│   │   │   ├── cart.py               # Modelos de carrinho
│   │   │   ├── order.py              # Modelos de pedidos
│   │   │   └── seller.py             # Modelos de vendedores
│   │   ├── repositories/             # Repositories (acesso a dados)
│   │   │   ├── __init__.py
│   │   │   ├── auth_repository.py    # Repository de autenticação
│   │   │   ├── cart_repository.py    # Repository de carrinho
│   │   │   ├── order_repository.py   # Repository de pedidos
│   │   │   └── seller_repository.py  # Repository de vendedores
│   │   ├── routes/                   # Rotas da API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Rotas de autenticação
│   │   │   ├── cart.py               # Rotas de carrinho
│   │   │   ├── orders.py             # Rotas de pedidos
│   │   │   └── sellers.py            # Rotas de vendedores
│   │   └── services/                 # Serviços de negócio
│   │       ├── __init__.py
│   │       └── email_service.py      # Serviço de email
│   ├── database/                     # Camada de banco de dados
│   │   ├── models/                   # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Modelo base
│   │   │   ├── cart.py               # Modelo de carrinho
│   │   │   ├── order.py              # Modelo de pedido
│   │   │   ├── project_iteration.py # Modelo de iteração
│   │   │   ├── product_spec.py       # Modelo de produto
│   │   │   ├── seller.py             # Modelo de vendedor
│   │   │   └── user.py               # Modelo de usuário
│   │   ├── enums/                     # Enums
│   │   │   ├── __init__.py
│   │   │   ├── iteration_status.py   # Status de iteração
│   │   │   ├── order_status.py       # Status de pedido
│   │   │   ├── seller_category.py    # Categorias de vendedor
│   │   │   └── user_role.py          # Papéis de usuário
│   │   └── session.py                # Sessão do banco de dados
│   ├── storage/                      # Serviço de armazenamento
│   │   ├── __init__.py
│   │   ├── image_service.py          # Serviço de imagens
│   │   └── local_storage.py         # Armazenamento local
│   └── web/                          # Frontend React
│       ├── public/                   # Arquivos estáticos
│       ├── src/
│       │   ├── components/           # Componentes React
│       │   │   ├── CreateOrderModal.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Toast.tsx
│       │   │   └── Tooltip.tsx
│       │   ├── hooks/                 # Custom hooks
│       │   │   ├── useAuth.ts
│       │   │   ├── useCart.ts
│       │   │   └── useOrders.ts
│       │   ├── lib/                   # Utilitários
│       │   │   ├── api.ts             # Cliente API
│       │   │   └── auth.ts            # Funções de autenticação
│       │   ├── pages/                 # Páginas
│       │   │   ├── Cart.tsx
│       │   │   ├── Login.tsx
│       │   │   ├── MyOrders.tsx
│       │   │   ├── OrderDetail.tsx
│       │   │   ├── Register.tsx
│       │   │   ├── SellerDashboard.tsx
│       │   │   ├── SellerDetail.tsx
│       │   │   └── Sellers.tsx
│       │   ├── types/                 # Tipos TypeScript
│       │   │   └── api.ts
│       │   ├── App.tsx
│       │   ├── index.css
│       │   └── main.tsx
│       ├── index.html
│       ├── package.json
│       ├── tailwind.config.js
│       └── vite.config.ts
├── tests/                            # Testes
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures compartilhadas
│   ├── test_cart_routes.py            # Testes de rotas de carrinho
│   ├── test_database_models.py        # Testes de modelos de banco de dados
│   ├── test_models.py                 # Testes de modelos Pydantic
│   ├── test_orders_routes.py          # Testes de rotas de pedidos
│   ├── test_repositories.py           # Testes de repositories
│   └── test_sellers_routes.py         # Testes de rotas de vendedores
├── .dockerignore
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore
├── alembic.ini                        # Configuração do Alembic
├── docker-compose.yml                 # Compose Docker
├── Dockerfile.api                    # Dockerfile da API
├── Dockerfile.web                    # Dockerfile do Frontend
├── pyproject.toml                    # Configuração do projeto Python
├── pytest.ini                        # Configuração do pytest
├── README.md
└── uv.lock                           # Lock file do uv
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.12 ou superior
- Node.js 18 ou superior
- PostgreSQL 14 ou superior
- Docker e Docker Compose (opcional)

### Backend

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/MeraKia.git
cd MeraKia

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -e .

# Instale as dependências de teste
pip install -e ".[test]"
```

### Frontend

```bash
cd src/web
npm install
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado em `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/merakia

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@merakia.com
EMAIL_FROM_NAME=MeraKia

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3 (opcional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Storage
STORAGE_TYPE=local  # ou 's3'
LOCAL_STORAGE_PATH=./storage/uploads

# Frontend
VITE_API_URL=http://localhost:8000
```

### Banco de Dados

```bash
# Execute as migrations
alembic upgrade head
```

---

## 🏃 Executando Localmente

### Backend

```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Execute a API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`

### Frontend

```bash
cd src/web
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

### Acessando a Documentação da API

Com o backend rodando, acesse:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🐳 Docker

### Usando Docker Compose

```bash
# Construa e inicie todos os serviços
docker-compose up --build

# Apenas inicie os serviços
docker-compose up

# Pare os serviços
docker-compose down

# Remova volumes e redes
docker-compose down -v
```

Serviços incluídos:

- **api**: Backend FastAPI
- **web**: Frontend React
- **db**: PostgreSQL

---

## 📡 API Endpoints

### Autenticação

- `POST /auth/register` - Registro de usuário
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Obter usuário atual
- `POST /auth/verify-email/{token}` - Verificar email
- `POST /auth/resend-verification` - Reenviar email de verificação
- `POST /auth/forgot-password` - Solicitar recuperação de senha
- `POST /auth/reset-password` - Redefinir senha

### Vendedores

- `POST /sellers/me/profile` - Criar perfil de vendedor
- `GET /sellers/me/profile` - Obter perfil do vendedor
- `PATCH /sellers/me/profile` - Atualizar perfil
- `POST /sellers/me/profile/logo` - Upload de logo
- `POST /sellers/me/profile/banner` - Upload de banner
- `GET /sellers/{id}` - Obter vendedor por ID
- `GET /sellers/by-slug/{slug}` - Obter vendedor por slug
- `GET /sellers/` - Listar vendedores
- `POST /sellers/me/products` - Criar produto
- `GET /sellers/me/products` - Listar produtos do vendedor
- `PATCH /sellers/me/products/{id}` - Atualizar produto
- `DELETE /sellers/me/products/{id}` - Deletar produto
- `POST /sellers/me/products/{id}/cover` - Upload de capa de produto

### Pedidos

- `POST /orders/` - Criar pedido
- `GET /orders/` - Listar pedidos do usuário
- `GET /orders/{id}` - Obter pedido por ID
- `PATCH /orders/{id}` - Atualizar pedido
- `PATCH /orders/{id}/status` - Atualizar status
- `POST /orders/{id}/approve` - Aprovar pedido
- `POST /orders/{id}/reject` - Rejeitar pedido
- `POST /orders/{id}/cancel` - Cancelar pedido
- `POST /orders/{id}/confirm-delivery` - Confirmar entrega
- `POST /orders/{id}/complete` - Completar pedido
- `POST /orders/{id}/iterations` - Criar iteração
- `GET /orders/{id}/iterations` - Listar iterações
- `POST /orders/{id}/iterations/{iteration_id}/approve` - Aprovar iteração

### Carrinho

- `GET /cart` - Obter carrinho
- `POST /cart/items` - Adicionar item ao carrinho
- `PATCH /cart/items/{id}` - Atualizar quantidade
- `DELETE /cart/items/{id}` - Remover item
- `DELETE /cart` - Limpar carrinho
- `POST /cart/checkout` - Checkout
- `GET /cart/total` - Obter total do carrinho

---

## 🧪 Testes

### Executar todos os testes

```bash
pytest
```

### Executar com coverage

```bash
pytest --cov=src/api --cov-report=html --cov-report=term-missing
```

### Executar testes específicos

```bash
# Testes de modelos
pytest tests/test_models.py

# Testes de rotas
pytest tests/test_orders_routes.py

# Testes de repositories
pytest tests/test_repositories.py
```

### Executar com verbose

```bash
pytest -v
```

### Relatório de Coverage

O relatório HTML será gerado em `htmlcov/index.html`

---

## 📦 Deploy

### Backend

#### Heroku

```bash
# Instale o Heroku CLI
heroku create merakia-api

# Defina as variáveis de ambiente
heroku config:set DATABASE_URL=your-database-url
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key

# Deploy
git push heroku main
```

#### Railway/Render

Siga as instruções do provedor para configurar as variáveis de ambiente e fazer o deploy.

### Frontend

#### Vercel/Netlify

1. Conecte seu repositório
2. Configure as variáveis de ambiente
3. Defina o diretório de build como `src/web`
4. Deploy automático

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

## 👥 Autores

- **Eduarda Fernandes Pires**
- **Igor Samuel Candido de Souza**

---

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através das issues do GitHub.

# MeraKia

MeraKia é uma plataforma de marketplace para produtos personalizados com integração de geração de imagens via IA. Vendedores criam lojas e cadastram produtos; clientes fazem pedidos personalizados e refinam o design em iterações com IA até aprovar a versão final.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack Tecnológico](#stack-tecnológico)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Executando com Docker](#executando-com-docker)
- [Executando Localmente](#executando-localmente)
- [API Endpoints](#api-endpoints)
- [Testes](#testes)
- [Contribuindo](#contribuindo)
- [Autores](#autores)

---

## 🎯 Visão Geral

MeraKia conecta clientes que desejam produtos personalizados com vendedores especializados. O diferencial é o fluxo de **iterações com IA**: após criar um pedido, o cliente descreve sua ideia e a IA (OpenAI gpt-image-2) gera uma imagem do produto. O cliente pode refinar a descrição e gerar novas versões até aprovar o design final.

**Fluxo principal:**
1. Vendedor cria loja e cadastra produtos personalizáveis
2. Cliente encontra a loja, abre pedido e descreve sua ideia
3. IA gera imagem do produto aplicando a personalização descrita
4. Cliente itera até aprovar — vendedor então produz e envia
5. Cliente confirma o recebimento e conclui o pedido

---

## ✨ Funcionalidades

### Para Clientes

- **Registro e Login** com verificação de email obrigatória
- **Explorar lojas e produtos** com busca e filtros por categoria
- **Pedidos personalizados** com iterações de geração de imagem por IA
- **Limite diário de iterações** configurável por usuário
- **Carrinho de compras** para produtos regulares com checkout
- **Acompanhamento de pedidos** com histórico de status
- **Confirmação de entrega** e conclusão de pedido
- **Perfil de usuário** com avatar e informações pessoais

### Para Vendedores

- **Criação e configuração de loja** com logo, banner e descrição
- **Gestão de produtos** com specs personalizáveis, preços e imagens de capa
- **Dashboard completo** com visão geral de pedidos por status
- **Aceitar/rejeitar pedidos** e atualizar status de produção/envio
- **Informações de envio** para entrega física dos pedidos
- **Filtros de pedidos** por status, tipo (personalizado/regular) e data

### Técnico

- API RESTful documentada via Swagger/ReDoc
- Autenticação JWT com refresh token
- Migrations automáticas via Alembic no startup
- Storage configurável: armazenamento local ou AWS S3 / DigitalOcean Spaces
- Modo placeholder para desenvolvimento (sem consumir créditos da OpenAI)
- Tratamento de erros da OpenAI (billing, moderação, permissão, timeout)
- Testes automatizados com pytest + coverage

---

## 🛠 Stack Tecnológico

### Backend

| Pacote | Uso |
|--------|-----|
| Python 3.12+ | Linguagem principal |
| FastAPI | Framework web |
| SQLAlchemy + Alembic | ORM e migrations |
| Pydantic + Pydantic Settings | Validação e configuração |
| python-jose + bcrypt | JWT e hash de senhas |
| openai | Geração de imagens (gpt-image-2) |
| boto3 | Storage S3 / DigitalOcean Spaces |
| psycopg2-binary | Driver PostgreSQL |
| uv | Gerenciamento de dependências |

### Frontend

| Pacote | Uso |
|--------|-----|
| React + TypeScript | UI e tipagem |
| Vite | Build tool e dev server |
| React Router | Roteamento SPA |
| TailwindCSS | Estilização |
| Lucide React | Ícones |
| Axios | Cliente HTTP |

### Infraestrutura

| Ferramenta | Uso |
|-----------|-----|
| PostgreSQL 16 | Banco de dados relacional |
| Docker + Docker Compose | Containerização e orquestração |

### Testes

| Pacote | Uso |
|--------|-----|
| pytest | Framework de testes |
| pytest-cov | Relatório de coverage |
| httpx | Cliente HTTP para testes de integração |

---

## 📁 Estrutura do Projeto

```
MeraKia/
├── alembic/                         # Migrations do banco de dados
│   └── versions/                    # Arquivos de migração gerados
├── config/
│   ├── logger.py                    # Configuração de logging estruturado
│   └── settings.py                  # Configurações via Pydantic BaseSettings
├── src/
│   ├── api/                         # Backend FastAPI
│   │   ├── ai/
│   │   │   ├── client.py            # Cliente OpenAI (geração de imagens)
│   │   │   ├── placeholders.py      # Gerador de placeholder para dev
│   │   │   ├── schemas.py           # Schemas de entrada/saída da IA
│   │   │   └── prompts/
│   │   │       └── image_generation.md  # Template de prompt
│   │   ├── dependencies/
│   │   │   └── auth.py              # Dependências de autenticação
│   │   ├── models/                  # Schemas Pydantic (request/response)
│   │   │   ├── auth.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── seller.py
│   │   ├── repositories/            # Acesso ao banco de dados
│   │   │   ├── auth_repository.py
│   │   │   ├── cart_repository.py
│   │   │   ├── order_repository.py
│   │   │   └── seller_repository.py
│   │   ├── routes/                  # Endpoints da API
│   │   │   ├── auth.py              # Login, registro, refresh
│   │   │   ├── cart.py              # Carrinho e checkout
│   │   │   ├── email_verification.py
│   │   │   ├── orders.py            # Pedidos e iterações de IA
│   │   │   ├── sellers_me.py        # Dashboard do vendedor
│   │   │   ├── sellers_public.py    # Lojas públicas
│   │   │   └── users_me.py          # Perfil e limite de iterações
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── email_service.py
│   │   │   └── iteration_service.py # Controle de limite diário de IA
│   │   └── main.py                  # Entry point da API
│   ├── database/
│   │   ├── models/                  # Modelos SQLAlchemy
│   │   │   ├── enums.py             # OrderStatus, IterationStatus, etc.
│   │   │   ├── order.py
│   │   │   ├── project_iteration.py
│   │   │   ├── seller.py
│   │   │   └── user.py
│   │   ├── migration.py             # Execução automática de migrations
│   │   └── session.py               # Sessão do banco de dados
│   ├── storage/
│   │   ├── image_service.py         # Serviço de upload de imagens
│   │   ├── local.py                 # Backend de storage local
│   │   └── s3.py                    # Backend S3 / Spaces / MinIO
│   └── web/                         # Frontend React
│       └── src/
│           ├── components/          # Header, Logo, Modal, Toast, etc.
│           ├── contexts/            # AuthContext, CartContext, IterationsContext
│           ├── hooks/               # useCart, useOrders, etc.
│           ├── lib/                 # api.ts (axios), auth.ts
│           └── pages/               # Home, Login, Register, OrderDetail,
│                                    # SellerDashboard, MyOrders, Cart, etc.
├── tests/                           # Testes automatizados
│   ├── conftest.py                  # Fixtures e setup
│   ├── test_cart_routes.py
│   ├── test_orders_routes.py
│   ├── test_repositories.py
│   └── test_sellers_routes.py
├── .env.example                     # Variáveis de ambiente documentadas
├── docker-compose.yml               # API + Web + PostgreSQL
├── pyproject.toml                   # Dependências Python (uv)
└── pytest.ini                       # Configuração do pytest
```

---

## � Executando com Docker

A forma mais simples de rodar o projeto. Requer apenas Docker e Docker Compose.

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas configurações. Para rodar localmente em modo desenvolvimento, os valores do exemplo já funcionam com `AI_PLACEHOLDER_MODE=true` (não consome créditos da OpenAI).

### 2. Subir os containers

```bash
docker compose up --build
```

Isso sobe três serviços:

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| `merakia-api` | `8000` | Backend FastAPI |
| `merakia-web` | `5173` | Frontend React (Vite dev) |
| `merakia-database` | `5432` | PostgreSQL 16 |

As migrations são executadas automaticamente no startup da API.

### 3. Acessar

- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Comandos úteis

```bash
# Parar os serviços
docker compose down

# Parar e remover volumes (reseta o banco)
docker compose down -v

# Ver logs da API
docker compose logs -f api
```

---

## 🚀 Executando Localmente

Requer Python 3.12+, Node.js 20+ e PostgreSQL rodando.

### Backend

```bash
# Clone o repositório

git clone https://github.com/Eduardafpires25/CraftAI
cd CraftAI


# Instale o uv (gerenciador de dependências)
pip install uv

# Instale as dependências
uv sync

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com POSTGRES_HOST=localhost e demais configurações

# Execute as migrations
uv run alembic upgrade head

# Inicie a API
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd src/web
npm install
npm run dev
```

---

## ⚙️ Configuração

Todas as variáveis estão documentadas em `.env.example`. As principais:

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `POSTGRES_*` | ✅ | Configurações do banco PostgreSQL |
| `SECRET_KEY` | ✅ | Chave JWT — use string aleatória longa em produção |
| `OPENAI_API_KEY` | ⚠️ | Obrigatório se `AI_PLACEHOLDER_MODE=false` |
| `AI_PLACEHOLDER_MODE` | — | `true` para dev (não chama OpenAI). Padrão: `true` |
| `AI_ITERATIONS_LIMIT_ENABLED` | — | Habilita limite diário por usuário. Padrão: `true` |
| `AI_ITERATIONS_DAILY_LIMIT` | — | Limite diário de iterações. Padrão: `5` |
| `STORAGE_BACKEND` | — | `local` ou `s3`. Padrão: `local` |
| `SMTP_*` | — | Opcional. Sem configurar, emails não são enviados |
| `S3_*` | ⚠️ | Obrigatório se `STORAGE_BACKEND=s3` |

---

## 📡 API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Autenticação — `/auth`

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/auth/register` | Registrar usuário |
| `POST` | `/auth/login` | Login (retorna access + refresh token) |
| `POST` | `/auth/refresh` | Renovar access token |
| `GET` | `/auth/me` | Dados do usuário autenticado |
| `POST` | `/auth/verify-email/{token}` | Verificar email |
| `POST` | `/auth/resend-verification` | Reenviar email de verificação |

### Usuário — `/users/me`

| Método | Rota | Descrição |
|--------|------|-----------|
| `PATCH` | `/users/me` | Atualizar perfil |
| `POST` | `/users/me/avatar` | Upload de avatar |
| `GET` | `/users/me/iterations-limit` | Limite de iterações do dia |

### Vendedores Públicos — `/sellers`

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/sellers` | Listar lojas |
| `GET` | `/sellers/{id}` | Detalhes de uma loja |
| `GET` | `/sellers/{id}/products` | Produtos de uma loja |

### Dashboard do Vendedor — `/sellers/me`

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/sellers/me/profile` | Criar perfil de vendedor |
| `GET` | `/sellers/me/profile` | Obter perfil |
| `PATCH` | `/sellers/me/profile` | Atualizar perfil |
| `POST` | `/sellers/me/profile/logo` | Upload de logo |
| `POST` | `/sellers/me/profile/banner` | Upload de banner |
| `POST` | `/sellers/me/products` | Criar produto |
| `GET` | `/sellers/me/products` | Listar produtos |
| `PATCH` | `/sellers/me/products/{id}` | Atualizar produto |
| `DELETE` | `/sellers/me/products/{id}` | Deletar produto |
| `POST` | `/sellers/me/products/{id}/cover` | Upload de capa |
| `GET` | `/sellers/me/orders` | Pedidos recebidos |
| `POST` | `/sellers/me/orders/{id}/accept` | Aceitar pedido |
| `POST` | `/sellers/me/orders/{id}/reject` | Rejeitar pedido |
| `POST` | `/sellers/me/orders/{id}/mark-shipped` | Marcar como enviado |

### Pedidos — `/orders`

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/orders` | Criar pedido personalizado |
| `GET` | `/orders` | Listar meus pedidos |
| `GET` | `/orders/{id}` | Detalhes do pedido |
| `POST` | `/orders/{id}/cancel` | Cancelar pedido |
| `POST` | `/orders/{id}/confirm-delivery` | Confirmar recebimento |
| `POST` | `/orders/{id}/iterations` | Gerar nova iteração de IA |
| `POST` | `/orders/{id}/approve-iteration/{iter_id}` | Aprovar iteração |

### Carrinho — `/cart`

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/cart` | Obter carrinho |
| `POST` | `/cart/items` | Adicionar item |
| `PATCH` | `/cart/items/{id}` | Atualizar quantidade |
| `DELETE` | `/cart/items/{id}` | Remover item |
| `DELETE` | `/cart` | Limpar carrinho |
| `POST` | `/cart/checkout` | Finalizar compra |

---

## 🧪 Testes

```bash
# Todos os testes
uv run pytest

# Com relatório de coverage
uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Arquivo específico
uv run pytest tests/test_orders_routes.py -v
```

O relatório HTML é gerado em `htmlcov/index.html`.

> **Nota:** Os testes usam banco SQLite in-memory e desativam o limite de iterações automaticamente via fixture em `conftest.py`.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/minha-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona minha feature'`)
4. Push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 👥 Autores

- **Eduarda Fernandes Pires**
- **Igor Samuel Candido de Souza**

---

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através das issues do GitHub.
