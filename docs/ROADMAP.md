# Roadmap

Desarrollo incremental por fases. Cada fase termina con tests ejecutados,
documentación actualizada y `docs/IMPLEMENTATION_STATUS.md` al día.

## Fase 0 — Análisis y diseño técnico
- [x] Inspección del repositorio (vacío, greenfield).
- [x] Estructura de carpetas definitiva.
- [x] Esquema de base de datos (`DATABASE.md`).
- [x] Riesgos arquitectónicos (`ARCHITECTURE.md` §9).
- [x] Roadmap y guía de desarrollo.

## Fase 1 — Fundación
- Monorepo (pnpm workspace para JS; uv para Python).
- `apps/api`: FastAPI, configuración tipada, logging, errores uniformes, CORS,
  health check con verificación de BD.
- Modelos SQLAlchemy de **todo** el esquema + migración inicial Alembic.
- Seeds de referencia (unidades, categorías, catálogos de mixología).
- Endpoint público de solo lectura `GET /api/v1/categories` como primer corte
  vertical real (BD → API → web).
- `apps/web`: Next.js, Tailwind v4, design system inicial (tokens, Button, Chip,
  Card, Skeleton, Container), layout con navegación, Inicio / Cocina / Mixología
  consumiendo la API con estados de carga/vacío/error.
- Docker Compose (db + api + web), `.env.example`.
- Tests de API (health, categorías, constraints del modelo) y lint/build del web.

**Entregable:** ambas apps corren en local.

## Fase 2 — Núcleo (sin IA)
- Endpoints de recetas: listado con búsqueda, filtros (categoría, tiempo,
  dificultad, tipo), ordenación y paginación.
- Detalle de receta con ingredientes, pasos, fuentes, sustituciones y
  relacionadas.
- Catálogo de ingredientes y autocompletado.
- Motor de recomendación determinista (EXACT / FLEXIBLE / DISCOVER) + tests.
- UI: búsqueda, filtros, selector de ingredientes con chips, resultados con %,
  detalle con ajuste de porciones.
- Seeds de recetas de ejemplo (cocina y cócteles clásicos con atribución).

## Fase 3 — Autenticación y comunidad
- Supabase Auth en web; verificación de JWT en API; perfiles `app_user`.
- RBAC (`user`, `moderator`, `admin`) aplicado en backend.
- Favoritos.
- Envío de recetas (formulario con React Hook Form + Zod; validación definitiva
  en API), detección de duplicados, revisiones.
- Panel de moderación: aprobar/rechazar.
- Subida de imágenes a Supabase Storage con validación de tipo/tamaño.
- Rate limiting en endpoints sensibles.

## Fase 4 — Ingesta con IA (opcional)
- Paquete `ai/`: `LLMProvider`, adaptador Ollama, adaptador externo opcional.
- Extracción estructurada con Pydantic; normalización y validación
  deterministas; detección de duplicados.
- Jobs idempotentes con reintentos seguros.
- Panel admin: jobs, errores de validación, candidatos a duplicado.

## Fase 5 — Pulido y release
- PWA (manifest, iconos, offline básico para recetas públicas).
- Accesibilidad (auditoría con axe), rendimiento, refinamientos responsive.
- E2E con Playwright para los recorridos clave.
- Guía de despliegue (Vercel + Fly/Render + Supabase).
