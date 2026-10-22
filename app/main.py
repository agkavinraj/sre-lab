import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app:app@db:5432/appdb")
# Kept small on purpose: pool exhaustion is one of the incidents you will trigger later.
POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))
POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "5"))

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency in seconds", ["method", "path"]
)

pool: ConnectionPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = ConnectionPool(
        DATABASE_URL, min_size=1, max_size=POOL_MAX, timeout=POOL_TIMEOUT, open=False
    )
    pool.open()  # does not block if the DB is down; /ready reports DB state
    yield
    pool.close()


app = FastAPI(title="sre-lab", lifespan=lifespan)


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route else "unmatched"  # template path keeps label cardinality low
    LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


class ItemIn(BaseModel):
    name: str


@app.get("/health")
def health():
    """Liveness: the process is up. Must NOT touch the database."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: the app can reach its database."""
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}")
    return {"status": "ready"}


@app.post("/items", status_code=201)
def create_item(item: ItemIn):
    with pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO items (name) VALUES (%s) RETURNING id", (item.name,)
        ).fetchone()
    return {"id": row[0], "name": item.name}


@app.get("/items")
def list_items(limit: int = 100):
    limit = max(1, min(limit, 1000))
    with pool.connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM items ORDER BY id DESC LIMIT %s", (limit,)
        ).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@app.get("/items/by-name/{name}")
def items_by_name(name: str):
    """Filters on an unindexed column. Fast on 100 rows, slow on millions (incident 1)."""
    with pool.connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM items WHERE name = %s", (name,)
        ).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
