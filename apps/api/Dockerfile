# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app

# Install dependencies first so they are cached independently of source changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 1000 miseo && chown -R miseo /app
USER miseo

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# Apply migrations and reference seeds, then serve.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seeds && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
