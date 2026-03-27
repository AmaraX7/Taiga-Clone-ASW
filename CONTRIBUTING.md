# Guía de Desarrollo

## Antes de empezar a trabajar

Siempre que vuelvas a trabajar en el proyecto, ejecuta estos comandos:

```bash
# 1. Asegúrate que estás en develop
git checkout develop

# 2. Trae los últimos cambios del remoto
git pull origin develop

# 3. Ejecuta las migraciones pendientes
python manage.py migrate

# 4. Verifica que tienes .env con las variables necesarias
# (Cópialo de .env.example si no lo tienes)
```

## Setup inicial del proyecto

Si es la primera vez que clonas el repo:

```bash
# Crear entorno virtual
python -m venv venv
source venv/Scripts/activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear .env basado en .env.example
cp .env.example .env

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

## Flujo de trabajo con ramas

1. Siempre crear una rama desde `develop`
2. Al terminar, pushear a la rama feature
3. Crear PR contra `develop` (no contra main)
4. Resolver conflictos si los hay
5. Una vez merged, borrar la rama feature

## Migraciones

- Si modificas `models.py`, **siempre** crea una migración:
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```
- Antes de pushear, asegúrate de que no hay conflictos de migraciones
- Si hay dos migraciones `0002_*` en paralelo, crear una migración de merge

## Base de datos

El proyecto usa PostgreSQL. En desarrollo:

```bash
docker-compose up -d  # Levanta la DB postgres
python manage.py migrate  # Aplica migraciones
```

En producción (Render): las migraciones se aplican automáticamente en el deploy.

## Variables de entorno

Edita `.env` (local) con tus valores. Nunca commitear `.env`.

Variables importantes:
- `SECRET_KEY`: Cambiar en producción
- `DEBUG`: `False` en producción
- `DB_*`: Credenciales de PostgreSQL
- `CSRF_TRUSTED_ORIGINS`: Agregar tu dominio para CSRF

## Testing

```bash
python manage.py test
```

## Antes de pushear

```bash
# Ver los cambios
git status
git diff

# Agregar cambios (seleccionar archivos, NO .env o .gitignore)
git add <file>
git commit -m "tipo(scope): mensaje en español"

# Traer cambios nuevos del remoto
git pull origin develop

# Si hay conflictos, resolverlos y hacer commit
git add .
git commit -m "merge: resolver conflictos con develop"

# Finalmente pushear
git push origin <tu-rama>
```

## Convención de commits

```
feat(scope): descripción breve
fix(scope): descripción breve
docs(scope): descripción breve
test(scope): descripción breve
refactor(scope): descripción breve
```

Ej: `feat(comments): agregar CRUD completo con edición`

## En caso de problemas

- **Conflictos al pulliar**: resuelve manually, `git add .`, `git commit`
- **Migraciones en conflicto**: crea merge migration `0003_merge_...`
- **Cambios perdidos**: `git reflog` para recuperar commits
- **Duda sobre qué hacer**: pregunta antes de hacer force-push ⚠️
