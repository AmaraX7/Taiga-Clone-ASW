# Projecte ASW — Taiga Clone

## Membres de l'equip
- Mohamed Amara
- Denis Roca
- Victor Carilla
- Adam Ziani
- Aina Oskam

## Links
- 🔗 Taiga: https://tree.taiga.io/project/victorr-cm-asw/timeline
- 🚀 App desplegada: (afegir link)

---

## Requisits previs
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instal·lat i en execució
- Git

Res més. No cal instal·lar Python ni PostgreSQL localment.

---

## Instal·lació local

### 1. Clona el repositori
```bash
git clone https://github.com/el-vostre-repo.git
cd projecte-asw
```

### 2. Configura les variables d'entorn
```bash
cp .env.example .env
```

El `.env` ja té les credencials correctes per a Docker, no cal canviar res per arrencar en local. Si vols configurar Google OAuth o S3, edita els camps corresponents (veure seccions més avall).

### 3. Arrenca el projecte
```bash
docker-compose up --build
```

La primera vegada triga uns minuts perquè descarrega les imatges. Les següents vegades és molt més ràpid.

L'aplicació estarà disponible a http://localhost:8000

### 4. Executa les migracions (primera vegada)
En un altre terminal, amb els contenidors en execució:
```bash
docker-compose exec web python manage.py migrate
```

### 5. Crea un superusuari (opcional, per accedir a /admin)
```bash
docker-compose exec web python manage.py createsuperuser
```

---

## Cada vegada que facis pull
Si un company ha afegit noves dependències o migracions:
```bash
docker-compose up --build
docker-compose exec web python manage.py migrate
```

Si només hi ha canvis de codi sense noves dependències ni migracions:
```bash
docker-compose up
```

---

## Comandos útils

| Acció | Comando |
|---|---|
| Arrencar | `docker-compose up` |
| Arrencar i reconstruir | `docker-compose up --build` |
| Parar | `docker-compose down` |
| Parar i esborrar dades DB | `docker-compose down -v` |
| Executar migracions | `docker-compose exec web python manage.py migrate` |
| Crear migracions | `docker-compose exec web python manage.py makemigrations` |
| Shell de Django | `docker-compose exec web python manage.py shell` |
| Logs | `docker-compose logs -f` |

---

## Configurar Google OAuth (només cal fer-ho una vegada per equip)

1. Accedeix a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un projecte nou
3. APIs & Services → Credentials → Create OAuth 2.0 Client ID
4. Afegeix aquesta URI de redirecció: `http://localhost:8000/accounts/google/callback/`
5. Copia el **Client ID** i el **Client Secret** al teu `.env`
6. Arrenca el servidor i accedeix a http://localhost:8000/admin
7. Sites → canvia `example.com` per `localhost:8000`
8. Social Applications → Add → Google → enganxa les credencials

---

## Base de dades

- **En local**: cada membre té la seva pròpia DB dins del contenidor Docker. Les dades no es comparteixen entre membres, això és normal.
- **En producció**: hi ha una única DB compartida a Render/Railway/Supabase, configurada per un sol membre de l'equip.

---

## Estructura del projecte
```
├── config/            # Configuració Django (settings, urls)
├── issues/            # App principal (issues, comments, attachments)
├── accounts/          # App d'usuaris i perfils
├── templates/         # HTML templates
├── static/            # CSS, JS, imatges estàtiques
├── media/             # Fitxers pujats en local (en prod s'usa S3)
├── Dockerfile         # Imatge Docker de l'aplicació
├── docker-compose.yml
├── .env.example       # Exemple de variables d'entorn
├── requirements.txt   # Dependències Python
└── manage.py
```
