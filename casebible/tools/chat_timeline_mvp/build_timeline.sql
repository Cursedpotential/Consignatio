-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Timeline MVP build (DuckDB scratch step): union extracted events, tag people, collapse duplicates
-- across exports while keeping every provenance row. Person terms come from the UNTRACKED server
-- terms file through DuckDB variables (set by build.py); no names are written in this file.
-- Inputs : events_raw in every attached extraction DB (view events_all, created by build.py).
-- Outputs: events_tagged, events_dedup, event_provenance, katrina_identity_evidence (tables in timeline_build.duckdb).

create or replace table events_tagged as
with e as (
  select *,
    lower(coalesce(sender, '')) as s_l,
    lower(array_to_string(coalesce(participants, []), ' | ') || ' | ' || coalesce(conversation_title, '') || ' | '
          || coalesce(contact_name, '') || ' | ' || coalesce(conversation_id, '')) as who_l,
    lower(coalesce(body, '')) as b_l
  from events_all
),
t as (
  select e.*,
    lower(sender) in ('owner', 'matt salem', 'matthew salem', 'me', 'matt') as from_owner,
    -- thread-level identity: participants/title/contact/folder name the person, or the counterparty
    -- phone is one confirmed for her (katrina_phones_confirmed, built by build.py from contact_name evidence).
    (regexp_matches(who_l, getvariable('katrina_strict'))
      -- folder names identify the thread only for per-thread exports; the SMS/call backups stored under
      -- "Messages with Katrina" are whole-phone backups, so they rely on contact_name / confirmed phone only.
      or (source_format not in ('sms_backup_xml', 'calls_backup_xml')
          and regexp_matches(lower(vault_key), 'inbox/katrinakinzel|messages with katrina|whatsapp chat - katrina'))
      or counterparty_phone in (select phone from katrina_phones_confirmed)) as katrina_thread,
    regexp_matches(b_l, getvariable('katrina_strict')) as katrina_name_in_body,
    regexp_matches(b_l || ' ' || who_l, getvariable('katrina_possible')) as katrina_possible_hit,
    regexp_matches(b_l || ' ' || who_l, getvariable('catrina_c')) as catrina_hit,
    regexp_matches(b_l, getvariable('landlord_context')) as landlord_ctx,
    regexp_matches(b_l, getvariable('nickname')) as nickname_hit,
    regexp_matches(b_l, getvariable('daughter_strong')) as daughter_strong_hit,
    regexp_matches(b_l, getvariable('daughter_weak')) as daughter_weak_hit,
    regexp_matches(b_l, getvariable('kinship')) as kinship_hit,
    regexp_matches(b_l, getvariable('custody')) as custody_hit,
    regexp_matches(b_l, getvariable('housing')) as housing_hit
  from e
)
select
  t.* exclude (s_l, who_l, b_l),
  case
    when katrina_thread and (coalesce(len(participants), 0) <= 2 or counterparty_phone is not null) then 'direct'
    when katrina_thread and regexp_matches(lower(coalesce(sender, '')), getvariable('katrina_strict')) then 'group_sent_by_her'
    when katrina_thread then 'group_participant'
    when katrina_name_in_body then 'name_mention'
    when catrina_hit and not landlord_ctx and (daughter_strong_hit or custody_hit) then 'catrina_confirmed_by_context'
    when nickname_hit and from_owner and not katrina_thread then 'nickname'
    when katrina_possible_hit then 'possible_surname_or_short_name'
    else null
  end as katrina_ref_type,
  case
    when katrina_thread or katrina_name_in_body or (catrina_hit and not landlord_ctx and (daughter_strong_hit or custody_hit)) then 'strong'
    when nickname_hit and from_owner and not katrina_thread then 'weak'
    when katrina_possible_hit then 'possible'
    else null
  end as katrina_conf,
  case when catrina_hit and landlord_ctx and not katrina_thread then 'catrina_landlord'
       when catrina_hit and not landlord_ctx and not katrina_thread and not (daughter_strong_hit or custody_hit) then 'catrina_ambiguous'
       else null end as catrina_class,
  case
    when daughter_strong_hit then 'strong'
    when kinship_hit then 'medium'
    when daughter_weak_hit and (katrina_thread or custody_hit) then 'weak'
    else null
  end as daughter_conf,
  custody_hit, housing_hit
from t;

-- Duplicate collapse: same thread identity + same instant + same normalized text = one event.
create or replace table events_keyed as
select *,
  md5(
    coalesce(counterparty_phone,
             array_to_string(list_sort(list_transform(coalesce(participants, []), x -> lower(trim(x)))), '|'),
             lower(coalesce(conversation_title, conversation_id, '')))
    || '#' || coalesce(epoch_ms(event_ts_utc)::varchar, 'local:' || coalesce(sort_ts::varchar, 'none:' || vault_key))
    || '#' || coalesce(event_kind, '')
    || '#' || md5(regexp_replace(lower(coalesce(body, '')), '\s+', ' ', 'g'))
  ) as dedup_key
from events_tagged;

create or replace table event_provenance as
select dedup_key, event_uid, source_format, extractor, vault_key, sha1, catalog_rel, member_path, record_index,
       ts_original, ts_field
from events_keyed;

create or replace table events_dedup as
select * exclude (rn) from (
  select k.*,
    count(*) over (partition by dedup_key) as n_sources,
    row_number() over (partition by dedup_key order by (tz_status = 'utc_known') desc, source_format, vault_key, record_index) as rn
  from events_keyed k
) where rn = 1;

-- Evidence for the identity list (owner confirms): which names/handles/phones sit on Katrina threads.
create or replace table katrina_identity_evidence as
select 'participant_or_sender' as kind, x as value, count(*) as n_events
from (select unnest(list_concat(coalesce(participants, []), [sender])) as x from events_dedup where katrina_ref_type in ('direct', 'group_sent_by_her'))
where x is not null and not lower(x) in ('owner', 'matt salem', 'matthew salem', 'me', 'matt')
group by all
union all
select 'phone_contact_name', counterparty_phone || ' = ' || coalesce(contact_name, '?'), count(*)
from events_dedup where counterparty_phone is not null and katrina_ref_type = 'direct' group by all;
