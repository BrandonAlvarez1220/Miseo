# Design system

Dos mundos, un sistema: **Cocina** (claro, fresco, ordenado: blanco, verde y
naranja) y **Mixología** (nocturno: grafito con ámbar). Ambos comparten
componentes; solo cambian los *tokens* de color.

> Dirección visual inspirada en interfaces tipo *app* de recetas (barra lateral,
> búsqueda fija, tarjetas con datos), con identidad propia de Miseo.

## Estructura de la app (app shell)

| Zona | Escritorio (`lg` ≥ 1024 px) | Móvil |
| --- | --- | --- |
| Navegación | Barra lateral fija (marca, menú, tarjeta "open source") | Barra de pestañas inferior |
| Barra superior | Acciones globales (búsqueda) | Marca + acciones |
| Contenido | `PageHeader` + secciones | Igual, una columna |

La navegación activa usa `usePathname()` dentro de `<Suspense>` con un
*fallback* sin estado activo. **Por qué:** con Cache Components, leer la ruta en
un layout compartido se suspende al prerenderizar rutas dinámicas
(`/recetas/[slug]`); sin el boundary, la build falla.

## Cómo funciona el cambio de "mundo"

Los valores viven en variables CSS (`apps/web/app/globals.css`). Tailwind las lee
con `@theme inline`, de modo que `bg-canvas` o `text-primary` resuelven al valor
del contexto. `MixologyRegion` (`data-theme="mixology"`) redefine las variables
para su subárbol:

```tsx
<MixologyRegion className="min-h-full">…</MixologyRegion>
```

Cada página decide si lo usa (no se deduce de la URL): así el detalle de un cóctel
puede ser oscuro aunque viva en `/recetas/...`. **Por qué así:** evita duplicar
componentes (`ButtonDark`, `CardMixology`, ...) y un componente nuevo funciona en
ambos mundos sin esfuerzo.

## Color

| Token | Cocina | Mixología | Uso |
| --- | --- | --- | --- |
| `canvas` | `#f6f7f5` | `#121418` | Fondo de página |
| `surface` | `#ffffff` | `#1b1e24` | Tarjetas, barra lateral |
| `surface-muted` | `#f0f2ef` | `#252930` | Skeletons, estados vacíos, hover |
| `ink` | `#17181a` | `#f3f4f6` | Texto principal |
| `ink-muted` | `#686d74` | `#a3a9b4` | Texto secundario |
| `line` | `#e6e8e4` | `#2d323b` | Bordes finos de tarjetas |
| `primary` | `#168a4a` verde | `#f0a93b` ámbar | Acciones, estado activo |
| `primary-soft` | `#e5f3ea` | `#3a2e1a` | Fondos de chips y navegación activa |
| `accent` | `#f0642f` naranja | `#ec6d93` | Marca, destacados, iconos |
| `accent-ink` | `#b9420f` | `#f59ab6` | Texto sobre fondos claros con acento |
| `notice` / `notice-soft` | `#b7791f` / `#fdf6e7` | — | Avisos (banners informativos) |
| `danger` | `#b42318` | `#f97066` | Errores |

Los pares texto/fondo principales cumplen WCAG AA (≥ 4.5:1). El naranja de acento
no se usa para texto pequeño sobre blanco (≈ 3:1); para eso existe `accent-ink`.

## Tipografía

- **Plus Jakarta Sans** para todo: geométrica, cercana y muy legible en móvil.
- Los títulos de página combinan dos pesos (`font-light` + `font-bold`) en dos
  líneas — `PageHeader` lo resuelve.
- El token `--font-display` sigue existiendo (hoy apunta a la misma familia) para
  poder separar la tipografía de títulos sin tocar componentes.

## Espaciado, radios y sombras

- Espaciado: escala de Tailwind (múltiplos de 4 px). Secciones separadas por
  `space-y-20`; *gutters* `px-4 sm:px-6 lg:px-8`; ancho máximo `max-w-6xl`.
- Radios: `sm` 8 px · `md` 12 px (botones, inputs) · `lg` 20 px (tarjetas) ·
  `xl` 28 px (paneles) · `full` (chips, avatares).
- Tarjetas con borde fino `line` sobre `surface`; `shadow-lift` solo al pasar el
  cursor por elementos clicables; `shadow-glow` (verde) en el botón principal.

## Componentes base (`apps/web/components/ui`)

| Componente | Notas |
| --- | --- |
| `Button` / `buttonVariants` | Variantes `primary`, `secondary`, `outline`, `ghost`, `link`; tamaños `sm/md/lg/pill`. Usa `buttonVariants()` en `<Link>` para no anidar elementos interactivos. |
| `Chip` | Etiquetas `neutral/primary/accent`. Base de los chips de ingredientes (Fase 2). |
| `Skeleton` | Estados de carga con la forma del contenido final. |
| `StateMessage` | Estados vacíos (`role=status`) y de error (`role=alert`). |
| `Container` | Ancho máximo y gutters estándar. |
| `PageHeader` | Título en dos pesos + descripción + acciones. |
| `SectionHeading` | Título + subtítulo + acción opcional ("Ver todo"). |

Reglas: solo un nivel de tarjeta (sin tarjetas dentro de tarjetas); el hover con
elevación solo en elementos clicables; los iconos decorativos llevan
`aria-hidden`.

## Breakpoints

Mobile-first con los de Tailwind: `sm` 640 · `md` 768 · `lg` 1024 · `xl` 1280.
Todo se diseña primero a 360–390 px de ancho, sin scroll horizontal.

## Movimiento y accesibilidad

- Transiciones de 150–300 ms solo en color/sombra/desplazamiento de iconos.
- `prefers-reduced-motion` desactiva animaciones.
- Foco visible global (`:focus-visible`) con el color `focus` del mundo activo.

## Modo oscuro

No hay modo oscuro "del sistema" para Cocina en esta fase: Mixología ya es un
tema oscuro propio. Los tokens están preparados para añadirlo después.

## Formato de código

Prettier con `prettier-plugin-tailwindcss` ordena las clases de Tailwind de forma
determinista (`pnpm --filter web format`).
