PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
FLASK := FLASK_APP=wsgi.py $(BIN)/flask

.PHONY: venv install install-dev run test lint db-migrate db-upgrade web-dev

venv:
	$(PY) -m venv $(VENV)

install: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

install-dev: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements-dev.txt

run:
	FLASK_DEBUG=1 $(FLASK) run

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check .

web-dev:
	cd frontend; npm run dev
web-test:
	cd frontend; npm test

test: backend-test web-test

db-migrate:
	$(FLASK) db migrate -m "$(m)"

db-upgrade:
	$(FLASK) db upgrade

dev-init:
	DEV_MODE=1 $(BIN)/flask dev-init

dev: dev-init
	DEV_MODE=1 FLASK_DEBUG=1 $(FLASK) run
