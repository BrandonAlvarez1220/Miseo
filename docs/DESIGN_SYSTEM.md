# Design system

Dos mundos, un sistema: **Cocina** (cálido, natural, editorial) y **Mixología**
(nocturno, atmosférico, sofisticado). Ambos comparten componentes; solo cambian
los *tokens* de color.

## Cómo funciona el cambio de "mundo"

Los valores viven en variables CSS (`apps/web/app/globals.css`). Tailwind las lee
con `@theme inline`, de modo que `bg-canvas` o `text-primary` resuelven al valor
del contexto. Cualquier elemento con `data-theme="mixology"` redefine las
variables para todo su subárbol:

```tsx
<section data-theme="mixology" className="bg-canvas text-ink">…</section>
```

`ThemeScope` lo aplica automáticamente a todas las rutas bajo `/mixologia`.
**Por qué así:** evita duplicar componentes (`ButtonDark`, `CardMixology`, ...) y
hace que un componente nuevo funcione en ambos mundos sin esfuerzo.

## Color

| Token | Cocina | Mixología | Uso |
| --- | --- | --- | --- |
| `canvas` | `#fbf7f0` crema | `#14131f` noche | Fondo de página |
| `surface` | `#ffffff` | `#1e1c2d` | Tarjetas, paneles |
| `surface-muted` | `#f4ece1` | `#262338` | Skeletons, estados vacíos, chips neutros |
| `ink` | `#2a211b` | `#f4eee4` | Texto principal |
| `ink-muted` | `#6e6259` | `#aaa4ba` | Texto secundario |
| `line` | `#eadfd2` | `#322e48` | Separadores (uso mínimo) |
| `primary` | `#b34a26` pimentón | `#e3a93b` ámbar/cítrico | Acciones, acentos |
| `primary-soft` | `#f7e4d8` | `#3a3020` | Fondos de chips/estados activos |
| `accent` | `#5f6d31` oliva | `#e0668c` cereza | Acento secundario |
| `danger` | `#b42318` | `#f97066` | Errores |

Los pares texto/fondo principales cumplen WCAG AA (≥ 4.5:1).

## Tipografía

- **Display**: Fraunces (serif con eje óptico) — títulos, nombres de receta.
  Aporta el tono editorial de un libro de cocina.
- **Texto**: Inter — legibilidad en pantallas pequeñas.
- Escala: títulos de página `text-4xl`→`sm:text-6xl/7xl`, secciones
  `text-2xl`→`sm:text-3xl`, cuerpo `text-base/lg`. `text-balance` en títulos.

## Espaciado, radios y sombras

- Espaciado: escala de Tailwind (múltiplos de 4 px). Secciones separadas por
  `space-y-20`; *gutters* `px-4 sm:px-6 lg:px-8`; ancho máximo `max-w-6xl`.
- Radios: `sm` 8 px · `md` 12 px · `lg` 20 px (tarjetas) · `xl` 28 px (paneles) ·
  `full` (botones y chips).
- Sombras: `shadow-soft` (reposo) y `shadow-lift` (hover en elementos
  interactivos). Preferimos sombra suave a bordes: menos ruido visual.

## Componentes base (`apps/web/components/ui`)

| Componente | Notas |
| --- | --- |
| `Button` / `buttonVariants` | Variantes `primary`, `secondary`, `ghost`, `link`; tamaños `sm/md/lg`. Usa `buttonVariants()` en `<Link>` para no anidar elementos interactivos. |
| `Chip` | Etiquetas `neutral/primary/accent`. Base de los chips de ingredientes (Fase 2). |
| `Skeleton` | Estados de carga con la forma del contenido final. |
| `StateMessage` | Estados vacíos (`role=status`) y de error (`role=alert`). |
| `Container` | Ancho máximo y gutters estándar. |
| `SectionHeading` | Eyebrow + título + descripción. |

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
tema oscuro propio y añadir un tercer conjunto de tokens antes de tener
fotografía real comprometería la calidad. Los tokens están preparados para
añadirlo después.
