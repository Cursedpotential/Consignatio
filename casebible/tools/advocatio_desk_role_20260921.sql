-- Catalog login for the Advocatio evidence desk (legal-api on ovh-app).
-- Byline: Claude Code · Fable 5.1 · 2026-09-21 — owner order 00:38 EDT "just make one".
--
-- Read-only on the catalog_reconcile views (they run with their owner's rights, so no
-- raw_duck grant is needed). Widen with one GRANT when the desk has something to write.
-- The password is never in this file: the runner prepends `\set pw '<generated>'` on stdin.
-- Idempotent; re-running rotates the password to the value supplied.
--
-- Run: (printf "\\set pw '%s'\n" "$PW"; cat advocatio_desk_role_20260921.sql) \
--        | docker exec -i <casebible-pg> psql -U postgres -d casebible -v ON_ERROR_STOP=1

SELECT format('CREATE ROLE advocatio_desk LOGIN')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'advocatio_desk') \gexec

ALTER ROLE advocatio_desk WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'pw';
ALTER ROLE advocatio_desk SET default_transaction_read_only = on;
ALTER ROLE advocatio_desk SET statement_timeout = '30s';

GRANT CONNECT ON DATABASE casebible TO advocatio_desk;
GRANT USAGE ON SCHEMA catalog_reconcile TO advocatio_desk;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog_reconcile TO advocatio_desk;
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog_reconcile GRANT SELECT ON TABLES TO advocatio_desk;

SELECT rolname, rolcanlogin, rolsuper,
       has_table_privilege('advocatio_desk', 'catalog_reconcile.object_versions', 'SELECT') AS reads_objects,
       has_table_privilege('advocatio_desk', 'catalog_reconcile.occurrences', 'SELECT') AS reads_occurrences,
       has_schema_privilege('advocatio_desk', 'raw_duck', 'USAGE') AS raw_duck_usage
FROM pg_roles WHERE rolname = 'advocatio_desk';
