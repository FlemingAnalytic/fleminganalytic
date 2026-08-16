# Fleming Analytic

Two deployables that only make sense together: a FastAPI application behind
`api.fleminganalytic.com`, and the React client at `fleminganalytic.com` that
talks to it.

```
client/              the Vite + React front end (see client/ for its own set-up)
```

## The API

One app per domain, mounted under its own prefix by `main.py`.

```
main.py              the application; mounts every router below
gunicorn_conf.py     one worker, on purpose - see "Sessions" below
chessapi.py          standalone router, mounted like the rest
apps/
  analyst/           dataset profiling, pivots, classification, modelling
  astro/             chart generation, interpretation, Printify integration
  stjohn/            church CMS - admin, public and API routers
  stocks/ trading/   market data and strategy endpoints
  fred/ news/ chat/  economic series, headlines, LLM queries
  restaurant/ orders/ lms/ cqa/ jobberhub/ wordclouds/ legacy/
templates/           server-rendered pages
```

## Running it

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env          # then fill it in
venv/bin/gunicorn -c gunicorn_conf.py -k uvicorn.workers.UvicornWorker main:app
```

`main.py` mounts `static/` and `examples/` as static directories and reads
data from `db/`, `momentum/`, `news/` and `weather/`. None of those are in
this repository — they are generated output and deployed assets, several
hundred megabytes each, and they rebuild from the scripts that produced
them. Create the directories before starting, or the static mounts will
raise at import time.

## Configuration

Everything secret comes from the environment via `python-dotenv`; nothing is
hardcoded. `.env` is not tracked and must not become tracked — it carries the
database URL, the SMTP password and the FRED API key.

## Sessions

`gunicorn_conf.py` sets `workers = 1` deliberately. The analyst app keeps
loaded dataframes in a module-level dict (`apps/analyst/router.py`), so a
second worker would answer requests about datasets it has never seen. The
same design means a restart forgets every loaded dataset, and clients have
to be able to recover from that rather than assume a session persists.

## The client

```bash
cd client && npm install
npm run dev                     # localhost:5173, talks to the live API
npm run build                   # -> dist/, copied into the web root
```

`client/src/pages/AnalystLab.jsx` is the report canvas: tiles on a grid, a
fields pane driven by the profiler's own measure/dimension tags, and
cross-filtering between visuals. Every figure it shows is aggregated by
`/analyst/pivot` rather than computed in the browser — the client never
receives more than a 100-row preview of any dataset.

`VITE_API_URL` must not end in `/api`. The routers are mounted at `/stocks`,
`/analyst` and so on with no shared prefix, and a base URL with that suffix
breaks every call in the app at once, silently, with 404s.

## History

This repository starts fresh. The previous server history had `venv/`
committed — 40,109 files, 3.13 GiB, including CUDA libraries larger than
GitHub's 100MB per-file limit — and a tracked `.env`. It remains on the
server; nothing was lost, but it is not something that can be published. The
client's own history came across intact.
