# Arquitectura de Miseo

> "Descubre lo que puedes crear con lo que ya tienes."

Miseo es una plataforma open source y comunitaria de recetas de cocina y mixología.
Este documento describe **qué** construimos, **cómo** está organizado y, sobre todo,
**por qué** se tomó cada decisión.

## 1. Estado inicial del repositorio (análisis Fase 0)

| Elemento | Hallazgo |
| --- | --- |
| Contenido | Solo `README.md` (un commit inicial). No hay código previo que preservar. |
| Restricciones heredadas | Ninguna. Se adopta el stack propuesto sin ajustes mayores. |
| Herramientas disponibles | Node 22, pnpm 10, Python 3.12+, uv, PostgreSQL 16, Docker. |

Conclusión: proyecto *greenfield*. Las decisiones de este documento definen la base.

## 2. Principios rectores

1. **Útil sin IA.** Búsqueda, filtros, recomendación por ingredientes y comunidad
   funcionan sin ningún LLM. La IA solo *enriquece* el catálogo de forma asíncrona.
2. **El backend es la fuente de verdad.** Reglas de negocio, validación y permisos
   viven en FastAPI. El frontend valida para UX, pero nunca es la única barrera.
3. **Datos estructurados, no blobs de texto.** Ingredientes normalizados, cantidades
   y unidades separadas, pasos numerados. Es lo que hace posible el motor de
   recomendación determinista.
4. **Procedencia siempre.** Cada receta conserva su fuente, licencia y atribución.
   Nunca se presenta una receta inventada como clásica o histórica.
5. **Simplicidad mantenible.** Abstracciones solo cuando pagan su costo.

## 3. Vista general

```
                ┌───────────────────────────┐
  Navegador ───▶│  apps/web  (Next.js, PWA) │
  (móvil/desk)  └────────────┬──────────────┘
                             │ REST/JSON (OpenAPI)
                             ▼
                ┌───────────────────────────┐        ┌────────────────────┐
                │  apps/api  (FastAPI)      │◀──────▶│ Supabase Auth (JWT)│
                │  reglas, validación, RBAC │        └────────────────────┘
                └────────────┬──────────────┘
                             │ SQLAlchemy 2 (psycopg 3)
                             ▼
                ┌───────────────────────────┐        ┌────────────────────┐
                │  PostgreSQL (Supabase)    │        │ Supabase Storage   │
                └────────────▲──────────────┘        │ (imágenes)         │
                             │                       └────────────────────┘
                ┌────────────┴──────────────┐
                │  ai/ ingestion (Fase 4)   │──▶ Ollama (local) / proveedor opcional
                │  jobs asíncronos, idempot.│
                └───────────────────────────┘
```

**Por qué una API separada en lugar de usar Supabase directamente desde el
frontend:** Supabase permite consultar Postgres desde el cliente con RLS, pero el
motor de recomendación, la moderación, la detección de duplicados y la ingesta son
lógica de negocio no trivial. Centralizarla en Python (a) evita duplicarla en una
futura app móvil, (b) la hace testeable de forma aislada y (c) nos permite cambiar
de proveedor de base de datos sin tocar los clientes.

## 4. Estructura del monorepo

```
miseo/
├── apps/
│   ├── web/                 # Next.js (App Router) + TypeScript + Tailwind
│   │   ├── app/             # Rutas (server components por defecto)
│   │   ├── components/      # UI reutilizable (design system en components/ui)
│   │   ├── features/        # Módulos por dominio (recipes, ingredients, ...)
│   │   ├── lib/             # Utilidades puras, cliente HTTP, config
│   │   └── types/           # Tipos compartidos del contrato de la API
│   └── api/                 # FastAPI + SQLAlchemy 2 + Alembic
│       ├── app/
│       │   ├── api/         # Routers HTTP (capa delgada)
│       │   ├── core/        # Config, logging, errores, seguridad
│       │   ├── db/          # Engine, sesión, Base declarativa
│       │   ├── models/      # Modelos ORM (tablas)
│       │   ├── schemas/     # Pydantic: contratos de entrada/salida
│       │   ├── repositories/# Acceso a datos (consultas)
│       │   ├── services/    # Reglas de negocio (recomendación, moderación)
│       │   ├── integrations/# Supabase, storage, etc.
│       │   └── main.py
│       ├── migrations/      # Alembic (única fuente de cambios de esquema)
│       ├── seeds/           # Datos de desarrollo (JSON), separados de producción
│       └── tests/
├── ai/                      # Fase 4: servicio de ingesta (paquete Python propio)
├── docs/
├── docker-compose.yml
└── .env.example
```

