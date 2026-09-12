# Media connector contract

## Required operations

```ts
interface MediaConnector {
  testConnection(): Promise<ConnectorStatus>;
  listAlbums(cursor?: string): Promise<Page<RemoteAlbum>>;
  snapshotAlbum(albumId: string): Promise<AlbumSnapshot>;
  diffAlbum(previous: AlbumSnapshot): Promise<AlbumDelta>;
  getAsset(assetId: string): Promise<RemoteAssetMetadata>;
  getThumbnail(assetId: string, size: ThumbnailSize): Promise<Blob>;
  prepareOriginalReference(assetId: string): Promise<OpaqueSourceReference>;
  publishReviewProjection?(request: PublishProjectionRequest): Promise<RunReceipt>;
}
```

## Immich

Use a dedicated API key with the smallest possible read permissions. Write-back
permissions for albums, album membership, tags, or stacks are separately enabled.
The connector uses the generated OpenAPI client pinned to the detected server
version. It does not read Immich's PostgreSQL database directly.

## PhotoPrism

Use authenticated REST for metadata and previews. WebDAV is reserved for explicitly
approved original-file transfer because it exposes filesystem-like write and delete
operations. The connector records the detected server version because PhotoPrism's
REST routes do not currently carry a formal deprecation guarantee.

## Sync semantics

- Initial import creates a frozen snapshot.
- Refresh creates another snapshot plus an added/removed/changed delta.
- No remote deletion is propagated.
- Source-service metadata is cached separately from embedded file metadata.
- Optional write-back creates a convenience projection and a receipt; it is not the
  canonical review or evidence decision.

## Platform handoff

`prepareOriginalReference` returns an opaque, authenticated reference. The Workbench
submits that reference to UIW. UIW owns acquisition, hash/metadata preview,
accept/reject state, context persistence, and the later evidence-promotion boundary.

