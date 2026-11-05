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

## Rediseño visual (entre Fase 1 y 2) ✅

Rama `refactor/web-app-shell-layout`. La interfaz pasa de un estilo editorial
(serif, crema) a una *app* tipo panel inspirada en la referencia aportada:
barra lateral, búsqueda fija, blanco/verde/naranja y Plus Jakarta Sans. Ver
`DESIGN_SYSTEM.md`. También: Prettier con orden de clases Tailwind y
`output: standalone` solo en Docker (`next start` vuelve a funcionar en local).

## Fase 2 — Núcleo (sin IA) ✅

**Completado**
- **Datos**
  - Migración 2: `ingredient.slug`, `ingredient.is_staple`, extensión `unaccent`
    (relleno seguro de `slug` para filas existentes).
  - Normalizador determinista (`services/normalization.py`), sin singularizar.
  - Seeds validados con Pydantic (`app/seeding/`): 62 ingredientes con 120+
    alias, 19 sustituciones, 12 recetas de cocina (ejemplos originales de Miseo,
    CC BY-SA 4.0) y 11 bebidas: 9 clásicos según la IBA (atribuidos), 1 variación
    documentada (Hemingway Special) y 2 sin alcohol (1 variación, 1 contemporánea).
    Upsert por clave natural en una transacción; ejecución repetible.
- **API**
  - `GET /recipes`: búsqueda sin acentos y tolerante a erratas, filtros (tipo,
    categoría, dificultad, tiempo máximo, ingredientes, con/sin alcohol), orden
    (relevancia, recientes, alfabético, rápidas) y paginación acotada.
  - `GET /recipes/{slug}`: ingredientes con unidades y sustituciones, pasos,
    fuentes, datos de barra, variaciones y relacionadas. Solo publicadas.
  - `GET /ingredients`: autocompletado (nombre/alias), resolución por slugs,
    populares por módulo.
  - `GET /recommendations`: motor EXACT / FLEXIBLE / DISCOVER.
  - `GET /categories` con número de recetas publicadas; `GET /mixology/techniques`
    y `/glass-types`.
- **Web**
  - Inicio con datos reales: recién añadidas, ingredientes populares (atajos al
    recomendador), clásicos de barra, categorías destacadas.
  - `/que-puedo-preparar`: combobox accesible (teclado, ARIA), sugerencias, modos,
    filtro de tipo, básicos; estado en la URL; tarjetas con % de coincidencia,
    lo que tienes, lo que falta, sustituciones y básicos asumidos.
  - `/recetas`: buscador global y filtros como formulario GET (funciona sin JS;
    con JS aplica al cambiar y limpia parámetros vacíos), chips de filtros
    activos, paginación.
  - `/recetas/[slug]`: detalle con ajuste de porciones (fracciones y redondeo
    métrico), sustituciones por ingrediente, consejo, fuente y atribución,
    compartir (Web Share API o copiar enlace), relacionadas; los cócteles se
    muestran con el tema de Mixología.
  - Cocina y Mixología: categorías enlazadas, últimas recetas; guía de técnicas y
    cristalería.
  - Ilustraciones de respaldo deterministas por categoría mientras no hay fotos.

**Decisiones**
- Matching en Python sobre candidatos filtrados en SQL (ver ARCHITECTURE §7).
- Los básicos de despensa se asumen por defecto pero el usuario puede desactivarlo.
- Proxy BFF para el autocompletado en lugar de exponer la API al navegador.
- Validación de parámetros de URL con Zod: valores inválidos se descartan en lugar
  de romper la página (enlaces editados a mano siguen funcionando).
- TanStack Query no se añadió: el único fetch en cliente (autocompletado) es un
  `fetch` con `AbortController` y *debounce*; no justifica la dependencia aún.
- Componentes de datos llaman a `connection()`: con *partial prefetching*, un
  render especulativo abortaba los `fetch` y quedaban errores en el log.
- Favoritos no se muestran en el detalle hasta tener autenticación (Fase 3): sin
  botones que no hagan nada.

**Tests ejecutados**
- API: 86 passed (`pytest -W error::DeprecationWarning`), `ruff`, `ruff format`,
  `mypy --strict` sin errores. Incluye 25+ tests unitarios del matcher.