### Ajustes respecto a la estructura sugerida (y por qué)

- **No existe `database/migrations` separado.** Tener dos lugares para migraciones
  genera divergencias. Alembic, dentro de `apps/api/migrations`, es la *única*
  fuente de cambios de esquema.
- **Seeds en `apps/api/seeds/`.** Así la imagen Docker de la API es autocontenida y
  el script de seed usa los mismos modelos y validaciones que la API.
- **`ai/` se crea en la Fase 4**, no antes: no generamos carpetas vacías. Será un
  paquete Python independiente que escribe en la base de datos a través de los
  mismos servicios/validaciones del dominio (o de la API), nunca saltándoselos.
- **`apps/web/services` y `hooks`** se crean cuando exista código real para ellos.

## 5. Backend (apps/api)

### Capas

```
Router (api/)  ──▶  Service (services/)  ──▶  Repository (repositories/)  ──▶  ORM/DB
   │                    │
   └─ Pydantic schemas ─┘  (validación de entrada y forma de salida)
```

- **Routers**: traducen HTTP ↔ dominio. Sin lógica de negocio.
- **Services**: reglas (p. ej. "una receta solo se publica si la aprueba un
  moderador"). Testeables con unit tests.
- **Repositories**: consultas SQLAlchemy. Aíslan el SQL para poder optimizarlo
  sin tocar reglas.

No aplicamos *Clean Architecture* completa (puertos/adaptadores para todo): en un
proyecto de este tamaño añadiría indirección sin beneficio. Sí separamos lo que
cambia por razones distintas.

### Decisiones técnicas clave

| Decisión | Alternativa descartada | Por qué |
| --- | --- | --- |
| **SQLAlchemy 2 async + psycopg 3** | asyncpg | psycopg 3 sirve tanto en modo async (app) como sync (Alembic) con un solo driver, y funciona con el pooler de Supabase (PgBouncer en modo transacción) desactivando prepared statements. asyncpg tiene problemas conocidos con PgBouncer. |
| **Enums como `VARCHAR + CHECK`** | Enums nativos de Postgres | Añadir/quitar valores a un `ENUM` nativo requiere migraciones delicadas (`ALTER TYPE` no es transaccional en todos los casos). Un `CHECK` se modifica con una migración normal. |
| **UUID como PK** (`gen_random_uuid()`) | `BIGSERIAL` | Coincide con los IDs de Supabase Auth, no filtra volumen de datos y permite generar IDs fuera de la BD (ingesta). Las URLs públicas usan `slug`. |
| **Alembic** como única vía de cambios | Supabase migrations | Una sola historia de esquema, versionada junto al código que la usa. |
| **pydantic-settings** | `os.environ` manual | Configuración tipada y validada al arrancar: si falta una variable crítica, la app falla rápido y con un mensaje claro. |
| **uv** para dependencias Python | pip/poetry | Resolución rápida y `uv.lock` reproducible. |

### Autenticación y autorización

Detalle y modelo de amenazas en [`AUTH.md`](AUTH.md). Resumen:

- Supabase Auth emite un JWT; la API lo **verifica** (JWKS o secreto HS256, con el
  algoritmo fijado por tipo de clave) y resuelve el perfil en `app_user`.
- El rol (`user`, `moderator`, `admin`) vive en **nuestra** base de datos, no en el
  token, y se exige con dependencias de FastAPI (`AdminUser`, `ModeratorUser`).
- Los agentes de ingesta (opencode, Claude, Gemini…) son una identidad distinta de
  las personas: token propio, guardado como hash, con *scopes* y revocación
  individual. Así se puede saber qué agente aportó cada receta.
- La `service_role key` de Supabase no se usa en ningún sitio.

### Errores, logging y seguridad

- Formato de error uniforme: `{"error": {"code", "message", "details"}}`.
- Logging estructurado (JSON en producción, legible en desarrollo) con
  `request_id` por petición.
- CORS restringido a orígenes configurados.
- Rate limiting en endpoints sensibles (envío de recetas, ingesta, auth) — Fase 3.
- Validación de imágenes por tipo MIME real y tamaño — Fase 3.

## 6. Frontend (apps/web)

- **Next.js App Router** con *server components* por defecto: el catálogo público
  se renderiza en servidor (SEO, rendimiento en móvil, cacheable para PWA).
- *Client components* solo donde hay interacción (selector de ingredientes,
  ajuste de porciones, favoritos).
- **Tailwind CSS v4** con tokens de diseño en CSS (`@theme`). Componentes base al
  estilo shadcn/ui (copiados y propios, no una dependencia opaca).
- **TanStack Query, React Hook Form y Zod** se incorporan cuando aparezcan las
  primeras pantallas interactivas que los necesiten (Fase 2/3), no antes.
- El tema de **Mixología** se activa con `data-theme="mixology"` sobre una sección:
  cambia los tokens de color sin duplicar componentes.

## 7. Motor de recomendación (Fase 2) — determinista

Implementado en `apps/api/app/services/matching.py` como **funciones puras** (sin
base de datos), probadas de forma exhaustiva en `tests/test_matching.py`. La carga
de candidatos vive aparte (`repositories/recommendation.py`). **Sin LLM.**

Para cada receta, cada ingrediente **requerido** aporta un peso:

| Situación | Peso |
| --- | --- |
| El usuario lo tiene | 1.0 |
| Es básico de despensa (`is_staple`) y `assume_staples=true` | 1.0 |
| Falta pero hay sustituto disponible `equivalent` / `similar` / `emergency` | 0.9 / 0.75 / 0.5 |
| Falta sin sustituto | 0 |

`match_percentage = Σ pesos / nº requeridos × 100`

- Los **opcionales** no penalizan; solo desempatan (bonus de 0.01 × fracción disponible).
- Una receta solo se recomienda si usa al menos un ingrediente **no básico** del
  usuario (si eliges "sal", no te recomendamos todo lo que lleva sal).
- **EXACT**: todo requerido disponible tal cual. **FLEXIBLE**: todo cubierto,
  con sustituciones. **DISCOVER**: cualquier coincidencia, ordenada.
- Orden: score ↓, faltantes ↑, tiempo total ↑, título.
- Los sustitutos pueden ser básicos (caldo → agua, de emergencia).
- **Cantidades:** el selector no pide cantidades, así que hoy no se comparan.
  Cuando exista la despensa del usuario (Fase 3, con cantidades y caducidad), el
  modelo `Candidate` ya separa lo necesario para añadirlo.

Los candidatos se filtran en SQL (recetas publicadas que usan algún ingrediente
disponible o sustituible) y se puntúan en Python: claro, testeable y suficiente
para miles de recetas. Si el catálogo crece mucho, el cálculo se puede mover a
una agregación SQL sin cambiar el contrato.

### Frontend del recomendador

`/que-puedo-preparar?i=pollo,arroz&modo=flexible&tipo=cooking&basicos=1`: el
estado vive en la URL (compartible, sobrevive a recargas). El selector es un
componente de cliente; los resultados se renderizan en servidor para esa URL.
El autocompletado usa un *route handler* de Next (`/api/ingredients`) como proxy
BFF: el navegador nunca conoce `API_URL` y la API no necesita abrir CORS.

## 7b. Animación de cócteles (datos → animación)

`apps/web/features/cocktail/`. Cada cóctel se anima **a partir de sus datos**, sin
recursos dibujados a mano:

```
receta (cristalería, técnica, ml, color, gas, guarnición)
   → buildPourPlan()   plan de vertido (volúmenes, mezcla de color, hielo...)   [puro, testeado]
   → buildTimeline()   lista de "beats": cada uno es una foto completa de la escena  [puro, testeado]
   → <CocktailAnimation>  SVG + Motion: interpola entre fotos consecutivas
```

- **Por qué Motion y no Lottie/Rive/Three.js:** Lottie y Rive necesitan una
  animación diseñada por cóctel; con datos, una nueva receta de la comunidad se
  anima sola. Three.js (3D) es demasiado pesado para móvil. Motion anima SVG de
  forma declarativa en React y respeta `prefers-reduced-motion`.
- **Líquido = rectángulos recortados por el `clipPath` del interior del vaso:** la
  misma lógica sirve para una copa cónica o un vaso recto.
- **Mezcla de color ponderada por volumen**, con menor peso para líquidos
  transparentes (ginebra, ron blanco): diluyen sin blanquear.
- **Orden de barra:** hielo antes de verter en tragos construidos; refrescos con
  gas siempre al final; sólidos (menta) primero y machacados.
- Controles de reproducción, paso a paso y lista de pasos sincronizada (sirve
  también para aprender). Con movimiento reducido muestra el trago terminado.
- Datos nuevos en BD: `ingredient.color` (hex, con CHECK) e `ingredient.is_carbonated`.

## 8. Ingesta asistida por IA (Fase 4)

Pipeline asíncrono e idempotente:

```
Fuente → Extracción → Parseo estructurado (LLM + Pydantic) → Mapeo de ingredientes
→ Normalización (determinista) → Detección de duplicados → Validación
→ Estado "pending" → Revisión humana → Publicación
```

- `LLMProvider` es una interfaz con adaptadores (Ollama primero; externo opcional).
- La salida del LLM es **no confiable**: se valida con Pydantic y reglas
  deterministas; nada se publica sin aprobación humana.
- Idempotencia: cada job tiene `idempotency_key` (hash del contenido/URL
  normalizados) con restricción `UNIQUE`.
- Si no hay proveedor configurado, el pipeline queda deshabilitado y la app sigue
  funcionando con normalidad.

## 9. Riesgos arquitectónicos identificados

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Calidad/normalización de ingredientes (sinónimos: "cilantro"/"coriandro") | Recomendaciones pobres | Tabla `ingredient_alias` + `normalized_name` único; normalización determinista antes de cualquier IA. |
| Conversión de unidades ambigua ("1 taza", "un chorrito") | Escalado de porciones incorrecto | Catálogo `unit` con factores a unidad base; unidades no convertibles marcadas como tales; cantidades nulas permitidas ("al gusto"). |
| Licencias de recetas importadas | Legal / reputación | `recipe_source` obligatorio en ingesta; no se ingieren fuentes sin licencia compatible; revisión humana. |
| Alucinaciones del LLM | Contenido falso | Validación determinista, `origin_type = ai_assisted`, revisión obligatoria, nunca auto-publicar. |
| Rendimiento del matching con catálogo grande | Latencia | Consultas agregadas en SQL con índices en `recipe_ingredient(ingredient_id)`; caché a futuro. Sin embeddings prematuros. |
| Conexiones a Supabase desde serverless | Agotamiento de conexiones | Usar el pooler de Supabase; driver compatible (psycopg 3 sin prepared statements). |
| Divergencia de contrato API ↔ web | Bugs en runtime | OpenAPI como contrato; a futuro, generación de tipos TS desde el esquema. |
| Supabase Auth no disponible en desarrollo local | Fricción | La API valida JWT con secreto configurable; en tests se generan tokens locales. |

## 10. Preparado para móvil

Toda la lógica vive en la API REST documentada con OpenAPI. Una futura app
(React Native/Expo o nativa) consumiría los mismos endpoints y el mismo Supabase
Auth, sin reescribir backend.
