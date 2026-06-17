.PHONY: api web dev

api:
	.venv/bin/uvicorn api.main:app --reload --port 8000

web:
	cd frontend && npm run dev

dev:
	make -j2 api web
