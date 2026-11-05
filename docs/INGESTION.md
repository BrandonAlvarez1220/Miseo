# Ingesta de recetas por agentes: diseño

Guía práctica para los agentes: [`AGENT_GUIDE.md`](AGENT_GUIDE.md). Identidades y tokens:
[`AUTH.md`](AUTH.md).

## Reparto de trabajo

| Quién | Qué | Por qué |
| --- | --- | --- |
| **Agente** (opencode, Claude, Gemini) | Buscar, leer, reescribir, estructurar | Es la parte difusa: necesita un modelo de lenguaje |
| **API** (determinista, sin IA) | Validar, mapear, puntuar, detectar duplicados, encolar | Debe ser predecible y comprobable; **no se confía en un LLM para esto** |
| **Persona** (moderador/admin) | Aprobar o rechazar | Nada generado por IA se publica sin revisión |

Por eso la app **sigue siendo útil sin ningún agente conectado**, y el scraping/LLM nunca
corre dentro del servidor: la API solo recibe datos ya estructurados.

## Flujo

```
Agente ──POST /agent/submissions──▶ validar (Pydantic, estricto)
                                    ├─ mapear ingredientes y unidades al catálogo
                                    ├─ dificultad 1-5, habilidades, etapa sugerida
                                    ├─ duplicados (catálogo y envíos pendientes)
                                    └─ guardar en estado `needs_review`  ← NADA público aún
Moderador ─ /review/submissions ──▶ aprobar ─▶ crea la receta PUBLICADA (origin: ai_assisted)
                                  └▶ rechazar ─▶ el agente lee el motivo
```

## Idempotencia y reintentos

La clave sale de la URL canónica (o de título + fuente + tipo) y es `UNIQUE` en la base de datos.

| Situación | Resultado |
| --- | --- |
| Misma clave, mismo agente, en revisión, contenido distinto | `updated` (corrige; máx. 5 revisiones) |
| Misma clave y contenido idéntico | `unchanged`, sin reanalizar ni gastar una revisión |
| Misma clave, otro agente | `unchanged`: no puede pisar el envío de otro |
| Misma clave, ya aprobada/rechazada | `unchanged`: una receta rechazada no se reintenta |
| Dos envíos simultáneos | La restricción `UNIQUE` decide; el perdedor recibe el existente |

## Reglas deterministas

**Validación:** esquema estricto (`extra=forbid`), texto sin caracteres de control ni
invisibles (bloquea los de dirección de escritura), URLs `http(s)`, `website` exige URL
(nunca se inventan fuentes), una receta de cocina no admite datos de bebida y viceversa.

**Ingredientes:** coincidencia **exacta** por nombre normalizado, alias o `ingredient_slug`.
Lo difuso solo se ofrece como *candidato* al revisor: mapear "ajo en polvo" a "ajo" en
silencio cambiaría la receta. El mismo ingrediente dos veces en un grupo se rechaza (422).

**Unidades:** códigos del catálogo o sinónimos en español/inglés (`gramos`, `cdas`, `cups`).
Cantidades implausibles (> 20 kg/l, > 100 piezas) y faltantes se marcan como aviso.

**Dificultad (1-5)** = puntos por nº de pasos + ingredientes principales (sin básicos) +
tiempo total + técnicas reconocidas en el texto (sellar, emulsionar, amasar…). Es una
**heurística de orden**, no una verdad: las recetas caseras sencillas salen 1-2 (acertado),
así que **no sirve para colocar por sí sola** una receta en una etapa.

**Habilidades:** reglas en `apps/api/seeds/skill_keywords.json` (datos, no código) sobre los
pasos, nombres y notas de ingredientes. Medido contra las 30 recetas etiquetadas a mano:
cobertura ≈ 71 %, precisión ≈ 59 %. Son **sugerencias** que el revisor confirma.

**Etapa sugerida** (`placement.py`): la primera etapa donde ya se enseñan las habilidades
de la receta; la dificultad es un techo de seguridad (mucho más difícil que la etapa →
siguiente, o "etapa nueva"); las habilidades que ninguna etapa enseña se listan como
nuevas para la ruta.

**Duplicados:** título parecido (trigram, ≥ 0.55), mismos ingredientes principales
(Jaccard ≥ 0.8) y títulos parecidos entre envíos **pendientes** de distintos agentes.

**Cócteles:** un agente nunca crea un clásico documentado; entran como `experimental` (o
`contemporary` si lo declara). Una persona puede marcarlo `classic` solo si la fuente no es
`ai_generated`. `variation` exige una receta padre y aún no se puede asignar al aprobar.

## Límites por agente

60 envíos nuevos/hora y 200 pendientes (HTTP 429 con `Retry-After`); 5 revisiones por envío
(409). Se cuentan en PostgreSQL: sin infraestructura extra. Configurables:
`AGENT_MAX_SUBMISSIONS_PER_HOUR`, `AGENT_MAX_PENDING`, `AGENT_MAX_REVISIONS`.

## Aprobar

`POST /review/submissions/{id}/approve` (moderador o admin) crea en **una transacción**: la
receta (publicada, `ai_assisted`, `created_by` vacío porque un agente no es un usuario),
ingredientes, pasos, fuente con su licencia y atribución, categorías, habilidades, un
`recipe_revision` y, si se pide, un hueco en una etapa de una ruta. Para aprobar, cada línea
debe resolverse:

- `ingredient_mappings`: línea → slug existente,
- `new_ingredients`: línea → **crear** un ingrediente nuevo (rechazado si ya existe como
  nombre, slug o alias; así el catálogo crece sin duplicarse),
- `unit_mappings`: línea → código de unidad.

Si algo falla, no queda nada creado (ni siquiera el ingrediente nuevo).

## Limitaciones conocidas

- La detección de duplicados ignora ingredientes sin mapear, así que "Paloma de jamaica" se
  marcó como casi igual a "Paloma" (el agua de jamaica no contaba).
- No se pueden crear etapas nuevas al aprobar (decisión editorial); solo colocar en las
  existentes. La API sugiere "etapa nueva" cuando una receta es más difícil que todas.
- No hay imágenes en este flujo (ver `IMAGES.md`).
- Los envíos pendientes entre agentes se comparan por título; no por ingredientes.
- Las reglas de habilidades se ajustaron con 30 recetas: conviene revisarlas con más datos.
- No se verifica que el contenido sea fiel a la fuente ni que su licencia permita reutilizarlo:
  eso lo comprueba la persona que revisa (`license_unknown` avisa cuando falta).
