COMPOSE ?= docker-compose
WEB ?= web

.PHONY: help up build down restart logs ps shell migrate makemigrations createsuperuser test check install-hooks

help:
	@echo "Comandos disponibles:"
	@echo "  make up              - Levanta los contenedores"
	@echo "  make build           - Reconstruye y levanta"
	@echo "  make down            - Para contenedores"
	@echo "  make restart         - Reinicia contenedores"
	@echo "  make logs            - Muestra logs en vivo"
	@echo "  make ps              - Estado de contenedores"
	@echo "  make shell           - Abre shell de Django"
	@echo "  make migrate         - Aplica migraciones"
	@echo "  make makemigrations  - Crea migraciones"
	@echo "  make createsuperuser - Crea superusuario"
	@echo "  make test            - Ejecuta tests"
	@echo "  make check           - Django check"
	@echo "  make install-hooks   - Instala hooks de git locales"

up:
	$(COMPOSE) up

build:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec $(WEB) python manage.py shell

migrate:
	$(COMPOSE) exec $(WEB) python manage.py migrate

makemigrations:
	$(COMPOSE) exec $(WEB) python manage.py makemigrations

createsuperuser:
	$(COMPOSE) exec $(WEB) python manage.py createsuperuser

test:
	$(COMPOSE) exec $(WEB) python manage.py test

check:
	$(COMPOSE) exec $(WEB) python manage.py check

install-hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks configurados en .githooks"
