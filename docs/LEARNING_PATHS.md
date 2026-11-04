# Rutas de aprendizaje (propuesta para revisión)

> Estado: **diseño**. Nada de esto está implementado todavía.

## Idea: una escalera de platillos

Cada ruta es una **escalera de platillos reales** que va de lo sencillo a lo
complejo: una sopa fácil, luego un bistec con nopales, luego algo con más pasos…
Las habilidades **no se estudian por separado**: se aprenden cocinando. Cada
platillo dice "esto es lo que aprendes aquí" (tiempos de cocción, sellar una
carne, hacer una salsa asada…), y al avanzar se van acumulando.

**Por qué así:** la motivación es el plato que te vas a comer, no un ejercicio de
técnica. Además, una habilidad aparece por primera vez en un platillo fácil y se
repite en platillos más difíciles, que es como se aprende en una cocina de verdad.

Lo que **no** queremos: "Nivel 0: picar. Nivel 5: picas perfecto".

## Cómo se ve para el usuario

```
Ruta de cocina · Etapa 2 "Comida de casa"            3 de 5 platillos
┌──────────────────────────────────────────────────────────────┐
│ ✓ Arroz rojo            ✓ Frijoles de la olla                 │
│ ▶ Bistec con nopales    · Fácil · 30 min                      │
│     Aprendes: sellar carne a fuego alto · asar nopales        │
│               sin que babeen · tiempo de cocción del bistec   │
│ ○ Pasta al pomodoro     ○ Lentejas guisadas                   │
└──────────────────────────────────────────────────────────────┘
Habilidades que ya tienes: picar cebolla y jitomate · sofreír ·
arroz por absorción · cocción larga de frijol …
```

- Cada platillo es una **receta normal del catálogo** (con su detalle, porciones,
  sustituciones…), no contenido aparte.
- "Lo que aprendes" sale de etiquetar las recetas con habilidades.
- La primera vez que aparece una habilidad, la receta incluye un **tip** que la
  explica ("cómo saber si el aceite está listo para sellar").
- Para pasar de etapa no hace falta completarlo todo: basta con unos cuantos
  platillos. Nadie se queda atascado por un platillo que no le apetece.

## Ruta de cocina — "Del primer platillo a cocinero con oficio"

✓ = ya existe en el catálogo · ＋ = receta nueva por escribir

| Etapa | Platillos | Lo que se aprende por el camino |
| --- | --- | --- |
| **1. Sin miedo a la estufa** | ＋ Huevos a la mexicana · ＋ Sopa de fideo · ＋ Quesadillas · ✓ Guacamole · ✓ Pico de gallo · ✓ Ensalada caprese | Picar cebolla y jitomate · fuego medio vs alto · sofreír jitomate para un caldillo · sazonar probando |
| **2. Comida de casa** | ＋ Arroz rojo · ＋ Frijoles de la olla · ＋ Bistec con nopales · ✓ Pasta al pomodoro · ✓ Lentejas guisadas | Arroz por absorción (tostar, tapar, no mover) · cocción larga de leguminosas · sellar carne · asar nopales sin baba · tiempos de cocción |
| **3. Sabores con más pasos** | ＋ Caldo de pollo · ＋ Chilaquiles rojos · ✓ Huevos rancheros · ✓ Pollo al limón · ✓ Salmón al horno · ✓ Tortilla de patatas | Hacer un caldo · salsa asada y licuada · punto de la proteína (que no se seque) · voltear sin miedo |
| **4. De fin de semana** | ✓ Arroz con pollo · ＋ Tinga de pollo · ＋ Enchiladas verdes · ＋ Crema de calabaza · ✓ Panqueques | Deshebrar · salsas cocidas · coordinar varias preparaciones a la vez · cremas lisas |
| **5. Retos** | ＋ Pozole rojo · ＋ Lasaña con bechamel · ＋ Flan napolitano · ＋ Pan de caja casero | Chiles secos (desvenar, tostar, hidratar) · roux y bechamel · baño maría · masas y fermentación · planear tiempos largos |
| **6. Oficio** | ＋ Mole (versión casera) · Menú de 3 tiempos · Cocinar sin receta con **¿Qué puedo preparar?** | Equilibrar sal, ácido, grasa y picante · adaptar recetas · improvisar con lo que hay |

## Ruta de barra — "Del primer highball a bartender con criterio"

| Etapa | Tragos | Lo que se aprende por el camino |
| --- | --- | --- |
| **1. Mis primeros tragos** | ✓ Cuba Libre · ✓ Moscow Mule · ＋ Paloma · ✓ Limonada de menta y jengibre | Medir con jigger · el hielo importa · construir en el vaso · la soda va al final |
| **2. Los sours** | ✓ Daiquiri · ✓ Margarita · ✓ Mojito · ✓ Mojito sin alcohol | Batir y colar · el equilibrio dulce/ácido · machacar sin amargar · escarchar |
| **3. Más técnica** | ✓ Whiskey Sour · ✓ Hemingway Special · ＋ Carajillo | Dry shake (espuma de clara) · variaciones de un clásico · batir con café |
| **4. Tragos de espirituosos** | ✓ Negroni · ✓ Old Fashioned · ＋ Manhattan · ＋ Martini | Remover y diluir · temperatura · perfumar con piel de cítrico |
| **5. Preparaciones de la casa** | ＋ Jarabe de jamaica · ＋ Margarita de tamarindo · ＋ Agua de jamaica con soda (sin alcohol) | Jarabes caseros · usar ingredientes locales · adaptar plantillas |
| **6. Tu firma** | Crea tu variación y documéntala | Pensar en plantillas (sour, highball, old fashioned) · libreta de especificaciones |

Notas:
- Toda la ruta de barra lleva un aviso de **consumo responsable y mayoría de edad**,
  y en cada etapa hay al menos una alternativa sin alcohol.
- Las creaciones de la etapa 6 se clasifican como `contemporary` o `experimental`,
  nunca como clásicos.
- Las especificaciones de los clásicos se verifican contra la fuente antes de
  publicarlas (ver nota sobre IBA).
- La **animación de cócteles** sirve directamente como material de las etapas 1–4.

## Modelo de datos

La ruta apunta a recetas; las habilidades son **etiquetas** de las recetas.

```
skill          (slug, name, discipline: cooking|bar, tip_md)   ← "sellar carne", "dry shake"
recipe_skill   (recipe_id, skill_id, first_time_tip: bool)      ← N:M, "lo que aprendes"
learning_path  (slug, title, discipline, description)
path_stage     (path_id, position, title, description, dishes_to_unlock)
path_dish      (stage_id, position, recipe_id)                 ← los platillos de la escalera
user_progress  (user_id, recipe_id, cooked_at, rating?)        ← Fase 3 (requiere login)
```

- "Habilidades que ya tienes" = habilidades de las recetas que el usuario marcó
  como cocinadas. No hay exámenes de técnica.
- `dishes_to_unlock` permite avanzar sin completar todos los platillos de la etapa.
- Antes del login, el progreso se guarda solo en el navegador; con cuenta, se
  sincroniza.
- Las rutas son datos (seeds versionados), no código.

## Orden de implementación sugerido

1. Escribir las recetas ＋ de las etapas 1–2 (son las que más usuarios van a cocinar).
2. Tablas + seeds de las dos rutas; etiquetar habilidades en las recetas existentes.
3. Páginas `/rutas`, `/rutas/cocina`, `/rutas/barra` y la sección "Lo que aprendes"
   en el detalle de cada receta.
4. Progreso local → progreso en la cuenta (Fase 3).
5. Etapas 3–6 de forma incremental.
