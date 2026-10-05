PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
FLASK := FLASK_APP=wsgi.py $(BIN)/flask

.PHONY: venv install install-dev run test lint db-migrate db-upgrade

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

db-migrate:
	$(FLASK) db migrate -m "$(m)"

db-upgrade:
	$(FLASK) db upgrade
