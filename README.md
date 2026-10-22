# sre-lab

A small production-style service to practice application support and SRE work:
run it, break it on purpose, investigate, fix it, and write up what happened.

## Stack
- Python / FastAPI service with Prometheus metrics (`/metrics`)
- PostgreSQL 16
- Docker + Docker Compose
- GitHub Actions: unit tests, image build, deploy to compose, smoke test

## Run it
    docker compose up -d --build
    ./scripts/smoke_test.sh
    curl localhost:8000/items

## Run tests (no database needed)
    pip install -r app/requirements.txt
    pytest -q

## Endpoints
| Path | Purpose |
|---|---|
| `/health` | liveness, never touches the DB |
| `/ready` | readiness, checks DB connectivity |
| `POST /items`, `GET /items` | basic CRUD |
| `/items/by-name/{name}` | filters an unindexed column (incident 1) |
| `/metrics` | Prometheus metrics |

## Incident log
Write-ups live in `incidents/` (use `incidents/TEMPLATE.md`).

## Roadmap
- [x] Service + Postgres + Compose
- [x] CI with smoke test
- [ ] Prometheus, Grafana, Alertmanager
- [ ] SLIs / SLOs and alerts
- [ ] Incident 1: slow query / missing index
- [ ] Incident 2: connection pool exhaustion
- [ ] Incident 3: bad release and rollback
