# Rutas de aprendizaje (propuesta para revisión)

> Estado: **diseño**. Nada de esto está implementado todavía. Revisa el temario
> antes de construirlo: es contenido, y el contenido define el producto.

## Idea

Dos rutas que llevan a alguien desde cero hasta tener **oficio** (no un título
profesional): saber trabajar con criterio, improvisar y no depender de una receta.

- **Cocina:** del primer huevo a cocinero con oficio.
- **Barra:** de tu primer highball a bartender casero con criterio.

Cada ruta tiene **niveles**. Cada nivel enseña **habilidades** (cortar, sellar,
batir…) y las practica con **recetas reales del catálogo**, y termina con un
**reto** que demuestra que la habilidad se aprendió (p. ej. "prepara un sour sin
mirar la receta").

### Por qué habilidades + recetas (y no solo una lista de recetas)

Una receta enseña a hacer *un* plato; una habilidad se transfiere a cientos. Si
cada receta declara qué habilidades practica (`recipe_skill`), la ruta puede:
- recomendar "la siguiente receta que te enseña algo nuevo";
- mostrar en cada receta "esta receta practica: sellar, desglasar";
- medir progreso por habilidades, no por número de platos.

## Modelo de datos propuesto

```
skill            (slug, name, discipline: cooking|bar, family, description, how_to JSONB pasos)
recipe_skill     (recipe_id, skill_id, emphasis: introduces|practices)   ← N:M
learning_path    (slug, title, discipline, description)
path_level       (path_id, position, title, goal, challenge)
path_item        (level_id, position, kind: skill|recipe|lesson, skill_id?, recipe_id?, lesson_id?, required)
lesson           (slug, title, body_md, discipline)   ← teoría corta: seguridad, mise en place...
user_progress    (user_id, path_item_id, completed_at)   ← Fase 3 (requiere login)
```

- `bartending_technique` (ya existe) se enlaza con `skill` en lugar de duplicarse.
- Antes del login, el progreso puede guardarse **solo en el navegador** como
  comodidad; con cuenta, se sincroniza en `user_progress`.
- Las rutas son datos (seeds versionados), no código: la comunidad podrá proponer
  mejoras con el mismo flujo de moderación.

## Ruta de cocina — "Del primer huevo a cocinero con oficio"

| Nivel | Objetivo | Habilidades | Práctica (✓ ya en catálogo · ＋ nueva) | Reto |
| --- | --- | --- | --- | --- |
| 0. Mise en place | Trabajar ordenado y seguro | Higiene y contaminación cruzada, agarre del cuchillo y "garra", picado, juliana, brunoise | ✓ Pico de gallo · ✓ Guacamole · ✓ Ensalada caprese | Pico de gallo con cortes parejos en < 15 min |
| 1. Huevos | Dominar el calor | Hervir (tiempos), revuelto cremoso, frito, tortilla francesa | ✓ Huevos rancheros · ✓ Panqueques · ✓ Tortilla de patatas · ＋ Huevos revueltos | Tortilla francesa sin dorar |
| 2. Granos y legumbres | Absorción y punto | Arroz por absorción, pasta al dente, legumbres sin remojo/con remojo | ✓ Pasta al pomodoro · ✓ Lentejas · ＋ Arroz blanco | Arroz suelto sin receta |
| 3. Sofrito, sopas y fondos | Construir sabor por capas | Sofrito, caldo casero, cremas, sazonar en capas | ✓ Sopa de tomate · ＋ Caldo de pollo · ＋ Crema de calabaza | Sopa con lo que haya en la nevera |
| 4. Proteínas | Punto de cocción | Sellar, reposar, termómetro, desglasar, horno | ✓ Pollo al limón · ✓ Salmón al horno · ✓ Arroz con pollo | Pollo jugoso al punto con salsa de sartén |
| 5. Salsas y emulsiones | Equilibrio y textura | Vinagreta, mayonesa, roux y bechamel, reducción | ＋ Vinagreta · ＋ Mayonesa · ＋ Bechamel | Salsa que "salve" un plato soso |
| 6. Horno y masas | Precisión | Pesar, gluten, fermentación básica, masas quebradas | ＋ Pan rápido · ＋ Bizcocho · ＋ Masa quebrada | Bizcocho que sube parejo |
| 7. Oficio | Autonomía | Equilibrar sal/ácido/grasa/calor, adaptar recetas, planificar un menú, cocinar con la despensa | Usa **¿Qué puedo preparar?** en modo Descubrir | Menú de 3 tiempos con lo que tienes |

## Ruta de barra — "De tu primer highball a bartender con criterio"

| Nivel | Objetivo | Habilidades | Práctica | Reto |
| --- | --- | --- | --- | --- |
| 0. Fundamentos | Medir y servir | Herramientas (jigger, coctelera, colador), hielo, cristalería, construir | ✓ Cuba Libre · ✓ Moscow Mule · ✓ Limonada de menta y jengibre | Highball con medidas exactas |
| 1. Sours | Equilibrio dulce/ácido | Batido, colado doble, proporción sour 2 : ¾ : ¾, dry shake | ✓ Daiquiri · ✓ Margarita · ✓ Whiskey Sour | Ajustar un sour que sale demasiado ácido |
| 2. Machacados | Extraer sin amargar | Machacar, hielo picado, completar con soda | ✓ Mojito · ✓ Mojito sin alcohol | Mojito sin hojas rotas |
| 3. Mezclados | Dilución y temperatura | Remover, enfriar, piel de cítrico | ✓ Negroni · ✓ Old Fashioned · ＋ Manhattan · ＋ Martini | Negroni con dilución correcta |
| 4. Preparaciones | Ingredientes propios | Jarabes (simple, rico, miel, jengibre), oleo saccharum, infusiones | ＋ Jarabe de jengibre · ＋ Jarabe de miel | Crear un jarabe y usarlo en un sour |
| 5. Variaciones | Pensar en plantillas | Plantillas (sour, highball, old fashioned), sustituir con criterio, libreta de specs | ✓ Hemingway Special (variación del Daiquiri) | Crear tu variación y documentarla |
| 6. Sin alcohol y hospitalidad | Servir bien | Mocktails con estructura, presentación, servicio, consumo responsable | ✓ Mojito sin alcohol · ✓ Limonada | Carta de 3 bebidas para una reunión |

Notas de producto:
- Las creaciones del nivel 5 se clasifican como `contemporary`/`experimental`, nunca
  como clásicas.
- Ruta de barra con aviso de **consumo responsable** y edad legal; todos los niveles
  tienen alternativa sin alcohol.
- La **animación de cócteles** ya sirve como material didáctico de los niveles 0–3
  (paso a paso con controles).

## Orden de implementación sugerido

1. Tablas `skill`, `recipe_skill`, `learning_path`, `path_level`, `path_item`, `lesson`
   + seeds de las dos rutas con las recetas ya existentes (✓).
2. Páginas `/rutas`, `/rutas/cocina`, `/rutas/barra` y nivel; "esta receta practica…"
   en el detalle.
3. Progreso local (navegador) → progreso en cuenta (Fase 3).
4. Recetas nuevas (＋) por niveles, con atribución.
