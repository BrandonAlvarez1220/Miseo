# Diseño de base de datos

Base de datos relacional normalizada en PostgreSQL (≥ 15, compatible con Supabase).
Las migraciones se gestionan **exclusivamente** con Alembic (`apps/api/migrations`).

## Convenciones

| Convención | Regla | Por qué |
| --- | --- | --- |
| Nombres | `snake_case`, tablas en singular (`recipe`, `ingredient`) | Coincide con el nombre de la clase ORM; evita plurales irregulares. |
| PK | `id UUID DEFAULT gen_random_uuid()` | IDs generables fuera de la BD (ingesta), compatibles con Supabase Auth. |
| Tiempos | `created_at`/`updated_at` `TIMESTAMPTZ` | Siempre con zona horaria; `updated_at` lo mantiene el ORM. |
| Enums | `VARCHAR` + `CHECK` | Evolucionan con migraciones normales (ver ARCHITECTURE.md). |
| Nombres de constraints | Convención fija (`pk_`, `fk_`, `uq_`, `ix_`, `ck_`) | Alembic puede generar/borrar constraints de forma determinista. |
| Borrado | `ON DELETE CASCADE` para hijos estrictos (pasos, ingredientes de receta); `RESTRICT`/`SET NULL` para catálogos y usuarios | Nunca perder recetas por borrar un ingrediente o un usuario. |

## Diagrama entidad-relación (resumen)

```
app_user ─┬─< recipe (created_by)
          ├─< user_favorite >── recipe
          ├─< recipe_contribution >── recipe
          └─< recipe_revision >── recipe

category ──< recipe_category >── recipe
recipe ──< recipe_ingredient >── ingredient ──< ingredient_alias
recipe_ingredient >── unit
recipe ──< preparation_step
recipe ──< recipe_source
recipe ──1:1── drink_details >── glass_type
                              >── bartending_technique
                              >── ingredient (base_spirit)
                              >── recipe (variation_of)
ingredient ──< ingredient_alternative >── ingredient
ingredient >── ingredient_category

ingestion_job ──< ingestion_issue
ingestion_job ──> recipe (result)
duplicate_candidate >── recipe (x2)
```

## Tablas

### Usuarios

**`app_user`** — datos de aplicación del usuario. El `id` es el mismo UUID de
`auth.users` de Supabase. **No** hay FK a `auth.users` porque ese esquema no existe
en desarrollo local ni en tests; la integridad se garantiza al crear el perfil
tras validar el JWT.

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | uuid PK | = `sub` del JWT de Supabase |
| display_name | varchar(80) | |
| avatar_url | text null | |
| role | varchar CHECK (`user`,`moderator`,`admin`) | default `user` |
| created_at / updated_at | timestamptz | |

### Catálogo

**`category`** — categorías de recetas, separadas por módulo.

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | uuid PK | |
| name | varchar(80) | |
| slug | varchar(100) | `UNIQUE (recipe_type, slug)` |
| description | text null | |
| recipe_type | CHECK (`cooking`,`drink`) | Una categoría pertenece a un módulo |

**`ingredient_category`** — familia del ingrediente (verdura, proteína, destilado,
licor, jarabe, ...). Tabla en lugar de enum porque la comunidad la ampliará.

**`ingredient`**

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | uuid PK | |
| name | varchar(120) | Nombre visible ("Limón") |
| normalized_name | varchar(120) **UNIQUE** | minúsculas, sin acentos, singular, espacios colapsados ("limon") |
| description | text null | |
| category_id | FK `ingredient_category` null | |
| is_alcoholic | bool default false | Clasifica bebidas sin alcohol de forma derivable |
| abv | numeric(4,1) null CHECK 0–100 | Solo si el dato es fiable (para estimar ABV del cóctel) |
| image_url | text null | |

**`ingredient_alias`** — sinónimos para normalización ("coriandro" → cilantro,
"lime" → lima). `normalized_alias` UNIQUE global: un alias apunta a un único
ingrediente, lo que hace el mapeo determinista.

