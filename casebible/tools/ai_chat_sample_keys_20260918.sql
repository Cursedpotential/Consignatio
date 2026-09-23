-- Byline: Claude Code · Fable 5.1 · 2026-09-18
-- Read-only. One example file per suspected AI-chat naming pattern, with its vault key,
-- so the first bytes can be read in place to confirm the shape.
with f as (
  select vault_key, size, catalog_rel, regexp_replace(catalog_rel, '^.*/', '') as name
  from raw_duck.ai_chat_probe_20260918
  where catalog_rel is not null
),
pat(label, rx) as (values
  ('gemini_slug_ts_md',      '^gemini_.*_20\d\d-\d\d-\d\dT.*\.md$'),
  ('google_gemini_date_md',  '^Google_Gemini_20\d\d-.*\.md$'),
  ('gemini_dash_title',      '^.?Gemini - .*\.(md|json)$'),
  ('gem_equals_title',       '^Gem=.*\.(md|json)$'),
  ('chatgpt_dash_title',     '^ChatGPT ?- ?.*\.(md|json|html)$'),
  ('claude_conversation',    '^Claude-Conversation-.*\.txt$'),
  ('claude_chat_md',         'Claude( Chat_)?.*\.md$'),
  ('perplexity_playground',  '^Perplexity Playground.*\.md$'),
  ('conversations_json',     '^conversations\.json$'),
  ('chat_export_json',       '^chat-export-\d+\.json$'),
  ('sessions_json',          '^\d+ Sessions - .*\.json$'),
  ('fb_ai_conversations',    '^ai_conversations\.json$'),
  ('chat_memo_txt',          '^chat-memo_.*\.txt$'),
  ('venice_chat',            '^Venice Chat.*\.md$')
)
select p.label, x.vault_key, x.size, x.name
from pat p
cross join lateral (
  select vault_key, size, name from f where name ~* p.rx order by size desc limit 1
) x
order by p.label;
