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
   - `alembic upgrade head`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Start Web:
   - `cd apps/web`
   - `npm install`
   - `npm run dev`

## Local AI Provider (Ollama, Optional but Integrated)
- The backend uses a local `AIProvider` abstraction with `OllamaProvider`.
- Default Ollama URL is `http://localhost:11434`.
- Model name is read from env (`OLLAMA_MODEL`).
- No paid OpenAI API key is required.
- If Ollama is unavailable or model is missing, services automatically fall back to deterministic rule-based behavior.

### Setup Ollama
1. Install Ollama on Windows and start the app/service.
2. Pull the model configured in `.env`:
   - `ollama pull llama3.1:8b`
3. Verify Ollama is up:
   - `curl http://localhost:11434/api/tags`
4. Ensure env values:
   - `OLLAMA_ENABLED=true`
   - `OLLAMA_BASE_URL=http://localhost:11434`
   - `OLLAMA_MODEL=llama3.1:8b`

### AI-Connected Services
- `TranslationService`: language detection, translation, practical meaning, tone/hierarchy/urgency/risk analysis.
- `DraftService`: draft generation and revision.
- `AgentService`: agent chat reply refinement.

## Current Scope
- Includes minimal API health endpoint and placeholder dashboard page.
- Slack, WhatsApp, and LINE integrations are intentionally not implemented yet.
- PostgreSQL schema and sample seed data are managed by Alembic migrations.
