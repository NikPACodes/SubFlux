# Docker
.PHONY: docker-build docker-up docker-up-d docker-down docker-restart docker-logs docker-ps

# Django
.PHONY: docker-bash docker-shell docker-migrate docker-makemigrations docker-createsuperuser

# Quality
.PHONY: docker-tests docker-check

# Docs
.PHONY: docker-schema

# Cleanup
.PHONY: docker-clean


docker-build:
	docker compose build

docker-up:
	docker compose up

docker-up-d:
	docker compose up -d

docker-down:
	docker compose down

docker-restart:
	docker compose down
	docker compose up -d --build

docker-logs:
	docker compose logs -f app

docker-ps:
	docker compose ps

docker-bash:
	docker compose exec app bash

docker-shell:
	docker compose exec app python manage.py shell

docker-migrate:
	docker compose exec app python manage.py migrate

docker-makemigrations:
	docker compose exec app python manage.py makemigrations

docker-createsuperuser:
	docker compose exec app python manage.py createsuperuser

docker-tests:
	docker compose exec app pytest apps

docker-check:
	docker compose exec app python manage.py check

docker-clean:
	docker compose down -v

docker-schema:
	docker compose exec app python manage.py spectacular --file schema.yml

