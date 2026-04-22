SHELL := /bin/bash
PYTHON_BIN := $(shell command -v python3.13 || command -v python3.11 || command -v python3)
API_VENV := $(shell if [ -x "apps/api/.venv313/bin/uvicorn" ]; then echo .venv313; elif [ -x "apps/api/.venv/bin/uvicorn" ]; then echo .venv; else echo .venv313; fi)

.PHONY: install-web install-api dev-web dev-api start-api seed-demo test-api print-api-venv

print-api-venv:
	@echo $(API_VENV)

install-web:
	cd apps/web && npm install

install-api:
	cd apps/api && $(PYTHON_BIN) -m venv $(API_VENV) && $(API_VENV)/bin/pip install -r requirements.txt

dev-web:
	cd apps/web && npm run dev

dev-api:
	cd apps/api && WATCHFILES_FORCE_POLLING=true $(API_VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-api:
	cd apps/api && $(API_VENV)/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

seed-demo:
	cd apps/api && $(API_VENV)/bin/python scripts/seed_demo.py

test-api:
	cd apps/api && $(API_VENV)/bin/pytest
