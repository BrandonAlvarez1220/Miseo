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
- Fase 2 en adelante (ver más abajo).

## Fase 1 — Fundación ✅

**Completado**
- Monorepo: pnpm workspace (`apps/web`) + proyecto uv (`apps/api`).
- **API** (`apps/api`):
  - Configuración tipada y validada al arrancar (`pydantic-settings`).
  - Logging con `request_id` por petición (texto en desarrollo, JSON en producción);
    `X-Request-ID` propagado solo si es seguro (evita inyección en logs).
  - Formato de error uniforme `{"error": {code, message, details}}` para 404, 422,
    errores de dominio y 500 (sin filtrar detalles internos).
  - CORS restringido a orígenes configurados; `/docs` deshabilitado en producción.
  - Modelos SQLAlchemy 2 de **todo** el esquema de `DATABASE.md` (21 tablas) con
    CHECKs, FKs, índices, `NULLS NOT DISTINCT` y trigram.
  - Migración inicial Alembic (reversible; `alembic check` sin diferencias).
  - Seeds idempotentes: unidades, categorías (cocina/mixología), familias de
    ingredientes, cristalería y técnicas de barra.
  - Endpoints: `GET /api/v1/health` (verifica BD, 503 si cae) y
    `GET /api/v1/categories?recipe_type=`.
  - Dockerfile (usuario no root, migra + seed al arrancar).
- **Web** (`apps/web`):
  - Next.js 16 (App Router, Cache Components) + Tailwind v4.
  - Design system: tokens de dos mundos, `Button`, `Chip`, `Skeleton`,
    `StateMessage`, `Container`, `SectionHeading` (ver `DESIGN_SYSTEM.md`).
  - Layout con cabecera/navegación activa, pie, `not-found`, `error`.
  - Páginas Inicio, Cocina y Mixología consumiendo la API real con skeleton,
    estado vacío y estado de error con reintento.
  - Cliente HTTP tipado (`apiFetch`) que traduce el formato de error de la API.
  - Build `standalone` + Dockerfile.
- `docker-compose.yml` (db + api + web), `.env.example`, CI de GitHub Actions,
  licencia MIT.

**Decisiones arquitectónicas**
- Datos del catálogo renderizados en servidor dentro de `<Suspense>` y diferidos a
  request time con `connection()`: la API no tiene por qué estar disponible al
  compilar, y así nunca se "hornea" un estado de error en el HTML estático.
- `API_URL` es solo de servidor; todavía no hay llamadas desde el navegador, por lo
  que no se expone ninguna URL ni clave con `NEXT_PUBLIC_`.
- Rutas públicas en español (`/cocina`, `/mixologia`); código y API en inglés.
- React Hook Form, Zod y TanStack Query se añadirán con las primeras pantallas
  interactivas (Fase 2/3), no antes.
- Las tarjetas de categoría aún no son enlaces: las páginas de categoría llegan en la
  Fase 2 y no queremos enlaces rotos ni elementos que parezcan clicables sin serlo.

**Tests ejecutados**
- API: `pytest` → 27 passed (health, CORS, errores, categorías, config, seeds,
  constraints de BD contra PostgreSQL 16 real). `ruff check`, `ruff format --check`
  y `mypy --strict` sin errores.
- Web: `vitest` → 12 passed (cliente API, grid de categorías y estado vacío, tema por
  ruta). `eslint` y `tsc` sin errores. `next build` correcto.
- Manual: API + web en local; categorías visibles en `/`, `/cocina`, `/mixologia`;
  con la API detenida se muestra el estado de error y se recupera al levantarla;
  sin scroll horizontal a 390 px; build standalone sirve páginas e icono.

**Problemas conocidos / no verificado**
- `docker compose up` **no se pudo ejecutar** en el entorno de desarrollo usado (sin
  daemon de Docker). `docker compose config` valida la sintaxis y las imágenes se
  basan en los mismos comandos verificados manualmente, pero falta probarlo de
  punta a punta.
- El workflow de CI no se ha ejecutado todavía en GitHub.
- Sin fotografía real todavía; las tarjetas usan solo tipografía.

**Siguientes tareas recomendadas (Fase 2)**
1. Normalizador determinista de ingredientes (`normalized_name`, alias) + tests.
2. Seeds de ingredientes, sustituciones y recetas de ejemplo con atribución.
3. `GET /recipes` (búsqueda trigram, filtros, orden, paginación) y `GET /recipes/{slug}`.
4. Motor de recomendación EXACT / FLEXIBLE / DISCOVER + tests exhaustivos.
5. UI: búsqueda, selector de ingredientes, resultados con %, detalle con porciones.
