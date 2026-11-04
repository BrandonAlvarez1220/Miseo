# Miseo

> Descubre lo que puedes crear con lo que ya tienes.

Plataforma **open source y comunitaria** de recetas de cocina y mixología. Gratis,
pensada para móvil y escritorio, y útil **sin depender de APIs de IA de pago**: la IA
solo enriquece el catálogo de forma opcional y siempre con revisión humana.

## Módulos

- **Cocina** — catálogo de recetas, búsqueda, filtros y recomendaciones según los
  ingredientes que tienes.
- **Mixología** — cócteles clásicos, variaciones documentadas, técnicas, cristalería
  y bebidas sin alcohol.

## Stack

| Capa | Tecnología |
| --- | --- |
| Web | Next.js (App Router) · React · TypeScript · Tailwind CSS v4 |
| API | Python 3.12 · FastAPI · Pydantic · SQLAlchemy 2 · Alembic |
| Datos | PostgreSQL (Supabase) · Supabase Auth · Supabase Storage |
| IA (opcional) | Ingesta asíncrona con Ollama / proveedores intercambiables |

## Inicio rápido

```bash
cp .env.example .env
docker compose up --build
```

Web en http://localhost:3000 · API en http://localhost:8000/docs

Instalación manual y convenciones: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md)
- [Base de datos](docs/DATABASE.md)
- [Design system](docs/DESIGN_SYSTEM.md)
- [Roadmap](docs/ROADMAP.md)
- [Estado de implementación](docs/IMPLEMENTATION_STATUS.md)

## Licencia

[MIT](LICENSE)
