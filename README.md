# Personal Communication Agent

Production-first local personal communication agent monorepo.

## Monorepo Structure
- `apps/web`: Next.js + Tailwind dashboard app (placeholder UI).
- `apps/api`: FastAPI backend with health endpoint.
- `agents/`: Platform connector and agent-module placeholders.
- `infra/`: Local infrastructure (PostgreSQL via Docker Compose).
- `docs/`: Product and setup documentation.
- `scripts/`: Helper scripts for local development.

## Quick Start
1. Copy `.env.example` to `.env` and adjust values.
2. Start PostgreSQL:
   - `docker compose -f infra/docker-compose.yml up -d`
3. Start API:
   - `cd apps/api`
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Start Web:
   - `cd apps/web`
   - `npm install`
   - `npm run dev`

## Current Scope
- Includes minimal API health endpoint and placeholder dashboard page.
- Slack, WhatsApp, and LINE integrations are intentionally not implemented yet.
