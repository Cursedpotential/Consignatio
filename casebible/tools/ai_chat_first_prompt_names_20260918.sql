-- Byline: Claude Code · Fable 5.1 · 2026-09-18
-- Read-only. Chat files named after the first sentence of the first prompt. Two exporter
-- signatures seen in the names: (a) stem cut at ~50 characters, often mid-word, optional
-- " (1)" / " 2" copy suffix; (b) stem cut and ended with "..." / "....". Lead only; content confirms.
with f as (
  select vault_key, sha1, size, ext, catalog_rel,
         regexp_replace(catalog_rel, '^.*/', '')    as name,
         regexp_replace(catalog_rel, '/[^/]*$', '') as dir
  from raw_duck.ai_chat_probe_20260918
  where catalog_rel is not null
    and probe_class in ('text', 'json', 'html')
    and catalog_rel !~* '(Claude-Slash-Commands|System-Prompt-Library|claude-context-master|Cool-Claude-Code-Stuff|Single-Shot-Brevity|claude-JSONL-browser|/raw_api_responses|\.smart-env|node_modules|site-packages|google photos|recup_dir|comfyui|text-generation-webui|/takeout/|your_facebook_activity|/messages/inbox/|\.obsidian|/voice/|/Mail/|Trilium)'
),
s as (
  select *,
         regexp_replace(regexp_replace(name, '\.[A-Za-z0-9]+$', ''), '( \(\d+\)| \d)$', '') as stem
  from f
),
c as (
  select *,
    case
      when stem ~ '\.{3,}$'                                   then 'b: cut with dots'
      when length(stem) between 47 and 51 and stem ~ ' '
           and stem !~ '^[A-Z][a-z]+( [A-Z][a-z]+){3,}'        then 'a: cut at ~50 chars'
    end as sig
  from s
  where array_length(regexp_split_to_array(trim(stem), ' +'), 1) >= 5
    and name !~* '^(ChatGPT ?-|gemini_|Google_Gemini|.?Gemini - |Gem=|Gemini Content|Claude - |Claude-Conversation|Perplexity|chat-export|chat-memo|Venice Chat)'
)
select 'COUNT' as kind, sig as a, count(*)::text as b, count(distinct sha1)::text as c, round(sum(size)/1e6,1)::text as d
from c where sig is not null group by sig
union all
select 'SAMPLE', vault_key, name, size::text, sig
from (select *, row_number() over (partition by sig order by md5(name)) rn from c where sig is not null) z
where rn <= 3
order by 1, 2;
