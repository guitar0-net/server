.PHONY: help install update lint test migrate run shell clean checkmigrations loc ci

# Переменные: интегрируем PDM
PYTHON := pdm run python
PDM := pdm run
DJANGO := $(PYTHON) manage.py


help: ## Показать все доступные команды
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости (PDM install)
	pdm install

update: ## Безопасно обновить зависимости
	pdm update --unconstrained
	pdm sync

lint: ## Линтинг
	$(PDM) lint

test: ## Запустить тесты
	$(PDM) pytest

migrate: ## Миграции БД
	$(DJANGO) makemigrations
	$(DJANGO) migrate

run: migrate ## Запустить dev-сервер
	$(DJANGO) runserver 0.0.0.0:8000

shell: ## Django shell_plus
	$(PDM) run python manage.py shell_plus

clean: ## Очистить временные и служебные файлы
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -f .coverage coverage.xml
	rm -rf htmlcov/ .mypy_cache .pytest_cache .ruff_cache

checkmigrations: ## Проверить наличие неприменённых миграций
	$(DJANGO) makemigrations --check --dry-run --no-input

loc: ## Подсчет строк кода и тестов
	@echo "📊 Подсчет строк кода:"
	@total=$$(find . -type f -name '*.py' ! -path '*/venv/*' ! -path '*/.venv/*' ! -path '*/migrations/*' | xargs wc -l | tail -n1 | awk '{print $$1}'); \
	tests=$$(find tests -type f -name '*.py' | xargs wc -l | tail -n1 | awk '{print $$1}'); \
	if [ -z "$$tests" ]; then tests=0; fi; \
	code=$$((total - tests)); \
	ratio=$$(python3 -c "print(round(($$tests / $$total * 100) if $$total else 0, 2))"); \
	echo "Всего строк Python: $$total"; \
	echo "Основной код: $$code"; \
	echo "Тесты: $$tests"; \
	echo "Тесты занимают: $$ratio% от общего количества"; \
	echo "--------------------------------------------"

ci: lint test ## Основные проверки перед отправкой PR
