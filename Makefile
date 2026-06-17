.PHONY: api web dev install start-api start-web

# Dev local
api:
	.venv/bin/uvicorn api.main:app --reload --port 8000

web:
	cd frontend && npm run dev

dev:
	make -j2 api web

# Installation
install:
	pip install -r requirements.txt
	cd frontend && npm ci

# Production (Railway)
start-api:
	uvicorn api.main:app --host 0.0.0.0 --port $${PORT:-8000}

start-web:
	cd frontend && npm run build && npm run start
