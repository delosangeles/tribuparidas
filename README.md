# Tribu Paridas

Directorio y comunidad de emprendimientos: un lugar para descubrir negocios hechos con pasión, hacerles preguntas, dejar opiniones y guardarlos como favoritos. Aplicación full-stack completa: backend Django + DRF, frontend Nuxt 3, base de datos PostgreSQL, autenticación JWT y todo dockerizado para desarrollo local.

## 1. Requisitos

- [Docker](https://www.docker.com/) y Docker Compose (v2, el que trae `docker compose`, no `docker-compose`).
- No necesitas instalar Python ni Node localmente: todo corre dentro de los contenedores.
- Opcional para desarrollo fuera de Docker: Python 3.12, Node 20+, PostgreSQL 16.

## 2. Arquitectura

```
Navegador
   │  HTTP (JSON) + JWT en header Authorization
   ▼
Frontend (Nuxt 3 / Vue 3 / TypeScript)  ── SSR + cliente ──  puerto 3000
   │  Axios → /api/...
   ▼
Backend (Django + Django REST Framework)                     puerto 8000
   │  ORM
   ▼
PostgreSQL 16                                                 puerto 5432 (interno)
```

- El **backend** expone una API REST en `/api/`, documentada con OpenAPI/Swagger en `/api/docs/`, y sirve el panel `/admin/` (Django Admin) como herramienta interna adicional al panel de administración en Vue.
- El **frontend** consume exclusivamente esa API (no hay datos hardcodeados): páginas públicas, dashboard del emprendedor y panel de administración.
- La comunicación entre contenedores ocurre por nombre de servicio Docker (`backend`, `db`), no por `localhost` (ver sección 12).

## 3. Estructura de carpetas

```
tribuparidas/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── .env.example
│   ├── config/
│   │   └── settings/        # base.py, dev.py, prod.py
│   └── apps/
│       ├── core/             # utilidades compartidas (paginación, permisos, validadores, seed_data)
│       ├── users/             # Custom User (login por email) + JWT
│       ├── categories/
│       ├── businesses/        # Business + BusinessImage
│       ├── questions/         # Question + Answer
│       └── reviews/           # Review + Favorite
│
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   ├── .env.example
│   ├── nuxt.config.ts
│   ├── pages/                 # rutas (Inicio, Emprendimientos, Dashboard, Admin, ...)
│   ├── components/            # ui/, business/, question/, review/, layout/
│   ├── composables/
│   ├── stores/                 # Pinia: auth, business, categories, questions
│   ├── services/                # una capa por recurso, toda la comunicación HTTP vive aquí
│   ├── middleware/              # auth.ts, admin.ts
│   └── tests/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## 4. Variables de entorno

Copia los `.env.example` a `.env` antes de levantar el proyecto:

```bash
cp .env.example .env
cp backend/.env.example backend/.env      # solo si vas a correr el backend fuera de Docker
cp frontend/.env.example frontend/.env    # solo si vas a correr el frontend fuera de Docker
```

El `.env` de la **raíz** es el que usa `docker-compose.yml`:

| Variable | Descripción |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Credenciales de la base de datos. |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `db` y `5432` dentro de Docker. |
| `DJANGO_SECRET_KEY` | Clave secreta de Django. **Cámbiala en cualquier entorno real.** |
| `DJANGO_DEBUG` | `True` en desarrollo, `False` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por coma. |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` o `config.settings.prod`. |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos para CORS (nunca `*`). Por defecto `http://localhost:3000`. |
| `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` | Si se definen, el backend crea automáticamente un superusuario al arrancar (idempotente). |
| `NUXT_PUBLIC_API_BASE` | URL de la API que usa el **navegador** (`http://localhost:8000/api`). |
| `NUXT_API_BASE_SERVER` | URL de la API que usa el **contenedor del frontend** al renderizar en el servidor (`http://backend:8000/api`) — ver sección 12. |

## 5. Levantar el proyecto con Docker

```bash
docker compose up --build
```

Esto levanta:

- **PostgreSQL** con un volumen persistente (`postgres-data`).
- **Backend** (Django): aplica migraciones automáticamente, crea el superusuario si las variables están definidas, y arranca en `http://localhost:8000`.
- **Frontend** (Nuxt): arranca en `http://localhost:3000`.

Un servicio `nginx` opcional (perfil `prod`) está preparado para simular un despliegue de producción: `docker compose --profile prod up`.

## 6. Migraciones

Ya están generadas y versionadas en `backend/apps/*/migrations/`. Se aplican automáticamente al arrancar el contenedor del backend. Para crear nuevas migraciones tras modificar un modelo:

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

## 7. Crear un superusuario

Automático si defines `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD` en `.env` (por defecto `admin@tribuparidas.com` / la contraseña del `.env.example`, **cámbiala**). También puedes crear uno manualmente:

```bash
docker compose exec backend python manage.py createsuperuser
```

## 8. Cargar datos de prueba

```bash
docker compose exec backend python manage.py seed_data
```

Crea (de forma idempotente, se puede correr varias veces sin duplicar):

- 7 categorías: Repostería, Moda, Belleza, Artesanías, Comida, Hogar, Servicios.
- 5 emprendimientos aprobados con logo, portada y galería (imágenes generadas con Pillow): Dulces de Stephania, Luna & Sol, Vela Viva, Verde Hogar, Manos que crean.
- Una pregunta respondida y varias opiniones por emprendimiento.
- 3 usuarios "visitantes" y un usuario "emprendedor" dueño por cada negocio (contraseña `ClaveSegura123`).

Después de cargar los datos, `http://localhost:3000` muestra contenido real de inmediato.

## 9. Ejecutar tests

Backend (pytest-django, cubre registro, login, permisos de negocio, preguntas/respuestas y reviews):

```bash
docker compose exec backend pytest
```

Frontend (Vitest + entorno Nuxt, cubre el store de autenticación/protección de rutas, un componente crítico y la capa de servicios):

```bash
docker compose exec frontend npm run test
```

## 10. URLs disponibles

| URL | Descripción |
|---|---|
| `http://localhost:3000` | Frontend (Home) |
| `http://localhost:3000/businesses` | Listado de emprendimientos |
| `http://localhost:3000/businesses/{slug}` | Perfil público de un emprendimiento |
| `http://localhost:3000/login`, `/registro`, `/registro/emprendimiento` | Autenticación y onboarding |
| `http://localhost:3000/dashboard` | Panel del emprendedor |
| `http://localhost:3000/admin` | Panel de administración (Vue) |
| `http://localhost:8000/api/` | API REST |
| `http://localhost:8000/api/docs/` | Documentación interactiva (Swagger/OpenAPI, vía drf-spectacular) |
| `http://localhost:8000/admin/` | Django Admin |

## 11. Cómo funciona la autenticación

- JWT con [`djangorestframework-simplejwt`](https://django-rest-framework-simplejwt.readthedocs.io/): `POST /api/auth/login/` devuelve `access` (15 min) y `refresh` (7 días, con rotación y blacklist).
- El frontend guarda ambos tokens en cookies (`useCookie` de Nuxt, seguras y compatibles con SSR — no `localStorage`, que no existe durante el renderizado en servidor).
- Un interceptor de Axios (`plugins/api.ts`) agrega `Authorization: Bearer <access>` a cada petición y, si recibe un `401`, intenta refrescar el token automáticamente y reintenta la petición original; si el refresh también falla, cierra la sesión y redirige a `/login`.
- **Roles**: no existe un campo `role` en el modelo `User`. Un usuario es **administrador** si `is_staff=True`; es **emprendedor** si tiene al menos un `Business` propio; en cualquier otro caso es **visitante**. Los permisos reales (quién puede editar qué) los deciden las clases de permisos de DRF comparando `business.owner` contra el usuario autenticado — eso es lo que realmente impide que un emprendedor edite el negocio de otro, no una etiqueta de rol.
- Rutas protegidas en el frontend: `middleware/auth.ts` (requiere sesión) y `middleware/admin.ts` (requiere `is_staff`).

## 12. Cómo se comunican frontend y backend

- El **navegador** llama a la API usando `NUXT_PUBLIC_API_BASE` (`http://localhost:8000/api`), porque necesita una URL alcanzable desde fuera de Docker.
- El frontend corre en modo **SPA puro** (`ssr: false` en `nuxt.config.ts`): no hay renderizado en servidor, todo se resuelve en el navegador con la API definida arriba. `runtimeConfig.apiBaseServer`/`NUXT_API_BASE_SERVER` quedan en el código por si en el futuro se reactiva SSR (útil dentro de Docker, donde `localhost` apuntaría al contenedor del frontend y no al backend), pero hoy no se usan en runtime.
- CORS está configurado en el backend con `django-cors-headers` y `CORS_ALLOWED_ORIGINS` explícito por variable de entorno (nunca `*`).
- Toda la lógica de llamadas HTTP vive en `frontend/services/*.ts` — ningún componente hace `fetch`/`axios` directamente.

## 13. Despliegue a producción

En producción (`tribuparidas.com/directorio`) **no se usa Docker**: el droplet tiene poca RAM, así que el backend corre bare-metal (venv + Gunicorn vía systemd) y el frontend se compila como sitio estático (SPA) servido directo por nginx, sin proceso Node corriendo. Ver `[Tribu Paridas producción DigitalOcean]` en la memoria del proyecto para el detalle completo de la arquitectura del servidor.

**Backend** — conectado por SSH al servidor:

```bash
sudo /opt/tribuparidas/deploy-backend.sh
```

Hace `git pull`, reinstala dependencias si cambiaron, corre migraciones, recolecta estáticos y reinicia el servicio.

**Frontend** — desde tu máquina, en la raíz del repo (Git Bash):

```bash
./deploy-frontend.sh
```

Compila el sitio estático con las variables de entorno de producción y lo sube al servidor por SCP. Requiere la llave SSH `~/.ssh/id_tribuparidas` autorizada en el droplet.

Flujo típico: hacer cambios en local → `git push` → correr `deploy-backend.sh` en el servidor si tocaste `backend/` → correr `./deploy-frontend.sh` en local si tocaste `frontend/`.

## Notas de diseño

- **Imágenes**: se manejan con Pillow en el backend (`MEDIA_ROOT`/`MEDIA_URL`, servidas por Django en desarrollo dentro de un volumen Docker persistente). La arquitectura queda preparada para migrar a S3/Cloudinary vía `django-storages` sin reescribir el resto del código (ver comentario en `backend/config/settings/base.py`).
- **Estadísticas del dashboard**: solo se muestran métricas reales que existen en el modelo de datos (preguntas, galería, opiniones, calificación promedio). No se simula un contador de "visitas" porque no hay un modelo de tracking de visitas en el alcance del proyecto — agregarlo sería una extensión futura razonable, no un dato inventado en el frontend.
- **Categorías**: las borra o edita únicamente un administrador (`IsAdminOrReadOnly`); si una categoría tiene emprendimientos asociados, el borrado falla a propósito (`on_delete=PROTECT`) para no dejar negocios huérfanos — el panel admin explica esto y sugiere desactivarla en su lugar.
