# DAGRD API

FastAPI backend baseline with layered architecture, stateless JWT authentication, PostgreSQL and Docker support.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2 |
| Database | PostgreSQL 16 (container: `dagrd-db`) |
| Validation / DTOs | Pydantic v2 + pydantic-settings |
| Security | python-jose (JWT) + passlib[bcrypt==3.2.2] |
| Infrastructure | Docker + docker-compose |

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                   # Entrypoint + lifespan (tables + seed)
│   ├── database.py               # SQLAlchemy engine + session + Base
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py       # Stateless JWT interceptor + require_roles()
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py           # POST /api/auth/login, /api/users/**
│   │       └── dummy.py          # GET /api/dummy/{community,operational,manager}
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # pydantic-settings (reads .env)
│   │   └── security.py           # bcrypt helpers + JWT encode/decode
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py               # User ORM model + RoleEnum
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py               # Pydantic DTOs
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py    # Data-access layer
│   └── services/
│       ├── __init__.py
│       └── user_service.py       # AuthService + UserService (business logic)
├── .env                          # Active env vars (do NOT commit!)
├── .env.example                  # Template
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Enter the project directory
cd dagrd-api

# 2. (Optional) Customise environment variables
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# 4. Open interactive API docs
open http://localhost:8000/docs
```

On first boot the container automatically:
1. Creates all PostgreSQL tables.
2. Inserts three seed users (one per role) if the table is empty.

---

## Test Users (seeded on first boot)

| Username | Password | Role |
|---|---|---|
| `user_community` | `Community123!` | Community |
| `user_operational` | `Operational123!` | Operational |
| `user_manager` | `Manager123!` | Manager |

---

## API Reference

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | ❌ Public | Returns a signed JWT |

**Request body**
```json
{ "username": "user_manager", "password": "Manager123!" }
```

**Response**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### Dummy Endpoints (role-protected, stateless)

| Method | Path | Allowed Roles |
|---|---|---|
| `GET` | `/api/dummy/community` | Community, Manager |
| `GET` | `/api/dummy/operational` | Operational, Manager |
| `GET` | `/api/dummy/manager` | Manager only |

Pass the token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

---

### User Management

| Method | Path | Auth |
|---|---|---|
| `POST` | `/api/users/` | JWT |
| `GET` | `/api/users/` | JWT |
| `GET` | `/api/users/{id}` | JWT |

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |

---

## Architecture Notes

### Layered Architecture

```
HTTP Request
    │
    ▼
Router (Controller)  ──── Depends(get_db) ──── SQLAlchemy Session
    │
    ▼
Service (Business Logic)
    │
    ▼
Repository (Data Access)
    │
    ▼
Database (PostgreSQL — dagrd-db)
```

### Stateless JWT Authorization

`dependencies.py` validates the JWT **signature only** — no DB call is made.
The `role` is read directly from the token payload.

### `require_roles()` — Dependency Factory

```python
@router.get("/manager")
def endpoint(payload = Depends(require_roles(RoleEnum.Manager))):
    ...
```

---

## cURL Quick Test

```bash
# 1. Login and capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user_manager","password":"Manager123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Access the Manager-only endpoint → 200 OK
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/dummy/manager

# 3. Try Community role on Manager endpoint → 403 Forbidden
TOKEN_C=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user_community","password":"Community123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN_C" http://localhost:8000/api/dummy/manager
```

---

## Generate a Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Replace the value in `.env` before deploying to production.

---

## AWS Deployment Hints

| Component | AWS Service |
|---|---|
| Container | ECS Fargate |
| Image registry | Amazon ECR |
| Database | Amazon RDS for PostgreSQL |
| Secrets | AWS Secrets Manager |
| Load balancer | Application Load Balancer (HTTPS → port 8000) |
| Logs | CloudWatch Logs |
