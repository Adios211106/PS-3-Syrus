# PS-03: Autonomous Developer Onboarding Agent

This project implements a dataset-driven onboarding agent for the PS-03 hackathon using the official Syrus 2026 resources.

## What It Delivers

- Chat-first onboarding assistant (mandatory)
- Persona identification from user intro (role, experience, tech stack, team)
- Dynamic onboarding checklist tracking (`In Progress` / `Completed`)
- RAG-style grounded answers with source citations
- Structured HR completion email payload (mandatory)
- Starter ticket assignment (mock integration path for Jira/GitHub/Slack)
- Example-flow aware chat guidance for:
  - Backend Intern (Node.js)
  - Frontend Senior (React)
- MCP-style mocked bonus actions (GitHub/Slack/Jira provisioning + Slack welcome)
- Session-level generated FAQ capture from grounded onboarding Q&A
- PDF + Markdown ingestion utility for vector DB pipeline

## Dataset Integration (Official PS03 Resources)

Resource files are vendored in:

- `agent/resources/ps03/`

The agent follows the same 3-tier pattern described in the dataset README:

1. **Tier 1 (RAG Searchable)**
   - `company_overview.md` (KB-001)
   - `engineering_standards.md` (KB-002)
   - `architecture_documentation.md` (KB-003)
   - `setup_guides.md` (KB-004)
   - `policies.md` (KB-005)
   - `org_structure.md` (KB-008)
   - `onboarding_faq.md` (KB-011)
2. **Tier 2 (Agent Logic Files)**
   - `employee_personas.md` (KB-006)
   - `onboarding_checklists.md` (KB-007)
   - `starter_tickets.md` (KB-010)
3. **Tier 3 (Template File)**
   - `email_templates.md` (KB-009)

## Services

1. `frontend/` (Next.js): onboarding chat + checklist dashboard + HR report preview
2. `agent/` (FastAPI): persona/checklist orchestration, retrieval, ticket assignment, completion email generation
3. `backend/` (FastAPI): CRUD scaffold for future persistence/integration expansion
4. `db` + `redis` via Docker Compose

## Run Locally

```bash
docker-compose up --build
```

Endpoints:

- Frontend: `http://localhost:3000`
- Agent API docs: `http://localhost:8001/docs`
- Backend API docs: `http://localhost:8000/docs`

## Core Agent Endpoints

### Chat onboarding

`POST /chat`

```json
{
  "session_id": "optional-session-id",
  "message": "Hi, I'm Riya. I've joined as a Backend Intern working on Node.js in Squad Beta."
}
```

Response includes:

- `message`
- `sources`
- `profile`
- `checklist`
- `assigned_ticket`
- `progress_percent`
- `status`
- `missing_profile_fields`
- `mcp_actions`
- `generated_faqs`

Useful chat commands:

- `Show me the example workflow`
- `Please provision all access and send slack welcome`
- `verify environment`
- `show generated faq`

### Checklist updates

`PATCH /onboarding/session/{session_id}/checklist/{item_id}`

### Finalize onboarding + generate HR report

`POST /onboarding/session/{session_id}/complete`

Returns structured payload containing employee info, completed/pending checklist items, compliance/access status, first-task summary, timestamps, and confidence score.

## Test Targets

- Backend smoke tests: `backend/tests/test_api.py`
- Agent behavior tests: `agent/tests/test_onboarding_service.py`

Run examples:

```bash
cd backend && pytest
cd ../agent && PYTHONPATH=. pytest
```

PDF/MD ingestion example:

```bash
cd agent
PYTHONPATH=. python -m rag.ingest /absolute/path/setup_guides.pdf /absolute/path/onboarding_faq.md
```
