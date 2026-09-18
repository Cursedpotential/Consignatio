-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Timeline views over raw_duck.chat_events_20260918 (run after load_pg.sh).
create index on raw_duck.chat_events_20260918 (sort_ts);
create index on raw_duck.chat_events_20260918 (katrina_conf, sort_ts);
create index on raw_duck.chat_events_20260918 (daughter_conf, sort_ts);
create index on raw_duck.chat_event_provenance_20260918 (dedup_key);
create index chat_events_20260918_body_fts on raw_duck.chat_events_20260918
  using gin (to_tsvector('english', coalesce(body, '')));

create or replace view raw_duck.timeline_20260918 as
select sort_ts, tz_status, ts_original, source_format, event_kind, sender, recipients, conversation_title, body,
       katrina_ref_type, katrina_conf, daughter_conf, catrina_class, custody_hit, housing_hit, n_sources, dedup_key, vault_key
from raw_duck.chat_events_20260918;

-- Her direct threads, her own group messages, and strong name mentions. Excluded: group chats where she is
-- only a member, surname/short-name "possible" hits, and the owner's nickname hits (see timeline_katrina_weak).
create or replace view raw_duck.timeline_katrina_20260918 as
select * from raw_duck.timeline_20260918
where katrina_conf = 'strong' and katrina_ref_type <> 'group_participant';

create or replace view raw_duck.timeline_katrina_weak_20260918 as
select * from raw_duck.timeline_20260918 where katrina_conf in ('weak', 'possible');

create or replace view raw_duck.timeline_daughter_20260918 as
select * from raw_duck.timeline_20260918 where daughter_conf is not null;

create or replace view raw_duck.timeline_catrina_landlord_20260918 as
select * from raw_duck.timeline_20260918 where catrina_class is not null;

create or replace view raw_duck.timeline_day_counts_20260918 as
select sort_ts::date as day,
       count(*) as events,
       count(*) filter (where katrina_conf = 'strong' and katrina_ref_type <> 'group_participant') as katrina,
       count(*) filter (where daughter_conf is not null) as daughter,
       count(*) filter (where housing_hit) as housing
from raw_duck.chat_events_20260918 where sort_ts is not null group by 1;

-- No GRANT here: raw_duck's existing default ACL gives metabase_ro SELECT on postgres-created tables/views.
