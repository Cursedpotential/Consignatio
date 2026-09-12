export type ConnectorKind = "immich" | "photoprism" | "local-file";
export type ReviewStatus = "unreviewed" | "candidate" | "accepted" | "excluded";

export interface RemoteMediaReference {
  connector: ConnectorKind;
  instanceId: string;
  remoteAssetId: string;
  remoteAlbumIds: string[];
  sourceChecksum?: string;
  remoteUpdatedAt?: string;
}

export interface PhotoSource {
  filename: string;
  albumName: string;
  capturedAt: string;
  dimensions: string;
  byteSize: number;
  mimeType: string;
  thumbnail: string;
  atomicContainer: boolean;
  sourceKind?: "photo" | "document" | "object";
  fields?: Readonly<Record<string, unknown>>;
}

export interface MachineProposal {
  groupLabel?: string;
  tags: string[];
  confidence: number;
  rationale: string;
  producer: string;
}

export interface HumanAnnotations {
  groupId?: string;
  tags: string[];
  status: ReviewStatus;
  note?: string;
}

export interface ReviewItem {
  id: string;
  source: Readonly<PhotoSource>;
  proposal?: Readonly<MachineProposal>;
  annotations: HumanAnnotations;
  remoteReferences: RemoteMediaReference[];
}

export interface AlbumSnapshot {
  id: string;
  connector: ConnectorKind;
  instanceId: string;
  remoteAlbumId: string;
  remoteAlbumName: string;
  capturedAt: string;
  memberRemoteIds: string[];
  membershipDigest: string;
}
