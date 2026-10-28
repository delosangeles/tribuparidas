# Tribu Paridas — guía para Claude

## Módulos nuevos: siempre con lanzamiento programado
Cada vez que se cree un **módulo nuevo** (app de backend + sección visible en el frontend), debe poder activarse desde `/admin/lanzamiento`:

1. **Backend:** migración en `apps/core/migrations/` que cree su `FeatureFlag` con `get_or_create` (`activate_at=None`, `is_forced_active=False`). Modelo a seguir: `0004_seed_blog_module_flag.py` y `0006_seed_festejos_module_flag.py`. Clave con formato `<modulo>_module`.
2. **API:** `is_<modulo>_module_live()` como en `apps/blog/views.py` / `apps/festejos/views.py` (si el flag no existe, se comporta como activo). Quien no es staff no ve nada ni se genera nada antes del lanzamiento; el equipo admin siempre lo ve.
3. **Frontend:** computed `is<Modulo>Live` en `stores/featureFlags.ts`; ocultar enlaces del menú (escritorio y móvil) con `|| authStore.isAdmin`, y redirigir la página si no es admin y el módulo no está lanzado.
4. **Tests:** fixture autouse que activa el flag (los demás tests asumen "ya lanzado") y tests de que antes del lanzamiento un usuario normal no ve nada y el admin sí.
5. Módulos existentes con flag: `blog_module`, `festejos_module`, `portal_module` (portal de emprendimientos y Mi tarjeta; `apps/portal`, `is_portal_module_live()` en `apps/portal/services.py`, permiso `PortalModuleLive`).
6. Si el módulo no debe ocultarse, dejarlo explícito en `docs/HISTORIAL.md`.

## Portal y cuentas "solo portal"
- `User.account_type` = `member` | `portal`. Las cuentas `portal` solo usan `/api/portal/…`, `/api/me/…` y `/api/auth/…` (lo impone `apps/portal/authentication.py`; si agregas un prefijo de API que deban usar, súmalo ahí). En los tests usa un cliente con JWT real: `force_authenticate` se salta esa clase.
- Todo endpoint del portal debe usar `PortalBusinessMixin` (propiedad verificada en el servidor) y filtrar siempre por `self.business`. Cada cambio de la dueña se anota con `log_change(...)`.
- Los `<img>` de `public/` van con `useAssetUrl()`; el QR se dibuja en el cliente y el token solo lo genera/verifica el backend.

## Historial
Todo lo que se haga con Claude se registra en `docs/HISTORIAL.md` (entrada nueva al terminar cada tarea: qué se hizo, archivos clave, pendientes).

## Pruebas
- Backend: pytest con Postgres (Docker). Sin Docker se puede probar con un settings de SQLite temporal fuera del repo.
- Frontend: `npx vitest run` desde `frontend/`.
