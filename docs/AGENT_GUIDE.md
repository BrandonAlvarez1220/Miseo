# Guía para agentes de ingesta (opencode, Claude, Gemini…)

Esta guía es para el **agente** (y para ti al configurarlo). Cualquier agente que pueda
hacer peticiones HTTP con una cabecera `Authorization: Bearer …` sirve.

Idea: el agente hace la parte difusa (buscar una receta, leerla, **reescribirla con
sus palabras**) y la API hace la parte determinista (validar, mapear ingredientes y
unidades, puntuar dificultad, detectar duplicados). **Nada se publica solo**: cada
envío espera a que una persona lo apruebe.

## 1. Conectar un agente

**Desde la web (lo más cómodo):** entra como administrador (en local, `/ingresar` con
`admin@example.com`), abre **Agentes** en la barra superior (`/admin/agentes`), elige un nombre
y la herramienta y pulsa *Crear y obtener token*. El token se muestra **una sola vez**, con botón
de copiar. Desde la misma pantalla puedes **revocar** un agente.

**Con la API**, como administrador:

```bash
curl -X POST $API/api/v1/admin/agents \
  -H "Authorization: Bearer $TU_TOKEN_DE_ADMIN" -H "Content-Type: application/json" \
  -d '{"name": "Claude recetas MX", "provider": "claude"}'
# → {"token": "mis_ag_..."}   se muestra UNA sola vez
```

Crea **un agente por herramienta** (`opencode`, `claude`, `gemini`) para saber de cuál
viene cada receta y poder revocar uno sin afectar a los demás. Guarda el token como
variable de entorno o en el gestor de secretos del agente (`MISEO_AGENT_TOKEN`):
**nunca en el repositorio ni en un prompt compartido**.

Comprobar que funciona: `GET /api/v1/agent/me`.

## 2. Flujo de trabajo del agente

1. **Mirar el catálogo** (público, sin token):
   `GET /ingredients?q=pollo` · `GET /units` · `GET /categories?recipe_type=cooking` ·
   `GET /mixology/glass-types` · `GET /mixology/techniques`.
2. **Buscar y leer una receta** en una fuente que permita reutilizarla.
3. **Reescribirla con palabras propias** y estructurarla (formato de abajo).
4. `POST /api/v1/agent/submissions`.
5. **Leer la respuesta**: `issues` (qué corregir) y `analysis` (dificultad, habilidades,
   etapa sugerida, duplicados). Corrige los `error` y reenvía.
6. Una persona lo revisa en **Revisión** (`/revision`). Consulta el resultado: `GET /api/v1/agent/submissions/{id}` (aprobada → `recipe_slug`;
   rechazada → `review_notes` con el motivo; **léelo y no la reenvíes igual**).

## 3. Reglas que no se negocian

- **Nunca inventes una fuente.** `source.name` y, si es un sitio web, `source.url`, deben
  ser reales. Una receta propia del agente se declara `source_type: "ai_generated"`.
- **No copies texto.** Los ingredientes y cantidades son datos; la redacción de los pasos
  no. Reescribe con tus palabras y rellena `license` y `attribution` si la fuente los indica.
- **No se aceptan imágenes** en este flujo.
- **Respeta `robots.txt` y los términos de la fuente.** Si no permiten reutilizar su
  contenido, no la envíes.
- **No adivines cantidades.** Si la fuente no la da, omite `quantity` y cuéntalo en
  `agent_notes`; no inventes un número.
- **Cócteles:** nunca serán "clásicos" por tu declaración. `claimed_classification` es
  informativo; entran como `experimental`/`contemporary` hasta que una persona verifique.
- Una receta por envío. Límites por agente: 60 envíos nuevos/hora y 200 pendientes.

## 4. Formato del envío

