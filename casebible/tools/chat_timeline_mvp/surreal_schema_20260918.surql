-- Byline: Claude Code · Opus 5 · 2026-09-18
-- Chat timeline MVP tables in Intake's SurrealDB (surreal-intake, ns consignatio / db intake), a new
-- dated table set beside the filesystem graph (owner 12:36 EDT: Surreal is the backend for this).
-- Rebuildable from B2 + raw_duck.chat_candidates_20260918; nothing here is canonical evidence.
-- No person names in this file: tags are computed upstream from an untracked terms file.

DEFINE TABLE IF NOT EXISTS tl_event_20260918 SCHEMALESS COMMENT 'One deduplicated chat/call event; provenance[] keeps every source row';
DEFINE FIELD IF NOT EXISTS sort_ts ON tl_event_20260918 TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS event_ts_utc ON tl_event_20260918 TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS tl_event_sort ON tl_event_20260918 FIELDS sort_ts;
DEFINE INDEX IF NOT EXISTS tl_event_kconf ON tl_event_20260918 FIELDS katrina_conf, sort_ts;
DEFINE INDEX IF NOT EXISTS tl_event_dconf ON tl_event_20260918 FIELDS daughter_conf, sort_ts;
DEFINE INDEX IF NOT EXISTS tl_event_format ON tl_event_20260918 FIELDS source_format;
DEFINE ANALYZER IF NOT EXISTS tl_text_20260918 TOKENIZERS blank, class, punct FILTERS lowercase, ascii;
DEFINE INDEX IF NOT EXISTS tl_event_body_ft ON tl_event_20260918 FIELDS body FULLTEXT ANALYZER tl_text_20260918 BM25;

DEFINE TABLE IF NOT EXISTS tl_person_20260918 SCHEMALESS COMMENT 'A sender/participant label as seen in the data (not a resolved identity)';
DEFINE TABLE IF NOT EXISTS tl_conversation_20260918 SCHEMALESS COMMENT 'Thread: phone, FB thread path, chat title';
DEFINE TABLE IF NOT EXISTS tl_source_20260918 SCHEMALESS COMMENT 'B2 vault object an event was read from';

DEFINE TABLE IF NOT EXISTS tl_sent_20260918 TYPE RELATION IN tl_person_20260918 OUT tl_event_20260918 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_in_20260918 TYPE RELATION IN tl_event_20260918 OUT tl_conversation_20260918 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_from_20260918 TYPE RELATION IN tl_event_20260918 OUT tl_source_20260918 SCHEMALESS;

-- Timeline queries (the "views"). $from/$to are datetimes or NONE; $person is a substring on sender/participants.
DEFINE FUNCTION OVERWRITE fn::timeline_20260918($from: option<datetime>, $to: option<datetime>, $person: option<string>, $source: option<string>, $lim: option<int>) {
  RETURN SELECT sort_ts, tz_status, ts_original, source_format, sender, recipients, conversation_title, body,
                katrina_ref_type, daughter_conf, n_sources, id
    FROM tl_event_20260918
    WHERE ($from IS NONE OR sort_ts >= $from) AND ($to IS NONE OR sort_ts < $to)
      AND ($source IS NONE OR source_format = $source)
      AND ($person IS NONE OR string::contains(string::lowercase(sender ?? ''), string::lowercase($person))
           OR string::contains(string::lowercase(array::join(participants ?? [], ' ')), string::lowercase($person)))
    ORDER BY sort_ts LIMIT $lim ?? 500;
};
DEFINE FUNCTION OVERWRITE fn::timeline_katrina_20260918($from: option<datetime>, $to: option<datetime>, $lim: option<int>) {
  RETURN SELECT sort_ts, tz_status, ts_original, source_format, sender, conversation_title, body, katrina_ref_type,
                daughter_conf, n_sources, id
    FROM tl_event_20260918
    WHERE katrina_conf = 'strong' AND katrina_ref_type != 'group_participant'
      AND ($from IS NONE OR sort_ts >= $from) AND ($to IS NONE OR sort_ts < $to)
    ORDER BY sort_ts LIMIT $lim ?? 500;
};
DEFINE FUNCTION OVERWRITE fn::timeline_daughter_20260918($from: option<datetime>, $to: option<datetime>, $min_conf: option<string>, $lim: option<int>) {
  LET $ok = IF $min_conf = 'strong' THEN ['strong'] ELSE IF $min_conf = 'medium' THEN ['strong', 'medium'] ELSE ['strong', 'medium', 'weak'] END;
  RETURN SELECT sort_ts, tz_status, ts_original, source_format, sender, conversation_title, body, daughter_conf,
                katrina_ref_type, n_sources, id
    FROM tl_event_20260918
    WHERE daughter_conf IN $ok AND ($from IS NONE OR sort_ts >= $from) AND ($to IS NONE OR sort_ts < $to)
    ORDER BY sort_ts LIMIT $lim ?? 500;
};
DEFINE FUNCTION OVERWRITE fn::timeline_search_20260918($q: string, $lim: option<int>) {
  RETURN SELECT sort_ts, source_format, sender, conversation_title, body, katrina_ref_type, daughter_conf, id,
                search::score(1) AS score
    FROM tl_event_20260918 WHERE body @1@ $q ORDER BY score DESC LIMIT $lim ?? 50;
};
DEFINE FUNCTION OVERWRITE fn::timeline_day_counts_20260918($scope: option<string>) {
  RETURN SELECT day, count() AS n FROM (
      SELECT time::format(sort_ts, '%Y-%m-%d') AS day FROM tl_event_20260918
      WHERE sort_ts IS NOT NONE AND (
        $scope IS NONE
        OR ($scope = 'katrina' AND katrina_conf = 'strong' AND katrina_ref_type != 'group_participant')
        OR ($scope = 'daughter' AND daughter_conf IS NOT NONE))
    ) GROUP BY day ORDER BY day;
};
