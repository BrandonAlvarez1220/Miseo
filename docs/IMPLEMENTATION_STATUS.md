# Estado de implementación

## Fase 0 — Análisis y diseño técnico ✅

**Completado**
- Análisis del repositorio: vacío (solo `README.md`), sin restricciones heredadas.
- `docs/ARCHITECTURE.md`: arquitectura, estructura del monorepo, decisiones y riesgos.
- `docs/DATABASE.md`: esquema normalizado completo con constraints e índices.
- `docs/ROADMAP.md`: plan por fases.
- `docs/DEVELOPMENT.md`: puesta en marcha y convenciones de Git.

**Decisiones arquitectónicas**
- Migraciones solo con Alembic (sin `database/migrations` paralelo).
- Seeds dentro de `apps/api/seeds/`.
- `ai/` se crea en Fase 4.
- psycopg 3 (async + sync) en lugar de asyncpg por compatibilidad con PgBouncer.
- Enums como `VARCHAR + CHECK`.
- Documentación en español; código, identificadores y API en inglés.

**Pendiente**
- Fase 1 en adelante.
