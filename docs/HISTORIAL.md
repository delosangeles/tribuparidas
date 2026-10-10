# Historial de cambios (sesiones con Claude)

Bitácora de lo que se hace en el proyecto, de lo más reciente a lo más antiguo.
**Regla:** al terminar cada tarea se agrega aquí una entrada nueva (fecha, qué se hizo, archivos clave, pendientes).

---

## 2026-10-10 (madrugada)

### Aviso "tenemos información nueva para ti" (datos precargados del Excel)
- Nuevo `User.needs_data_confirmation` (+ `data_confirmed_at`). La migración `users/0007` marcó a las **154 cuentas** que ya traen datos del Excel (incluida `arboledastephania@gmail.com`); el importador (`importar_excel`) marca a quien cree o complete y no vuelve a preguntar a quien ya confirmó.
- Al ingresar sale un modal cálido ("¡Hola, {nombre}! 💛 Estamos organizando la tribu…") con 4 pestañas ya rellenas (datos, ubicación —muestra lo que escribió en el Excel—, festejos con hijos/embarazo, "Cuéntanos de ti"). Puede corregir y **Confirmar mis datos** (`PATCH /api/me/` con `confirm_data: true`), o **Más tarde** (se oculta esa sesión y vuelve a salir al próximo ingreso). Se confirma una sola vez; no se puede apagar por otro medio.
- Archivos: `components/profile/ProfileConfirmModal.vue` (montado en `app.vue`), `users/serializers.py`, `users/migrations/0007`.

### Comentarios del blog: responder, reaccionar, fotos, editar y eliminar
- **Responder** (un nivel; responder a una respuesta cuelga del comentario principal), **me gusta** (uno por persona, alterna), **foto** opcional (JPG/PNG/WEBP ≤5MB, nombre de archivo aleatorio; un comentario puede ser solo foto), **editar** solo la autora (texto y foto; queda "· editado"), **eliminar** la autora o un admin (se van también sus respuestas). Un admin **no** puede editar comentarios ajenos; su eliminación queda en el historial (`blog_comment_deleted`).
- API: `GET/POST /api/blog/<slug>/comments/` (principales con `replies`, `like_count`, `liked_by_me`, `image`), `PATCH/DELETE …/comments/<id>/`, `POST …/comments/<id>/like/`. Leer sigue siendo público; escribir/reaccionar exige sesión. Migración `blog/0005`.
- Frontend: `BlogCommentItem.vue` (reescrito), `CommentComposer.vue`, `pages/blog/[slug].vue`.

### Categoría "Desahogos"
- Nueva categoría de blog `desahogos` (migración `blog/0006`), la **única** donde cualquier persona registrada publica **sin aprobación**: queda `PUBLISHED` con fecha de hoy y se registra en el historial (`blog_post_published_open`). En las demás categorías sigue "en revisión". El servidor decide el estado (no se puede forzar desde el cliente) y los no-admin ya no pueden marcar `featured`.
- El formulario de "Nuevo blog" avisa qué pasa según la categoría elegida, y el mensaje final dice si quedó publicado o en revisión. Constante `OPEN_CATEGORY_SLUG` en `blog/models.py`.

### Pruebas
- Backend en Docker (Postgres): **182 tests pasan**. Frontend: 15 pasan y `nuxi build` compila.
- Recorrido en Chrome: modal (aparece, precarga, "Más tarde", confirmar, no reaparece), comentario con foto, respuesta, like, edición, eliminación por admin y formulario con Desahogos. Capturas 40–62 en `Stephania/recorrido-2026-10-10/`. Datos de prueba eliminados.
- Pendiente: notificar a la autora cuando alguien responde o reacciona; listado de moderación de comentarios en el admin (hoy se elimina desde el propio artículo); publicar un desahogo completo desde la interfaz no se probó en el navegador (sí por API).

---

## 2026-10-10 (noche)

