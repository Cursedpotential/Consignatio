-- Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
-- Lean chat-timeline graph in Intake SurrealDB (surreal-intake, ns consignatio / db intake).
-- Generation _20260919. The earlier _20260918 tables are left untouched.
--
-- Shape rationale (measured on the 21,106 rows of the _20260918 set):
--   message text = 4.97 MB, on-disk = 164 MB, i.e. 97% of storage was NOT the message.
--   Provenance was stored three times (event array + edge fields + top-level scalars),
--   conversation-level fields were repeated on every event, and 13 derived flags rode along.
--   Here: the event row keeps only what a timeline row shows; identity lives on source_file,
--   participants live on the conversation, provenance lives on the from_file edge.
-- No person names in this file. Identity mapping comes from an untracked terms file on the host.

-- ---------- entities ----------
DEFINE TABLE IF NOT EXISTS tl_person_20260919 SCHEMALESS
  COMMENT 'A resolved human. kind=identity for confirmed people, kind=participant for one-label-one-person';
DEFINE INDEX IF NOT EXISTS tl_person_kind ON tl_person_20260919 FIELDS kind;

DEFINE TABLE IF NOT EXISTS tl_alias_20260919 SCHEMALESS
  COMMENT 'A handle as it appears in the data: display name, phone, email, export label';
DEFINE INDEX IF NOT EXISTS tl_alias_label ON tl_alias_20260919 FIELDS label;

DEFINE TABLE IF NOT EXISTS tl_conversation_20260919 SCHEMALESS
  COMMENT 'A thread: phone thread, FB thread, chat title. Participants live here, not on every event';

DEFINE TABLE IF NOT EXISTS tl_source_20260919 SCHEMALESS
  COMMENT 'The B2 vault object an event was read from. sha1 and catalog_rel resolved from the catalog';
DEFINE INDEX IF NOT EXISTS tl_source_sha1 ON tl_source_20260919 FIELDS sha1;

DEFINE TABLE IF NOT EXISTS tl_event_20260919 SCHEMALESS
  COMMENT 'One deduplicated chat/call event, keyed by dedup_key. Lean row: see header';
DEFINE FIELD IF NOT EXISTS ts ON tl_event_20260919 TYPE option<datetime>;
DEFINE INDEX IF NOT EXISTS tl_event_ts ON tl_event_20260919 FIELDS ts;
DEFINE INDEX IF NOT EXISTS tl_event_kconf ON tl_event_20260919 FIELDS katrina_conf, ts;
DEFINE INDEX IF NOT EXISTS tl_event_dconf ON tl_event_20260919 FIELDS daughter_conf, ts;
DEFINE INDEX IF NOT EXISTS tl_event_conv ON tl_event_20260919 FIELDS conv, ts;

-- ---------- graph edges ----------
DEFINE TABLE IF NOT EXISTS tl_sent_20260919 TYPE RELATION IN tl_person_20260919 OUT tl_event_20260919 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_in_20260919 TYPE RELATION IN tl_event_20260919 OUT tl_conversation_20260919 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_to_20260919 TYPE RELATION IN tl_event_20260919 OUT tl_person_20260919 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_from_file_20260919 TYPE RELATION IN tl_event_20260919 OUT tl_source_20260919 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_has_alias_20260919 TYPE RELATION IN tl_person_20260919 OUT tl_alias_20260919 SCHEMALESS;
DEFINE TABLE IF NOT EXISTS tl_about_20260919 TYPE RELATION IN tl_event_20260919 OUT tl_person_20260919 SCHEMALESS
  COMMENT 'Event mentions/concerns a person; conf = strong|medium|weak|possible';
DEFINE TABLE IF NOT EXISTS tl_next_20260919 TYPE RELATION IN tl_event_20260919 OUT tl_event_20260919 SCHEMALESS
  COMMENT 'Next event in the same conversation, by time';

-- ---------- timeline functions ----------
-- $person: a tl_person id slug ('katrina', 'daughter', 'catrina_landlord', 'owner', or a
-- participant key), or any substring of a person name / alias label.
DEFINE FUNCTION OVERWRITE fn::timeline($person: option<string>, $from: option<datetime>, $to: option<datetime>, $lim: option<int>) {
  LET $q = string::lowercase($person ?? '');
  LET $pid = IF $person IS NONE THEN NONE ELSE type::record('tl_person_20260919:' + $person) END;
  LET $ids = IF $person IS NONE THEN NONE ELSE array::distinct(array::flatten([
      (SELECT VALUE id FROM tl_person_20260919
        WHERE id = $pid OR string::contains(string::lowercase(name ?? ''), $q)),
      (SELECT VALUE person FROM tl_alias_20260919
        WHERE string::contains(string::lowercase(label ?? ''), $q))
    ])) END;
  RETURN SELECT ts, fmt, sender_name, conv.title AS conversation, body, katrina, katrina_conf, daughter_conf, n_src, id
    FROM tl_event_20260919
    WHERE ($ids IS NONE
           OR sender_person IN $ids
           OR (->tl_to_20260919->tl_person_20260919) CONTAINSANY $ids
           OR (->tl_about_20260919->tl_person_20260919) CONTAINSANY $ids)
      AND ($from IS NONE OR ts >= $from) AND ($to IS NONE OR ts < $to)
    ORDER BY ts LIMIT $lim ?? 500;
};

-- Direct conversation with Katrina: her threads and messages, group-only participation excluded.
DEFINE FUNCTION OVERWRITE fn::timeline_katrina($from: option<datetime>, $to: option<datetime>, $lim: option<int>) {
  RETURN SELECT ts, fmt, sender_name, conv.title AS conversation, body, katrina, n_src, id
    FROM tl_event_20260919
    WHERE katrina_conf = 'strong' AND katrina != 'group_participant'
      AND ($from IS NONE OR ts >= $from) AND ($to IS NONE OR ts < $to)
    ORDER BY ts LIMIT $lim ?? 500;
};

-- $min_conf: 'strong' | 'medium' (default) | 'weak'.
DEFINE FUNCTION OVERWRITE fn::timeline_daughter($from: option<datetime>, $to: option<datetime>, $min_conf: option<string>, $lim: option<int>) {
  LET $ok = IF $min_conf = 'strong' THEN ['strong'] ELSE IF $min_conf = 'weak' THEN ['strong', 'medium', 'weak'] ELSE ['strong', 'medium'] END;
  RETURN SELECT ts, fmt, sender_name, conv.title AS conversation, body, daughter_conf, katrina, n_src, id
    FROM tl_event_20260919
    WHERE daughter_conf IN $ok AND ($from IS NONE OR ts >= $from) AND ($to IS NONE OR ts < $to)
    ORDER BY ts LIMIT $lim ?? 500;
};

-- $scope: NONE (everything) | 'katrina' | 'daughter'.
DEFINE FUNCTION OVERWRITE fn::day_counts($scope: option<string>) {
  RETURN SELECT day, count() AS n FROM (
      SELECT time::format(ts, '%Y-%m-%d') AS day FROM tl_event_20260919
      WHERE ts IS NOT NONE AND (
        $scope IS NONE
        OR ($scope = 'katrina' AND katrina_conf = 'strong' AND katrina != 'group_participant')
        OR ($scope = 'daughter' AND daughter_conf IS NOT NONE))
    ) GROUP BY day ORDER BY day;
};