**`unit`** — unidades estandarizadas. PK natural `code` (`g`, `kg`, `ml`, `l`,
`tsp`, `tbsp`, `cup`, `oz`, `piece`, `pinch`, `dash`, ...).

| Columna | Tipo | Notas |
| --- | --- | --- |
| code | varchar(16) PK | Estable, se usa en la API |
| name | varchar(40) | |
| unit_type | CHECK (`mass`,`volume`,`count`,`other`) | |
| to_base_factor | numeric(12,6) null | Factor a la unidad base (g o ml). Null = no convertible (pizca, al gusto) |

**Por qué un catálogo de unidades:** si `unit` fuera texto libre, "cda", "cucharada"
y "tbsp" serían tres cosas distintas y el escalado de porciones o la conversión
métrica/imperial serían imposibles.

### Recetas

**`recipe`**

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | uuid PK | |
| title | varchar(160) | Índice trigram para búsqueda |
| slug | varchar(180) **UNIQUE** | URL pública |
| description | text null | Resumen corto |
| introduction | text null | Historia/contexto |
| tips | text null | Consejos |
| preparation_time_minutes | int null CHECK ≥ 0 | |
| cooking_time_minutes | int null CHECK ≥ 0 | |
| difficulty | CHECK (`easy`,`medium`,`hard`) null | |
| servings | int CHECK > 0 default 1 | Base para escalar cantidades |
| image_url | text null | Supabase Storage |
| recipe_type | CHECK (`cooking`,`drink`) | |
| status | CHECK (`draft`,`pending`,`published`,`rejected`) | Solo `published` es público |
| origin_type | CHECK (`community`,`curated`,`ai_assisted`) | |
| created_by | FK `app_user` null, `ON DELETE SET NULL` | |
| published_at | timestamptz null | |
| created_at / updated_at | timestamptz | |

Índices: `(status, recipe_type)`, `(published_at)`, GIN trigram sobre `title`.

**`recipe_category`** — N:M receta ↔ categoría. PK compuesta.

**`recipe_ingredient`**

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | uuid PK | |
| recipe_id | FK `recipe` CASCADE | |
| ingredient_id | FK `ingredient` RESTRICT | Índice: base del matching |
| quantity | numeric(10,3) null CHECK > 0 | Null = "al gusto" |
| quantity_max | numeric(10,3) null | Rangos "2–3"; CHECK ≥ quantity |
| unit_code | FK `unit` null | |
| is_optional | bool default false | |
| preparation_notes | varchar(200) null | "picado fino" |
| group_label | varchar(80) null | "Para la salsa" |
| position | int | Orden de visualización |

`UNIQUE NULLS NOT DISTINCT (recipe_id, ingredient_id, group_label)`: el mismo
ingrediente no se repite en el mismo grupo, pero sí puede aparecer en grupos
distintos (azúcar en la masa y en la cobertura). `NULLS NOT DISTINCT` (PG15+) hace
que dos filas sin grupo también se consideren duplicadas.

**`preparation_step`** — `UNIQUE (recipe_id, step_number)`, `step_number > 0`.

**`recipe_source`** — procedencia y licencia: `source_name`, `source_url`,
`attribution`, `license`, `source_type` CHECK (`website`,`book`,`community`,
`original`,`ai_generated`,`other`). Una receta puede tener varias fuentes.

### Mixología

**`drink_details`** — relación 1:1 opcional con `recipe` (PK = `recipe_id`).
**Por qué una tabla aparte:** los campos de cóctel no tienen sentido en una receta
de cocina; meterlos en `recipe` llenaría la tabla de columnas nulas y
reglas condicionales.

