# Linear programming tutor (MVP)

Graph-first LP tutor: **FastAPI** + **SciPy** backend, **SvelteKit 5** + **Plotly** frontend.

## Backend (uv)

```bash
cd backend
uv sync
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- `POST /api/lp/analyze` with JSON `{ "source": "<DSL>" }` — optional: `tableau_mode` (`auto`, `primal`, `dual`, `big_m`), `use_blands_rule`, `big_m_value`; response may include `modeling_notes` (e.g. strict inequality ε).
- `GET /health`

## Frontend

JavaScript dependencies are managed with **[Bun](https://bun.sh)** only (no `package-lock.json`; use `bun.lock` / `bun install`).

Use Bun on your `PATH`, then:

```bash
cd frontend
bun install
bun run dev
```

The dev server proxies `/api` and `/health` to the backend on port **8000**. Open the URL Vite prints (default `http://127.0.0.1:5173`).

Typecheck: `cd frontend && bun run check`. Build: `cd frontend && bun run build`.

Repo root: `bun install` then `bun run dev` (with `uv` on `PATH` and frontend deps installed) runs API and UI together.

## Roadmap

Shipped scope and future ideas are tracked in [ROADMAP.md](ROADMAP.md).

## Tests

```bash
cd backend && uv run pytest
```
