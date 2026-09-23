-- Byline: Claude Code · Fable 5.1 · 2026-09-18
-- Read-only. Owner 2026-09-18 21:14 EDT: "many chats are just the first sentence of the first prompt".
-- Finds md/txt/html/json files whose NAME reads like a sentence (5+ words), that the service-name
-- patterns in ai_chat_pattern_counts_20260918.sql do not already catch. A lead only; content confirms.
with f as (
  select vault_key, sha1, size, ext, catalog_rel,
         regexp_replace(catalog_rel, '^.*/', '')    as name,
         regexp_replace(catalog_rel, '/[^/]*$', '') as dir
  from raw_duck.ai_chat_probe_20260918
  where catalog_rel is not null
    and probe_class in ('text', 'json', 'html')
    and catalog_rel !~* '(Claude-Slash-Commands|System-Prompt-Library|claude-context-master|Cool-Claude-Code-Stuff|Single-Shot-Brevity|claude-JSONL-browser|/raw_api_responses|\.smart-env|node_modules|site-packages|google photos|recup_dir|comfyui|text-generation-webui|/takeout/|your_facebook_activity|/messages/inbox/|\.obsidian|/voice/|/Mail/)'
),
s as (
  select *,
         regexp_replace(name, '\.[A-Za-z0-9]+$', '') as stem
  from f
)
select dir, name, round(size / 1e3, 0) as kb
from s
where array_length(regexp_split_to_array(trim(stem), '[ _]+'), 1) >= 5
  and length(stem) >= 28
  and stem ~ '[a-z]{3,} [a-z]{2,}'
  and name !~* '^(ChatGPT ?-|gemini_|Google_Gemini|.?Gemini - |Gem=|Gemini Content|Claude - |Claude-Conversation|Perplexity|chat-export|chat-memo|Venice Chat)'
  and stem ~* '^(how|what|why|can|could|would|should|is|are|do|does|did|i |i''|im |my |please|help|need|explain|tell|write|create|make|give|let|we |you |act |analy|review|draft|summar|here|this|the |a |an |in |on |if |so |ok|hey|hi )'
order by dir, name
limit 200;