### Registro y perfil con más datos, fotos y ficha de admin
- **Obligatorios al registrarse:** nombre, apellido, **cédula**, teléfono (el mismo WhatsApp de siempre), correo y contraseña. El cumpleaños dejó de ser obligatorio.
- **Opcionales, en pestañas:** Ubicación (departamento, ciudad, dirección), Festejos (cumpleaños, hijos, embarazo) y "Cuéntanos de ti" (las preguntas abiertas del Excel, ahora editables por la usuaria).
- **Cédula:** única (se normaliza: `1.234.567-8` = `12345678`), solo la ven la usuaria y el equipo admin, nunca aparece en endpoints públicos. Una vez guardada solo la cambia un admin. Las cuentas precargadas del Excel pueden reclamarla al registrarse.
- **Fotos:** foto de la madre (`POST/DELETE /api/me/photo/`) y una por hijo (`/api/me/children/<id>/photo/`), con nombres de archivo aleatorios. Se ven en: comentarios del blog (la de la madre, pública), festejos (la del hijo/a en sus festejos, la de la madre en su cumpleaños), menú de usuario y ficha admin. Se suben desde "Mi perfil" (en el registro no, porque la cuenta aún no tiene sesión).
- **Admin de usuarios:** la tabla muestra avatar, teléfono, cédula y ciudad; "Ver ficha" abre un modal con pestañas en tres columnas y las preguntas abiertas en solo lectura (con contador de respuestas). La búsqueda incluye cédula, teléfono y ciudad.
- **Migración:** `users/0006_profile_contact_and_photos`. Las cuentas existentes quedan con los campos nuevos vacíos.
- Archivos clave: `users/{models,serializers,views,urls}.py`, `composables/useProfileQuestions.ts`, `components/profile/*`, `components/ui/UserAvatar.vue`, `pages/login.vue`, `pages/dashboard/settings.vue`, `pages/admin/users.vue`.
- Tests: backend 149 pasan (nuevos de cédula, obligatorios, fotos, permisos, comentarios y festejos); frontend 15 pasan y `nuxi build` compila. No se probó en un navegador.
- Pendientes: las fotos se sirven desde `/media/` (URL aleatoria pero no autenticada: la de los hijos no es realmente privada si alguien tiene el enlace); mostrar la foto también en preguntas/opiniones de emprendimientos; decidir si el admin puede subir fotos por otra persona; las opciones de "¿Cómo estás?" son texto libre.

### Cédula "medio obligatoria" y prueba en Docker (misma noche)
- La **cédula pasó a opcional** en el registro, con el aviso: *si quieres acceder a descuentos y promociones exclusivas para la tribu, debes registrar tu cédula*. Obligatorios quedan: nombre, apellido, teléfono, correo y contraseña. El aviso también sale en "Mi perfil" mientras no tenga cédula, y en la ficha admin el campo dice "Sin cédula (sin acceso a descuentos)". Sigue siendo única cuando se escribe; varias cuentas pueden quedar sin cédula.
- **Prueba en Docker (Postgres 16):** migraciones `news/0002` y `users/0006` aplicadas sobre la base real (3 noticias → privadas; 208 cuentas con cédula vacía); `makemigrations --check` sin cambios; 152 tests pasan.
- **Recorrido en Chrome (Playwright, 20 pasos, todos OK):** visitante (inicio, noticias públicas, emprendimientos, blog, "Inicia sesión" para preguntar/opinar/comentar, festejos/admin/perfil privados), registro con pestañas (desktop y celular), perfil con fotos, comentario con foto, festejos con fotos, ficha admin y formulario de noticias con visibilidad. Capturas en `Stephania/recorrido-2026-10-10/`.
- **Bugs encontrados y corregidos:** (1) el comentario recién publicado devolvía la foto con URL relativa (se veía rota) → ahora absoluta, con test; (2) en "Mi perfil" el botón de borrar hijo quedaba debajo de la foto → reordenado.
- Nota del entorno: el servidor de desarrollo del contenedor `frontend` no detecta archivos/componentes nuevos; hay que reiniciarlo (`docker compose restart frontend`) después de crear componentes.
- Datos de prueba (cuentas `qa.*`, noticia y blog "QA …", 2 festejos generados) fueron eliminados y el interruptor de festejos quedó oculto como estaba.
- Pendiente: en celular la pestaña "Cuéntanos de ti" queda fuera de la vista hasta deslizar; las imágenes de los blogs existentes no cargan en el entorno de desarrollo (faltan archivos en `media`).

---

## 2026-10-10 (tarde)

### Sitio abierto: lectura pública, escritura con sesión
Antes todo el sitio exigía sesión. Ahora:

