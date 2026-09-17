-- Byline: Claude Code · Opus 5 · 2026-09-17
-- Intake engine v1: append-only overlay of file operations performed on catalog:// (parent answer 08:58 EDT, option A).
-- The engine performs the real B2 operation on the vault object first, then appends one row here in the same request.
-- raw_duck.source_occurrences and raw_duck.vault_objects_20260916_r4 are never rewritten; the catalog:// listing
-- applies these rows on top of raw_duck.intake_catalog_fs_20260917 / _dirs_20260917.
--
-- Created by cb_agent (its existing CREATE on raw_duck; no grant):
--   docker exec -i fgz1n7useplhk0t91uk7k1aw psql -U cb_agent -d casebible -v ON_ERROR_STOP=1 < intake_fs_ops_20260917.sql
\pset pager off

create table if not exists raw_duck.intake_fs_ops_20260917 (
  op_id          bigserial primary key,
  at             timestamptz not null default now(),
  op             text not null check (op in ('rename', 'move', 'copy', 'delete', 'mkdir', 'relocate')),
  kind           text not null check (kind in ('file', 'dir')),
  from_rel       text,          -- catalog path (no scheme) before the op
  to_rel         text,          -- catalog path after the op; null when the entry left the catalog tree
  vault_key_from text,          -- bucket-relative B2 key before the op (file ops)
  vault_key_to   text,          -- bucket-relative B2 key after the op; null when deleted
  b2_path_to     text,          -- destination on the mount for copy/relocate out of catalog://
  actor          text not null default 'intake-engine',
  detail         jsonb not null default '{}'::jsonb
);

select count(*) as ops from raw_duck.intake_fs_ops_20260917;
