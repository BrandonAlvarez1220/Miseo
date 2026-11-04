# Imágenes de recetas y cócteles (propuesta para revisión)

> Estado: **diseño**. El frontend ya soporta `image_url` de punta a punta (si existe
> se muestra; si no, la ilustración por categoría o la animación del cóctel).

## Objetivos

1. Cada receta y cóctel con una imagen atractiva y **coherente** con el resto.
2. **Procedencia siempre registrada**: quién la hizo, con qué licencia, si es de IA.
3. La IA es **opcional y asíncrona**: las imágenes se generan una vez y se guardan;
   la app nunca llama a un modelo al servir una página (sigue siendo gratis y
   funciona sin IA).
4. Nada se publica sin revisión humana.

## Modelo de datos propuesto

`recipe.image_url` es insuficiente: no guarda procedencia. Se propone:

```
recipe_image (
  id, recipe_id,
  storage_path, width, height, alt_text,
  source_type: original_photo | community_upload | ai_generated | open_license,
  source_name, source_url, license, attribution,
  generator,        -- p. ej. "gemini-<modelo>" si es de IA
  prompt,           -- prompt usado (reproducibilidad)
  status: pending | approved | rejected,
  created_by, reviewed_by, created_at
)
recipe.cover_image_id → recipe_image (solo imágenes approved)
```

## Fuente 1 — Generación con tu agente de Gemini

```
Agente Gemini (fuera de la app)
   1. GET  /api/v1/recipes/{slug}           ← datos estructurados de la receta
   2. Construye el prompt con la guía de estilo (abajo)
   3. Genera la imagen
   4. POST /api/v1/admin/recipes/{slug}/images   (token de servicio con scope "images")
        → la API valida formato/tamaño, sube a Supabase Storage,
          crea recipe_image(status=pending, source_type=ai_generated, generator, prompt)
   5. Un moderador aprueba en el panel → pasa a portada
```

- **Por qué el agente usa la API y no escribe en la BD:** la API ya tiene la
  validación, los permisos y la moderación. Un agente con acceso directo a la BD
  se saltaría todo eso.
- **Transparencia:** en la web se muestra la etiqueta "Imagen generada con IA".
  Una imagen generada no es una foto del plato real; presentarla como tal
  engañaría al usuario (mismo principio que no presentar recetas inventadas
  como clásicas).
- **Proveedor intercambiable:** el endpoint acepta la imagen ya generada, así que
  da igual si viene de Gemini, de otro modelo o de una persona.

### Guía de estilo para el prompt (coherencia visual)

Plantilla construida con los datos de la receta, no texto libre:

```
Fotografía gastronómica de {title}. {ingredientes visibles principales}.
{Cocina: plato hondo/llano de cerámica clara | Barra: servido en {glass}, garnish {garnish}}.
Luz natural lateral suave, fondo neutro claro, ángulo 45°, poca profundidad de campo,
estilo editorial limpio, sin texto, sin marcas, sin manos, sin logos.
```

Mismos ángulo, luz y fondo para todo el catálogo → la galería se ve coherente
aunque se generen en días distintos.

## Fuente 2 — "Que busque y la ponga": solo con licencias abiertas

Aquí hay un riesgo legal: **la mayoría de imágenes de internet tienen derechos de
autor**. Que un agente las descargue de buscadores y las publique sería infringirlos,
aunque el proyecto sea gratuito.

Se puede hacer bien limitando la búsqueda a fuentes con licencia explícita y API:

| Fuente | Licencia | Requisitos |
| --- | --- | --- |
| Wikimedia Commons | CC BY / CC BY-SA / dominio público | Atribución; CC BY-SA obliga a compartir igual |
| Openverse (buscador de contenido CC) | Varias CC | Guardar la licencia exacta de cada imagen |
| Unsplash API / Pexels API | Licencias propias permisivas | Atribución al autor; respetar sus términos de API |

Reglas para el agente:
1. Solo esas fuentes; nunca resultados de buscadores generales.
2. Guardar `source_url`, `license`, `attribution` de cada imagen.
3. Si la licencia no se puede determinar → descartar.
4. Comprobar que la imagen corresponde de verdad a la receta (un humano lo valida
   en la moderación).

## Fuente 3 — Comunidad

Subidas de usuarios (Fase 3) con validación de tipo MIME real, tamaño máximo,
eliminación de metadatos EXIF (ubicación) y moderación.

## Frontend

- `next/image` con el dominio de Supabase Storage configurado y placeholder borroso.
- Texto alternativo (`alt_text`) obligatorio.
- Etiqueta visible según `source_type` (IA, comunidad, licencia abierta + atribución).
- Si no hay imagen aprobada: ilustración por categoría (cocina) o animación (cócteles).

## Orden de implementación sugerido

1. Tabla `recipe_image` + migración de `image_url` existente.
2. Endpoint de subida para administradores/servicio + panel de moderación de imágenes.
3. Conectar el agente de Gemini a ese endpoint con un token de servicio.
4. Búsqueda en fuentes con licencia abierta (Openverse/Wikimedia) como alternativa.
