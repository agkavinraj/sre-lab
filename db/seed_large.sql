-- Run manually when you start incident 1:
--   docker compose exec -T db psql -U app -d appdb < db/seed_large.sql
INSERT INTO items (name)
SELECT 'item-' || g FROM generate_series(1, 2000000) AS g;
ANALYZE items;
