-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- tag_events_v1 — person tagging + dedup key for one extracted batch (DuckDB, run by elt_run.py).
-- Same rules and the same dedup key as the 2026-09-18 afternoon build (build_timeline.sql), so an event
-- re-extracted by an ELT template lands on the SAME row / the SAME Weaviate object as before.
-- Terms come from DuckDB variables set by the runner out of the UNTRACKED server terms file; no names here.
-- Input : table ev_in (event contract + vault_key, sha1, catalog_rel, source_format, extractor, member_path).
-- Output: table ev_tagged.
create or replace table ev_tagged as
with e as (
  select *,
    lower(array_to_string(coalesce(participants, []), ' | ') || ' | ' || coalesce(conversation_title, '') || ' | '
          || coalesce(contact_name, '') || ' | ' || coalesce(conversation_id, '')) as who_l,
    lower(coalesce(body, '')) as b_l
  from ev_in
),
t as (
  select e.*,
    lower(coalesce(sender, '')) in ('owner', 'matt salem', 'matthew salem', 'me', 'matt') as from_owner,
    -- Thread identity is CONTENT ONLY (owner 2026-09-18 21:08: folder names mean nothing): the thread
    -- names her in its participants / title / contact_name / conversation id, or the counterparty phone is
    -- one of the owner-confirmed numbers.
    (regexp_matches(who_l, getvariable('katrina_strict'))
      or counterparty_phone in (select unnest(getvariable('katrina_phones_confirmed')))) as katrina_thread,
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
  t.* exclude (who_l, b_l),
  case
    when katrina_thread and (coalesce(len(participants), 0) <= 2 or counterparty_phone is not null) then 'direct'
    when katrina_thread and regexp_matches(lower(coalesce(sender, '')), getvariable('katrina_strict')) then 'group_sent_by_her'
    when katrina_thread then 'group_participant'
    when katrina_name_in_body then 'name_mention'
    when catrina_hit and not landlord_ctx and (daughter_strong_hit or custody_hit) then 'catrina_confirmed_by_context'
    when nickname_hit and from_owner and not katrina_thread then 'nickname'
    when katrina_possible_hit then 'possible_surname_or_short_name'
  end as katrina_ref_type,
  case
    when katrina_thread or katrina_name_in_body or (catrina_hit and not landlord_ctx and (daughter_strong_hit or custody_hit)) then 'strong'
    when nickname_hit and from_owner and not katrina_thread then 'weak'
    when katrina_possible_hit then 'possible'
  end as katrina_conf,
  case when catrina_hit and landlord_ctx and not katrina_thread then 'catrina_landlord'
       when catrina_hit and not landlord_ctx and not katrina_thread and not (daughter_strong_hit or custody_hit) then 'catrina_ambiguous'
  end as catrina_class,
  case when daughter_strong_hit then 'strong'
       when kinship_hit then 'medium'
       when daughter_weak_hit and (katrina_thread or custody_hit) then 'weak'
  end as daughter_conf,
  coalesce(sort_ts, event_ts_utc::timestamp) as sort_ts_final,
  md5(
    coalesce(counterparty_phone,
             array_to_string(list_sort(list_transform(coalesce(participants, []), x -> lower(trim(x)))), '|'),
             lower(coalesce(conversation_title, conversation_id, '')))
    || '#' || coalesce(epoch_ms(event_ts_utc)::varchar, 'local:' || coalesce(sort_ts::varchar, 'none:' || vault_key))
    || '#' || coalesce(event_kind, '')
    || '#' || md5(regexp_replace(lower(coalesce(body, '')), '\s+', ' ', 'g'))
  ) as dedup_key
from t;
