# Miseo API

FastAPI + SQLAlchemy 2 + Alembic. See [`docs/DEVELOPMENT.md`](../../docs/DEVELOPMENT.md)
for setup and [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) for design decisions.

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.seeds
uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
uv run pytest
```
