# Old Weaviate instance stopped — owner direction 2026-09-11

The owner explicitly superseded the historical side-by-side hold and directed
stopping the original instance if the replacement was good. This is not permission
to delete retained data or restart either host.

Verified immediately before stopping:

- Both endpoints reported readiness HTTP200.
- Replacement `100.91.190.107:8082`, Coolify application
  `data-weaviate-native-v1` (`v43tfq25o7i561n4lnc124p2`), was healthy.
- All seven shared collections had matching counts, totaling 3,035 objects.
- Original's additional `EvidenceChunkV1` collection contained zero objects.
- Earlier migration receipt records independent semantic parity and real vector/
  hybrid retrieval parity. This turn checked health/counts, not another full export.

Action: Coolify POST stop for `data-weaviate-files`
(`o97r85b7nagwjuncs4oo07hs`), specifying `docker_cleanup=false`. No direct Docker
stop/remove command, application deletion or data deletion was issued.

Verified outcome:

- Port8081 no longer responds; its old container is absent after Coolify stop.
- Coolify status settled to `exited:unhealthy` (initial status was stale).
- Replacement container remains healthy on HTTP8082 and gRPC50052; readiness200.
- Original persistence is a bind at `/data/probata/volumes/weaviate`; directory
  existence verified after stopping. No data bytes were exported or removed.

The historical deployment-choice hold is superseded: Intake's intended target is
the remaining instance at HTTP8082/gRPC50052, with its own collection. This action
does not provision that collection or claim downstream clients were repointed.
Existing clients still configured for8081 require their own configuration update.
Do not restart the original based on an older migration hold.

## Owner-authorized retirement follow-up

Owner approved removing the stopped Coolify entry and quarantining the retained
old data. Verified the live replacement binds the separate directory
`/data/probata/volumes/weaviate-native-v1`. No running container mounted the old
`/data/probata/volumes/weaviate` path.

The old directory was moved, without overwriting an existing destination, to:

`/data/probata/to_be_deleted/weaviate-old-8081-o97r85b7nagwjuncs4oo07hs`

Both source and destination parents were resolved and checked before the move.
Only the owner may permanently delete the quarantined bytes. This same-server
move does not free their disk space.

Then the old application was re-read, exact name and stopped status verified,
and DELETE submitted through the Coolify API for only
`o97r85b7nagwjuncs4oo07hs`. No new instance settings were changed. The old Coolify
entry is not recoverable by a start operation after deletion; retained data can
be used to recreate a service if needed. Verification results follow below.

- Old Coolify application lookup: HTTP404, confirming entry removal.
- Only the replacement Weaviate container remains; Docker reports healthy.
- Replacement readiness: HTTP200 on port8082.
- Original data path absent; named quarantine directory exists after deletion.
- No permanent data-file deletion, host restart, or replacement-service restart.
