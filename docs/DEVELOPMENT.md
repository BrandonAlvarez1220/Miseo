# Guía de desarrollo

## Requisitos

| Herramienta | Versión | Uso |
| --- | --- | --- |
| Node.js | ≥ 20.9 (recomendado 22) | Frontend |
| pnpm | ≥ 9 | Gestor de paquetes JS (workspace) |
| Python | ≥ 3.12 | API |
| uv | ≥ 0.5 | Entornos y dependencias Python |
| PostgreSQL | ≥ 15 | Local o vía Docker (Supabase en producción) |
| Docker (opcional) | — | Levantar todo con `docker compose` |

## Puesta en marcha rápida (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000 — documentación OpenAPI en http://localhost:8000/docs

El contenedor de la API aplica las migraciones y carga los seeds al arrancar.

## Puesta en marcha manual

### 1. Base de datos

Con Docker solo para Postgres (crea también `miseo_test` en el primer arranque):

```bash
docker compose up -d db
```

O con un PostgreSQL local:

```sql
CREATE USER miseo WITH PASSWORD 'miseo' CREATEDB;
CREATE DATABASE miseo OWNER miseo;
CREATE DATABASE miseo_test OWNER miseo;
```

### 2. API

```bash
cd apps/api
cp .env.example .env            # ajusta DATABASE_URL si hace falta
uv sync                         # crea .venv e instala dependencias
uv run alembic upgrade head     # aplica migraciones
uv run python -m app.seeds      # carga datos de referencia/desarrollo
uv run uvicorn app.main:app --reload
```

### 3. Web

```bash
pnpm install                    # desde la raíz del repo
cp apps/web/.env.example apps/web/.env.local
pnpm --filter web dev
```

## Comandos frecuentes

| Tarea | Comando |
| --- | --- |
| Tests API | `cd apps/api && uv run pytest` |
| Lint API | `cd apps/api && uv run ruff check . && uv run ruff format --check .` |
| Tipos API | `cd apps/api && uv run mypy app` |
| Nueva migración | `cd apps/api && uv run alembic revision --autogenerate -m "describe change"` |
| Lint web | `pnpm --filter web lint` |
| Formato web | `pnpm --filter web format` (CI usa `format:check`) |
| Tipos web | `pnpm --filter web typecheck` |
| Tests web | `pnpm --filter web test` |
| Build web | `pnpm --filter web build` |

El usuario `miseo` debe poder crear la extensión `pg_trgm` (es una extensión
*trusted* en PostgreSQL ≥ 13, así que basta con ser dueño de la base de datos).

Los tests de la API usan una base de datos real (`TEST_DATABASE_URL`, por defecto
`miseo_test`). **Por qué no SQLite:** usamos características propias de Postgres
(`pg_trgm`, `NULLS NOT DISTINCT`, `gen_random_uuid()`); probar en otro motor daría
falsos positivos.

## Probar rutas protegidas en local (sin Supabase)

Con un secreto de desarrollo puedes firmar tus propios tokens:

```bash
export SUPABASE_JWT_SECRET="un-secreto-local-de-al-menos-32-bytes!!"
cd apps/api && uv run uvicorn app.main:app --reload
# en otra terminal:
TOKEN=$(uv run python -c "import jwt,time,uuid; print(jwt.encode({'sub':str(uuid.uuid4()),'aud':'authenticated','exp':int(time.time())+3600,'email':'yo@local.test'}, '$SUPABASE_JWT_SECRET', algorithm='HS256'))")
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/v1/me
uv run python -m app.cli grant-role --email yo@local.test --role admin
```

Nunca uses ese secreto fuera de tu máquina. Ver [`AUTH.md`](AUTH.md).

## Convenciones de Git

### Ramas

Nombre descriptivo con prefijo por tipo:

```
feat/<descripcion-corta>      feat/ingredient-recommendation-engine
fix/<descripcion-corta>       fix/serving-scaling-rounding
docs/<descripcion-corta>      docs/phase-0-architecture-design
chore/<descripcion-corta>     chore/upgrade-nextjs
refactor/<descripcion-corta>  refactor/recipe-repository-queries
test/<descripcion-corta>      test/moderation-permissions
```

### Commits — Conventional Commits

```
<tipo>(<ámbito opcional>): <resumen en imperativo>
```

Tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`. Ámbitos habituales: `api`, `web`, `db`, `ai`, `docs`.

Ejemplos:

```
feat(api): add deterministic ingredient matching service
fix(web): keep selected ingredients when switching search mode
docs: describe database normalization rules
```

## Variables de entorno

- Nunca se commitean secretos: solo `.env.example`.
- Variables con prefijo `NEXT_PUBLIC_` se exponen al navegador: **nunca** pongas
  ahí la `service_role key` de Supabase ni claves de LLM.
- La API valida su configuración al arrancar (`app/core/config.py`).

## Datos de ejemplo vs producción

Los seeds (`apps/api/seeds/`) son para desarrollo. El script es idempotente
(upsert por claves naturales: `code`, `slug`, `normalized_name`), así que se
puede ejecutar varias veces sin duplicar registros.
