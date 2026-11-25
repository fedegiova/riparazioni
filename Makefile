PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
FLASK := FLASK_APP=wsgi.py $(BIN)/flask

.PHONY: venv install install-dev run test backend-test lint db-migrate db-upgrade web-dev web-test dev dev-init

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

backend-test:
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

deploy-frontend:
	#cd frontend; npm run build
	rsync -ar frontend/dist root@192.168.1.27:/opt/riparazioni/frontend
	ssh root@192.168.1.27 chown -R riparazioni:riparazioni /opt/riparazioni/frontend/dist
