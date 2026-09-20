-- Byline: Claude Code · Fable 5.1 · 2026-09-18
-- Read-only. Counts vault files per confirmed AI-chat naming pattern (shapes confirmed by reading
-- the first bytes of one example each, 2026-09-18 21:15 EDT). "files" = catalog occurrences,
-- "unique" = distinct content (sha1), so copies of the same export count once.
with f as (
  select vault_key, sha1, size, catalog_rel,
         regexp_replace(catalog_rel, '^.*/', '')    as name,
         regexp_replace(catalog_rel, '/[^/]*$', '') as dir
  from raw_duck.ai_chat_probe_20260918
  where catalog_rel is not null
    and catalog_rel !~* '(Claude-Slash-Commands|System-Prompt-Library|claude-context-master|Cool-Claude-Code-Stuff|Single-Shot-Brevity|claude-JSONL-browser|/raw_api_responses|\.smart-env|node_modules|site-packages|google photos|recup_dir|comfyui|text-generation-webui)'
),
pat(ord, label, service, rx) as (values
  (1,  'chat-memo_*.txt (all-conversations export, per-message timestamps)', 'chatgpt',    '^chat-memo_.*\.txt$'),
  (2,  'conversations.json / conversations*.zip (official export)',           'claude/chatgpt', '^conversations( \(\d+\))?\.(json|zip)$'),
  (3,  'ChatGPT - <title> / ChatGPT-<title>',                                  'chatgpt',    '^ChatGPT ?- ?.*\.(md|json|html|txt)$'),
  (4,  'gemini_<slug>_<timestamp>.md',                                         'gemini',     '^gemini_.*_20\d\d-\d\d-\d\dT.*\.(md|txt|html)$'),
  (5,  'Google_Gemini_<date>.md',                                              'gemini',     '^Google_Gemini_20\d\d-.*\.md$'),
  (6,  'Gemini - <title> / Gem=<title> / Gemini Content',                      'gemini',     '^(.?Gemini - |Gem=|Gemini Content).*\.(md|json|txt|html)$'),
  (7,  'Takeout Gemini Apps MyActivity',                                       'gemini',     '^MyActivity\.(html|json)$'),
  (8,  'Claude - <title> - Claude.md / <date>_Claude Chat_.md',                'claude',     '(^Claude - .*\.md$|Claude Chat_.*\.md$)'),
  (9,  'Claude-Conversation-<timestamp>.txt',                                  'claude',     '^Claude-Conversation-.*\.txt$'),
  (10, 'Perplexity Playground*.md / Perplexity context',                       'perplexity', '^Perplexity.*\.(md|txt)$'),
  (11, 'chat-export-<epoch>.json (Qwen / Open WebUI shape)',                   'qwen/other', '^chat-export-\d+\.json$'),
  (12, 'Venice Chat*.md',                                                      'venice',     '^Venice Chat.*\.md$'),
  (13, 'case chats.zip / chat_transcript_raw.txt / AI Lawyer*.md',             'mixed',      '^(case chats.*\.zip|chat_transcript_raw\.txt|AI Lawyer.*\.md)$')
)
select p.ord, p.label, p.service,
       count(*)                      as files,
       count(distinct f.sha1)        as unique_files,
       round(sum(f.size) / 1e6, 1)   as mb_all_copies,
       count(distinct f.dir)         as folders
from pat p join f on f.name ~* p.rx
  and not (p.ord = 7 and f.dir !~* 'gemini apps')
group by p.ord, p.label, p.service
union all
select 99, 'other files inside folders named chats / AI_Chats / Raw AI Chats / AI convos / Context_Files (lead only, confirm by content)', 'unknown',
       count(*), count(distinct sha1), round(sum(size) / 1e6, 1), count(distinct dir)
from f
where dir ~* '(/chats(/|$)|ai[_ ]chats|raw ai chats|ai convos|context_files|ai_resources/chats)'
  and not exists (select 1 from pat p where f.name ~* p.rx)
order by 1;
