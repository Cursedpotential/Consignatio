-- Byline: Claude Code · Fable 5.1 · 2026-09-18
-- Read-only. Owner 2026-09-18 21:10 EDT: read the directory tree a few levels down, look at the
-- file names, make good guesses, then open some files to confirm and produce a pattern.
-- "Chats" = the owner's conversations WITH AI. "Message transcripts" = SMS/Messenger/etc.
-- Source: raw_duck.ai_chat_probe_20260918 (every json/text/html/zip in the vault, with its
-- original catalog path). Folder names are a lead only; content confirms.
with f as (
  select catalog_rel, size, ext, probe_class,
         regexp_replace(catalog_rel, '/[^/]*$', '') as dir,
         regexp_replace(catalog_rel, '^.*/', '')    as name
  from raw_duck.ai_chat_probe_20260918
  where catalog_rel is not null
    and catalog_rel !~* '(google photos|recup_dir|comfyui|text-generation-webui|node_modules|site-packages|\.obsidian|supplemental-metadata|/photos from |\.(heic|jpg|jpeg|png|mp4|mov)\.json$)'
)
select dir,
       count(*)                                   as n,
       round(sum(size) / 1e6, 1)                  as mb,
       string_agg(distinct ext, ',')              as exts,
       (array_agg(name order by size desc))[1:3]  as examples
from f
where name ~* '(chat|gpt|claude|gemini|copilot|perplex|grok|deepseek|conversation|bard|openai|anthropic|transcript|handover|handoff|session|prompt|(^|[^a-z])ai([^a-z]|$))'
   or dir  ~* '(ai[_ -]?chat|chatgpt|claude|gemini|copilot|perplexity|/chats?(/|$)|conversations?)'
group by dir
order by n desc
limit 80;