| Columna | Tipo | Notas |
| --- | --- | --- |
| recipe_id | PK/FK `recipe` CASCADE | |
| is_alcoholic | bool | Mocktails = false |
| base_spirit_id | FK `ingredient` null | |
| glass_type_id | FK `glass_type` null | |
| technique_id | FK `bartending_technique` null | |
| garnish | varchar(200) null | |
| abv_estimate | numeric(4,1) null | Solo si es fiable |
| classification | CHECK (`classic`,`variation`,`contemporary`,`experimental`) | Distingue canon de variaciones y sugerencias experimentales |
| variation_of_id | FK `recipe` null | Variación documentada de un clásico |

`CHECK (classification <> 'variation' OR variation_of_id IS NOT NULL)`.

**`glass_type`**, **`bartending_technique`** — catálogos (`name`, `slug` UNIQUE,
`description`).

### Sustituciones

**`ingredient_alternative`**

| Columna | Tipo | Notas |
| --- | --- | --- |
| ingredient_id | FK `ingredient` | Original |
| alternative_ingredient_id | FK `ingredient` | Sustituto |
| substitution_type | CHECK (`equivalent`,`similar`,`emergency`) | Peso en el modo FLEXIBLE |
| ratio | numeric(6,3) default 1 | 1 de original = `ratio` de sustituto |
| equivalence_notes | text null | |

`UNIQUE (ingredient_id, alternative_ingredient_id)` y
`CHECK (ingredient_id <> alternative_ingredient_id)`. Es dirigida: que la
mantequilla sustituya al aceite no implica lo contrario.

### Comunidad

- **`user_favorite`** — PK `(user_id, recipe_id)`, `created_at`.
- **`recipe_contribution`** — `recipe_id`, `submitted_by`, `status`
  (`pending`,`approved`,`rejected`), `review_notes`, `reviewed_by`, `reviewed_at`.
- **`recipe_revision`** — `recipe_id`, `revision_number`
  (`UNIQUE (recipe_id, revision_number)`), `snapshot JSONB`, `change_summary`,
  `created_by`. **Por qué JSONB aquí:** la revisión es una *foto histórica*
  inmutable; la receta canónica sigue siendo estructurada. Guardar el historial
  normalizado multiplicaría las tablas sin aportar consultas útiles.

### Ingesta (Fase 4)

- **`ingestion_job`** — `idempotency_key` **UNIQUE**, `status`
  (`queued`,`running`,`needs_review`,`completed`,`failed`), `source_url`,
  `raw_input`, `provider`, `attempts`, `last_error`, `result_recipe_id`,
  `created_by`.
- **`ingestion_issue`** — errores/advertencias de validación por job:
  `severity` (`info`,`warning`,`error`), `code`, `message`, `field_path`.
- **`duplicate_candidate`** — `recipe_id`, `candidate_recipe_id`,
  `similarity` (0–1), `reason`, `status` (`open`,`confirmed`,`dismissed`).
  `UNIQUE (recipe_id, candidate_recipe_id)`.

## Reglas de integridad (resumen)

1. Ingredientes normalizados: `ingredient.normalized_name` y
   `ingredient_alias.normalized_alias` únicos.
2. Cantidad y unidad separadas del ingrediente (`recipe_ingredient`).
3. Unidades estandarizadas mediante FK a `unit`.
4. Opcionales distinguibles (`is_optional`).
5. Procedencia preservada (`recipe_source`).
6. Nada de recetas como texto libre: pasos, ingredientes y metadatos en tablas.
7. Índices en todas las FK usadas en filtros/joins.
8. Sin ingredientes duplicados dentro del mismo grupo de una receta.

## Búsqueda

Fase 2 usa PostgreSQL estándar: `ILIKE` + `pg_trgm` (similitud y tolerancia a
errores tipográficos) sobre `recipe.title` e `ingredient.normalized_name`.
No se introducen embeddings ni búsqueda vectorial hasta que exista un problema
real que lo justifique.

## Seeds

`apps/api/seeds/*.json` contiene datos **de desarrollo** (unidades, categorías,
ingredientes de ejemplo). El catálogo de unidades sí es de referencia y se usa en
producción. Las recetas de ejemplo se marcan con `origin_type = curated` y una
fuente `source_type = original` que indica "Datos de ejemplo de Miseo".
