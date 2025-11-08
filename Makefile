.PHONY: help build up down logs clean test lint security hadolint trivy check-user check-health

help:
	@echo "Available commands:"
	@echo "  make build         - Build Docker image"
	@echo "  make up            - Start services with docker-compose"
	@echo "  make down          - Stop services"
	@echo "  make logs          - View logs"
	@echo "  make clean         - Remove containers and images"
	@echo "  make test          - Run tests locally"
	@echo "  make lint          - Run linters"
	@echo "  make security      - Run security checks"
	@echo "  make hadolint      - Check Dockerfile with hadolint"
	@echo "  make trivy         - Scan image with trivy"
	@echo "  make check-user    - Verify container runs as non-root"
	@echo "  make check-health  - Test healthcheck"

build:
	docker build -t workout-log-api:latest .

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker rmi workout-log-api:latest || true

test:
	pytest -v --cov=app --cov-report=term

lint:
	ruff check .
	black --check .
	isort --check-only .

security:
	bandit -r app/ -c .bandit

hadolint:
	docker run --rm -i hadolint/hadolint < Dockerfile

trivy: build
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image workout-log-api:latest

check-user: build
	@echo "Checking if container runs as non-root user..."
	@docker run --rm workout-log-api:latest id
	@docker run --rm workout-log-api:latest sh -c 'if [ $$(id -u) -eq 0 ]; then echo "ERROR: Running as root!"; exit 1; else echo "OK: Running as user $$(id -u)"; exit 0; fi'

check-health: build
	@echo "Testing healthcheck..."
	@docker run -d --name test-api workout-log-api:latest
	@echo "Waiting for healthcheck to pass..."
	@sleep 20
	@docker inspect test-api --format='{{.State.Health.Status}}'
	@docker stop test-api
	@docker rm test-api

ci-check: lint security test hadolint trivy check-user check-health
	@echo "All checks passed!"
