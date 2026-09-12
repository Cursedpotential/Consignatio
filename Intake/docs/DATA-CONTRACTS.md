# Data contracts

> _Byline: Codex · GPT-5 · 2026-08-30._

## Imported dataset

JSON imports accept a top-level array or an `items`, `records`, `data`, or
`objects` array. CSV imports require one header row with unique, non-empty field
names; blank headers receive deterministic `column_N` names. Quoted commas,
escaped quotes, and quoted line breaks are preserved.

Scalar source values remain strings, numbers, booleans, or null. Nested JSON
values are losslessly projected as JSON strings for display in the current
slice. The import preview records field order, inferred display type, populated
count, and a bounded sample. Loading creates immutable source objects and empty
human-annotation overlays; it never rewrites the selected file.

## Review record

```ts
interface ReviewRecord<TSource> {
  id: string;
  source: Readonly<TSource>;
  proposal?: Readonly<MachineProposal>;
  annotations: HumanAnnotations;
  remoteReferences: RemoteMediaReference[];
}
```

The `source` object is immutable after import. Corrections are annotations that
state what is corrected, why, by whom, and when; they do not rewrite the imported
value.

## Album snapshot

```ts
interface AlbumSnapshot {
  id: string;
  connector: "immich" | "photoprism";
  instanceId: string;
  remoteAlbumId: string;
  remoteAlbumName: string;
  capturedAt: string;
  memberRemoteIds: string[];
  membershipDigest: string;
  priorSnapshotId?: string;
}
```

Album membership is contextual provenance. Evidence identity belongs to acquired
content bytes, not the album name or membership position.

## Group identifiers

Human groups receive monotonically allocated identifiers such as `G-000018`.
Identifiers are stable and never silently renumbered. Dissolved identifiers remain
retired in the operation log.

## Remote identity

```ts
interface RemoteMediaReference {
  connector: "immich" | "photoprism";
  instanceId: string;
  remoteAssetId: string;
  remoteAlbumIds: string[];
  sourceChecksum?: string;
  remoteUpdatedAt?: string;
}
```

Remote identity and content identity are separate. One byte-identical item may have
many remote references; one remote record may later point to changed bytes and must
therefore be detected as a new version.

## Provenance layers

Every displayed field belongs to exactly one layer:

- `source`: immutable values supplied by the source system or file;
- `proposal`: machine or rule-generated suggestion with model/rule metadata;
- `human`: accepted, rejected, or edited decision;
- `derived`: deterministic calculation with algorithm and inputs.
