# Autenticación, roles y agentes

## Quién puede hacer qué

| Principal | Se identifica con | Puede |
| --- | --- | --- |
| Visitante | nada | Ver recetas, buscar, rutas, recomendador |
| `user` | JWT de Supabase | Lo anterior + `/me` (después: favoritos, enviar recetas) |
| `moderator` | JWT de Supabase | Lo anterior + moderar contribuciones (próximamente) |
| `admin` | JWT de Supabase | Todo lo anterior + usuarios, roles y agentes |
| Agente | Token propio `mis_ag_…` | Solo `GET /agent/me` por ahora; enviar recetas pendientes (siguiente rama) |

Los permisos se comprueban **siempre en la API**. La web solo oculta botones.

## Cómo se verifica un usuario

1. El navegador inicia sesión con Supabase Auth y recibe un *access token* (JWT).
2. Lo envía como `Authorization: Bearer <token>`.
3. La API **solo verifica** la firma; nunca necesita la `service_role` key de Supabase.
4. El perfil (`app_user`) se crea en la primera petición con el rol `user`.

Reglas de seguridad (probadas en `tests/test_auth.py`):

- El algoritmo se **fija según el tipo de clave**: `HS256` solo con el secreto
  compartido; `RS256`/`ES256` solo con claves del JWKS. Así se bloquean `alg: none` y
  el ataque de confusión de algoritmo (firmar HS256 con la clave pública).
- `exp`, `sub` y `aud` son obligatorios; `iss` se valida si se configura.
- **El rol no se lee del token**: vive en nuestra base de datos. Editar los metadatos
  de Supabase no da permisos, y un cambio de rol se aplica al instante con el mismo
  token.
- Si falla la autenticación de una persona → 401. Si no está configurada o el JWKS
  no responde → 503 (solo las rutas protegidas; las públicas siguen funcionando).

## Configuración (`apps/api/.env`)

Configura **una** de estas opciones (las que da tu proyecto de Supabase):

```bash
# Proyectos con claves de firma asimétricas (recomendado)
SUPABASE_JWKS_URL=https://<tu-proyecto>.supabase.co/auth/v1/.well-known/jwks.json
# Proyectos con el secreto JWT compartido (legacy)
SUPABASE_JWT_SECRET=...
# Opcional pero recomendado
SUPABASE_JWT_ISSUER=https://<tu-proyecto>.supabase.co/auth/v1
```

Sin ninguna, la API funciona igual en modo solo lectura pública.

> Aún no hay pantalla de login en la web: requiere un proyecto de Supabase real
> (URL y *anon key*) y no se puede probar sin él. La API ya está lista y probada.

## Nombrar al primer administrador

Nadie es admin al principio y no debe poderse hacer desde fuera, así que se hace con
acceso a la base de datos, después de haber iniciado sesión una vez:

```bash
cd apps/api
uv run python -m app.cli grant-role --email tu@correo.com --role admin
```

A partir de ahí, un admin cambia roles con `PUT /api/v1/admin/users/{id}/role`
(no puede cambiar el suyo, para no bloquearse a sí mismo).

## Conectar agentes (opencode, Claude, Gemini…)

Cada agente es una identidad **separada** con su propio token:

```bash
curl -X POST $API/api/v1/admin/agents \
  -H "Authorization: Bearer $TU_JWT_DE_ADMIN" -H "Content-Type: application/json" \
  -d '{"name": "Claude recetas MX", "provider": "claude"}'
# → {"id": "...", "token": "mis_ag_...", ...}   ← el token se muestra UNA vez
```

- El token se guarda **solo como hash SHA-256**; no se puede recuperar. Si se pierde,
  se revoca el agente y se crea otro.
- Se revoca uno sin afectar a los demás: `POST /admin/agents/{id}/revoke`.
- Un agente comprueba su token con `GET /api/v1/agent/me`.
- Un token de agente **no** sirve para endpoints de usuario ni de admin, y un JWT de
  usuario no sirve como token de agente.
- `last_used_at` se actualiza como máximo una vez por minuto.
- Guarda el token en un gestor de secretos o en la configuración privada del agente;
  **nunca en el repositorio**. Los tokens llevan el prefijo `mis_ag_` para que
  herramientas como *secret scanning* los detecten si se filtran.

## Pendiente

- Pantalla de login y `/admin` en la web (necesita un proyecto de Supabase).
- Límite de peticiones por agente y por usuario.
- Endpoint de envío de recetas para agentes y cola de revisión (siguiente rama).
- Tabla de auditoría: hoy los cambios de rol y de agentes quedan en el log con el
  prefijo `AUDIT`.
