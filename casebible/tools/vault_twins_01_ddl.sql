CREATE TABLE IF NOT EXISTS raw_duck.vault_objects_stage (
  key   text,
  size  bigint,
  b2_id text
);
TRUNCATE raw_duck.vault_objects_stage;

CREATE TABLE IF NOT EXISTS raw_duck.vault_objects (
  key         text PRIMARY KEY,
  size        bigint NOT NULL,
  b2_id       text,
  md5         text,
  sha1        text,
  hash_source text,
  depth       int
);
