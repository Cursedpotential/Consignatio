-- Byline: Claude Code · Fable 5.1 · 2026-09-14
-- Occurrence catalog for the B2 consolidation: one row per source file, every source, every time —
-- "bytes stored once on B2, metadata N times in the catalog" (owner decision 2026-09-13).
-- Idempotent DDL; loaders upsert by (source, scope, path). Never hand-edited.
create table if not exists raw_duck.source_occurrences (
  source            text not null,            -- 'onedrive' | 'gdrive/salemnet' | 'gdrive/salem85' | 'local/D-Backup' | ...
  scope             text not null,            -- source-native root, e.g. 'Case Bible', 'Documents/CSV'
  path              text not null,            -- relative to scope, forward slashes
  size              bigint not null,
  modtime           timestamptz,
  source_id         text,                     -- provider object id (OneDrive/Drive id)
  native_hash_kind  text,                     -- 'quickxor' | 'md5' | 'sha256' | null
  native_hash       text,
  md5               text,                     -- server-side content md5 when computed
  disposition       text not null,            -- content_on_b2 | to_copy | copied | zero_byte | junk_excluded | pending_hash
  b2_key            text,                     -- object key on b2:salem-data holding these bytes
  matched_origin    text,                     -- b2_content.origin for content_on_b2 (carrier | preexisting)
  metadata          jsonb,                    -- provider metadata as listed (btime, creators, mime, ...)
  recorded_at       timestamptz not null default now(),
  primary key (source, scope, path, source_id)
);
-- 2026-09-14: Google Drive paths are not unique (duplicate top-level folders), so identity is
-- (source, scope, path, source_id); source_id is '' where the provider has none. Idempotent migration:
alter table raw_duck.source_occurrences alter column source_id set default '';
update raw_duck.source_occurrences set source_id = '' where source_id is null;
alter table raw_duck.source_occurrences alter column source_id set not null;
do $$ begin
  if not exists (select 1 from pg_constraint c join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any(c.conkey)
                 where c.conrelid = 'raw_duck.source_occurrences'::regclass and c.contype = 'p' and a.attname = 'source_id') then
    alter table raw_duck.source_occurrences drop constraint if exists source_occurrences_pkey;
    alter table raw_duck.source_occurrences add primary key (source, scope, path, source_id);
  end if;
end $$;
create index if not exists source_occurrences_md5_size on raw_duck.source_occurrences (md5, size);
create index if not exists source_occurrences_disposition on raw_duck.source_occurrences (disposition);