- Web: 44 passed (`vitest`), `eslint`, `prettier --check`, `tsc`, `next build`.
- Manual con Playwright: autocompletado → selección con teclado → cambio de modo
  → quitar ingrediente; escalado de porciones (800 g → 400 g); búsqueda global y
  filtros; sin errores en consola; sin scroll horizontal a 390 px.

**Problemas conocidos**
- Las especificaciones IBA se transcribieron a mano: conviene verificarlas contra
  la lista oficial antes de un release.
- Una receta inexistente muestra la página 404 pero responde HTTP 200 (el estado
  ya se envió al hacer *streaming*); Next añade `noindex`, así que no se indexa.
- `docker compose up` sigue sin probarse de punta a punta (sin daemon de Docker).
- Licencia de contenido de recetas (CC BY-SA 4.0) a confirmar por el autor.
- Sin fotografía real; `image_url` está soportado de punta a punta.

**Siguientes tareas recomendadas (Fase 3)**
1. Supabase Auth + verificación de JWT en la API + perfiles `app_user`.
2. RBAC en dependencias de FastAPI y tests de permisos.
3. Favoritos (y su botón en el detalle).
4. Despensa del usuario con cantidades y caducidad (habilita el aviso "tu tempeh
   está por caducar" de la referencia).
5. Envío de recetas con React Hook Form + Zod y moderación.

## Animación de cócteles ✅

Rama `feat/cocktail-pour-animation` (parte de la Fase 2).

**Completado**
- Migración 3: `ingredient.color` (hex validado por CHECK) e `ingredient.is_carbonated`;
  colores en los seeds; expuestos en el detalle de receta (`RecipeIngredientRef`).
- `buildPourPlan` y `buildTimeline` (funciones puras) + `CocktailAnimation`
  (SVG + Motion 14.3.1): 10 tipos de cristalería, técnicas batido / mezclado /
  construido / machacado, hielo, burbujas, guarniciones (rueda de cítrico, piel de
  naranja, menta, cereza, borde de sal), controles y paso a paso.
- Reemplaza la ilustración estática en el detalle de cada cóctel.

**Tests**
- API: 88 passed. Web: 58 passed (plan de vertido, mezcla de color, orden de barra,
  textos, guion por técnica). Verificado en Chromium: daiquiri, mojito, cuba libre
  y negroni, escritorio y móvil, `prefers-reduced-motion`, sin errores de consola.

**Limitaciones conocidas**
- Las alturas del líquido son lineales (no calculan el volumen real de una copa
  cónica): es una ilustración, no una simulación.
- El azúcar en cucharaditas se representa como líquido (se disuelve); en el mojito
  aparece después de la menta en vez de machacarse con ella.
- Las guarniciones se deducen del texto libre `garnish`; las no reconocidas no se
  dibujan.

## Rutas de aprendizaje (escalera de platillos) ✅ etapas 1–4

Rama `feat/learning-paths-dish-ladder`. Detalle en `LEARNING_PATHS.md`.

**Completado**
- Migración 4: `skill`, `recipe_skill`, `learning_path`, `path_stage`, `path_dish`.
- Seeds validados: 7 recetas nuevas (6 de cocina mexicana casera y la Paloma),
  8 ingredientes, 30 habilidades con tips, 66 etiquetas, rutas de cocina y barra
  con 4 etapas cada una. Repetibles sin duplicar.
- API `GET /paths`, `GET /paths/{slug}` (`is_new` calculado en orden de la
  escalera; solo recetas publicadas); `skills` y `paths` en el detalle de receta.
- Web: `/rutas`, `/rutas/[slug]` con progreso, desbloqueo sugerido (nunca
  bloquea la navegación), "Ya lo cociné" y habilidades que ya tienes; sección
  "Lo que aprendes" con tips en cada receta; tarjetas de rutas en el inicio;
  "Rutas" en la navegación (en móvil sustituye a "Recetas", que sigue en la
  búsqueda). Aviso de consumo responsable en la ruta de barra.
- El progreso vive en `localStorage` mediante `useSyncExternalStore` (correcto con
  SSR, sincronizado entre pestañas, tolera almacenamiento bloqueado).

**Tests**
- API: 97 passed (rutas, `is_new`, recetas no publicadas, validaciones del seed).
- Web: 65 passed (lógica de desbloqueo, escalera interactiva, almacenamiento
  bloqueado). Playwright: marcar 3 platillos desbloquea la etapa 2 y persiste tras
  recargar; sin errores de consola; sin scroll horizontal en móvil.

**Notas**
- La Paloma usa la especificación IBA de memoria (50 ml tequila, 5 ml lima, 100 ml
  refresco de toronja, sal): verificar junto con el resto.
- El progreso es por navegador hasta tener cuentas (Fase 3).

## Auth, roles y registro de agentes ✅ (API)

Rama `feat/api-auth-roles-and-agent-registry`. Detalle en `AUTH.md`.

**Completado**
- Migración 5: tabla `agent` (con CHECK de nombre y scopes) y `app_user.email`.
- Verificación de JWT de Supabase con algoritmo fijado por tipo de clave (HS256 con
  secreto, RS256/ES256 con JWKS), `exp`/`sub`/`aud` obligatorios, `iss` opcional.
  Fallo del JWKS → 503, no 401.
- Perfiles creados en el primer acceso (rol `user`), con carga segura frente a
  peticiones simultáneas. El rol se lee de la BD, nunca del token.
- RBAC: `CurrentUser`, `ModeratorUser`, `AdminUser`; `GET/PATCH /me`;
  `GET /admin/users`, `PUT /admin/users/{id}/role` (un admin no cambia su propio rol).
- CLI `python -m app.cli grant-role` para nombrar al primer administrador.
- Registro de agentes: `POST/GET /admin/agents`, `POST /admin/agents/{id}/revoke`,
  `GET /agent/me`. Token `mis_ag_…` mostrado una vez y guardado como SHA-256; scope
  `submit_recipes`; revocación individual; `last_used_at` limitado a 1 escritura/min.
- `Page[T]` movido a `schemas/common.py` (lo usan ahora recetas y usuarios).

**Tests:** 151 passed (`-W error::DeprecationWarning`): 35 de auth (token expirado,
audiencia, firma, sin `sub`/`exp`, `alg: none`, confusión de algoritmo, emisor, ES256
con JWKS simulado, roles ignorados en el token, matriz de permisos), 19 de agentes
(hash en BD, tres agentes independientes, revocación, tokens no intercambiables,
CLI). `ruff` y `mypy --strict` limpios. Prueba manual con el servidor real: login →
CLI → admin → tres agentes con token válido.

**No verificado**
- Contra un **Supabase real**: se probó con tokens firmados localmente. Falta
  confirmar la configuración del JWKS/emisor con tu proyecto.
- Pantalla de login en la web (necesita URL y *anon key* de tu proyecto).

**Siguiente:** endpoint `POST /agent/submissions` (validación, normalización,
duplicados, dificultad, sugerencia de etapa, cola pendiente) y pantalla de revisión.

## Ingreso local (sin Supabase) ✅

Rama `feat/local-dev-login`. Se desarrolla todo en local; Supabase queda para la
publicación.

**Completado**
- API: `POST /api/v1/dev/login` (solo si `DEV_LOGIN_ENABLED`), usuarios estables por
  correo, `DEV_ADMIN_EMAILS` para el primer admin sin CLI. Validación de arranque:
  prohibido en producción y exige el secreto de firma.
- Web: `/ingresar`, sesión en cookie `httpOnly`, menú de usuario en la barra superior
  (dentro de `<Suspense>`), cerrar sesión, `apiFetch` con `token`, redirección `next`
  segura.
- `getSession()` difiere la llamada a `/me` con `connection()`: Next hace renders de
  prefetch con cookies reales y los aborta, lo que dejaba `fetch` rechazados en el log.

**Tests:** API 162 passed (11 nuevos); web 77 passed (`safeRedirectPath`, `apiFetch`
con token). Playwright: login, dominio reservado rechazado con mensaje, `next`
malicioso ignorado, cookie `httpOnly` ilegible desde JS, logout, cookie corrupta =
sesión cerrada, sin errores de consola, sin scroll horizontal en móvil.

**Notas**
- El validador de correos rechaza `.local`/`.test`; el valor por defecto es
  `admin@example.com`.
