# Linear programming tutor (MVP)

Graph-first LP tutor: **FastAPI** + **SciPy** backend, **SvelteKit 5** + **Plotly** frontend.

## Backend (uv)

```bash
cd backend
uv sync
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- `POST /api/lp/analyze` with JSON `{ "source": "<DSL>" }`
- `GET /health`

## Frontend

Use **Bun** (recommended here) or **Node/npm**. The dev server proxies `/api` and `/health` to the backend on port **8000**.

### Bun

[Bun](https://bun.sh) is installed to `~/.bun/bin` by the official installer. Ensure it is on your `PATH`, then:

```bash
cd frontend
bun install
bun run dev
```

### npm

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (default `http://127.0.0.1:5173`). Start the backend on port **8000** so the Vite proxy can reach it.

Typecheck: `cd frontend && bun run check` (or `npm run check`).

## Roadmap

Future work (strict `<` / `>`, extended tableau, UI polish, and more) is listed in [ROADMAP.md](ROADMAP.md).

## Tests

```bash
cd backend && uv run pytest
```