| Sección | Sin sesión | Con sesión |
|---|---|---|
| Inicio `/` | Público (noticias públicas) | Noticias públicas + privadas |
| Emprendimientos (listado y detalle, contacto incluido) | Lee todo | Pregunta, opina, favoritos, crea emprendimiento |
| Blog (listado, detalle, imagen, comentarios) | Lee todo | Comenta y envía blogs (quedan en revisión) |
| Preguntas y opiniones de un emprendimiento | Solo lectura | Escribir |
| Noticias | Solo públicas, activas y vigentes | Públicas y privadas |
| Festejos | Nada | Con sesión y con el interruptor de lanzamiento |
| `/dashboard`, `/admin`, `/registro` | Nada | Según rol |

- Backend: emprendimientos, categorías, blog (posts, categorías, etapas, comentarios), preguntas y opiniones pasan a lectura abierta. `IsAdminOrCreateOnly` ahora exige sesión para crear (antes dejaba pasar cualquier POST). `/api/feature-flags/` se puede leer sin sesión para que los visitantes sepan si el blog ya está lanzado.
- Frontend: `middleware/auth.global.ts` pasa de "todo cerrado salvo /login" a una lista de prefijos privados (`/dashboard`, `/admin`, `/festejos`, `/registro`). El home ya no redirige al login, el menú se muestra a visitantes, y en el detalle del emprendimiento las preguntas y opiniones muestran "Inicia sesión para…" con regreso a la misma página.
- Sin cambios: crear emprendimientos sigue exigiendo sesión; el registro sigue quedando inactivo hasta que un admin apruebe.
- Tests: se actualizaron los que exigían 401 en lecturas y se agregaron los de lectura anónima y escritura bloqueada. Backend 124 pasan; falla `test_analytics_summary_aggregates_data` de forma intermitente por empates de `created_at` en Windows (ya existía). Frontend: 15 pasan y `nuxi build` compila.
- Pendientes: SSR para buscadores y vistas previas (hoy es SPA); revisar que `/media/` se sirva sin sesión en producción; el menú de visitantes solo tiene "Iniciar sesión" (no hay botón directo de registro).

---

## 2026-10-10 (mañana)

### Noticias: campo obligatorio de visibilidad (público / privado)
- Nuevo campo `News.visibility` (`public` | `private`), **obligatorio** y sin valor por defecto: quien crea la noticia debe elegir.
- Migración `news/0002_news_visibility`: las noticias que ya existían quedan **privadas**.
- Significado: **pública** = la ve cualquiera, incluso sin iniciar sesión; **privada** = solo con sesión iniciada.
- API (`apps/news/views.py`): `list`, `retrieve` y `active` son de lectura abierta. Sin sesión solo devuelve noticias públicas, activas y vigentes; con sesión, todas (como antes). Escribir sigue siendo solo del equipo admin.
- Frontend: selector obligatorio "Visibilidad" en `NewsForm.vue`, etiqueta Pública/Privada en `admin/news.vue`, tipo `NewsVisibility`, y `/noticias` pasa a ser ruta pública en `middleware/auth.global.ts`.
- Tests nuevos en `apps/news/tests.py`.
- Pendiente: revisar que las imágenes de `/media/` se sirvan sin sesión en producción; decidir si el carrusel de la portada (`/`) también debe abrirse al público (hoy `/` exige sesión).

### Festejos dentro de la función de lanzamiento
- Nuevo interruptor `festejos_module` (migración `core/0006_seed_festejos_module_flag`), programable en `/admin/lanzamiento`.
- Antes del lanzamiento: la API devuelve lista vacía y no genera festejos para usuarias; el enlace del menú, la página `/festejos` y el banner de datos faltantes quedan ocultos. El equipo admin los ve siempre.
- Tests en `apps/festejos/tests.py` y `tests/stores/featureFlags.test.ts`.
- Pendiente: el formulario de datos (cumpleaños, hijos) sigue visible en registro y ajustes; su texto menciona "festejos".

### Commits creados
- `a79bbea` Módulo de festejos y datos de perfil de las usuarias
- `7711f07` Importador del Excel de inscripción
- `d58fb82` Reportes mensuales de la plataforma
- Los cambios de lanzamiento de festejos y de visibilidad de noticias siguen **sin commitear**.

### Revisión y análisis
- Cómo se generan los festejos: `logic.py` calcula fechas (mesversarios 1–11, cumpleaños, semana lunes–domingo) y `generator.py` crea registros de forma idempotente al consultar o con `calcular_festejos`. Quedan **pendientes de aprobar** por un admin.
- Pendientes detectados: cron para `calcular_festejos` y `reporte_mensual`, revisar `TIME_ZONE`, correr tests con Postgres (Docker estaba apagado; se probó con SQLite), documentar festejos/importador/reportes en el README.