```json
{
  "source": {
    "name": "Nombre del sitio, libro o autor",
    "url": "https://ejemplo.com/receta",
    "source_type": "website",
    "license": "CC BY-SA 4.0",
    "attribution": "Cómo se debe citar"
  },
  "recipe": {
    "title": "Chilaquiles rojos",
    "description": "Una frase.",
    "introduction": null,
    "tips": null,
    "recipe_type": "cooking",
    "servings": 2,
    "preparation_time_minutes": 10,
    "cooking_time_minutes": 20,
    "categories": ["desayunos"],
    "ingredients": [
      {"name": "tortillas de maíz", "quantity": 8, "unit": "piezas", "notes": "en triángulos"},
      {"name": "tomate", "ingredient_slug": "tomate", "quantity": 4, "unit": "piece"},
      {"name": "sal", "unit": "al gusto"}
    ],
    "steps": ["Primer paso…", "Segundo paso…"]
  },
  "agent_notes": "Dudas para quien revise (opcional)."
}
```

Para un cóctel, `"recipe_type": "drink"` y un bloque obligatorio:

```json
"drink": {"is_alcoholic": true, "base_spirit": "tequila", "glass": "highball",
          "technique": "construido", "garnish": "Rodaja de lima"}
```

Detalles:
- `source_type`: `website` (exige `url`), `book`, `community`, `original`, `ai_generated`, `other`.
- `unit`: acepta el código (`g`, `ml`, `tbsp`…) o nombres comunes (`gramos`, `cucharadas`, `tazas`).
- `ingredient_slug`: opcional pero **preferible** si lo encontraste con `GET /ingredients`.
- Un mismo ingrediente no puede repetirse en el mismo `group`; usa `group` ("Para la salsa") si
  aparece en dos partes de la receta.
- Los campos desconocidos se rechazan (un `ingridients` mal escrito da error, no se ignora).

## 5. Qué devuelve y cómo reaccionar

`201` = creado; `200` = actualizado o ya enviado (mira `outcome`).

| `outcome` | Significa |
| --- | --- |
| `created` | Nuevo envío en revisión |
| `updated` | Corregiste un envío tuyo que seguía en revisión (máx. 5 revisiones) |
| `unchanged` | Ya existía (misma fuente) o enviaste exactamente lo mismo; no pasó nada |

**Idempotente:** la misma URL (ignorando mayúsculas del dominio, `/` final, `utm_*`, `fbclid`
y `#fragmento`) es siempre el mismo envío. Reintentar tras un fallo de red es seguro.

`issues`, de más a menos grave:

| Código | Gravedad | Qué hacer |
| --- | --- | --- |
| `unknown_ingredient` | error | Mira `candidates` en el mensaje; usa `ingredient_slug` o deja que el moderador lo cree |
| `unknown_unit` | error | Usa un código de `GET /units` |
| `missing_quantity`, `missing_unit`, `implausible_quantity` | warning | Revisa si es un error de lectura |
| `unknown_category`, `no_category`, `unknown_glass`, `unknown_technique` | warning | Usa los slugs de los catálogos |
| `possible_duplicate` | warning | Probablemente ya existe: ¿merece la pena enviarla? |
| `license_unknown`, `missing_time`, `short_steps` | warning | Completa si la fuente lo dice |
| `classification_downgraded` | info | Esperado en cócteles |

Los `error` no impiden el envío (queda en revisión) pero **bloquean la aprobación** hasta que
un moderador mapee o cree el ingrediente. Cuantos menos `error`, menos trabajo humano.

## 6. Texto para pegar en el agente

> Eres un agente de ingesta para Miseo, un recetario abierto y comunitario. Tu tarea:
> buscar recetas (de cocina casera o cócteles) en fuentes que permitan reutilizarlas,
> reescribirlas **con tus propias palabras** y enviarlas a la API siguiendo `AGENT_GUIDE.md`.
> Antes de cada envío consulta `GET /ingredients`, `/units`, `/categories`.
> Reglas: nunca inventes fuentes ni cantidades; no copies texto ni imágenes; respeta robots.txt
> y los términos de cada sitio; declara `license` y `attribution` si existen; una receta por
> envío. Lee `issues` en la respuesta y corrige los `error` antes de reenviar. No reenvíes algo
> rechazado sin leer `review_notes`. Tu token está en la variable `MISEO_AGENT_TOKEN`.
> Nada se publica sin revisión humana: no pidas que se salten la revisión.
