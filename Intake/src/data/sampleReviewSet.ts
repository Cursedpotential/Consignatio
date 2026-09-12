import type { AlbumSnapshot, ReviewItem } from "../domain/types";

const palette = [
  ["#244a56", "#9bb5b9", "#d6a558"],
  ["#5d6d72", "#d7ddd9", "#9b615a"],
  ["#213b4a", "#7f9ca1", "#d5c5a2"],
  ["#6f4d46", "#d2b49c", "#657b78"],
  ["#263d42", "#a9bab2", "#bf8b4b"],
  ["#3d5362", "#c8d3d5", "#815b55"],
];

function thumbnail(index: number, label: string): string {
  const colors = palette[index % palette.length];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320" viewBox="0 0 480 320"><rect width="480" height="320" fill="${colors[0]}"/><circle cx="355" cy="82" r="58" fill="${colors[2]}" opacity=".9"/><path d="M0 285L118 128l91 99 58-67 113 125z" fill="${colors[1]}"/><path d="M0 320v-44l132-98 79 75 57-55 133 122z" fill="#eef2ef" opacity=".38"/><text x="24" y="42" fill="#fff" font-family="monospace" font-size="17">${label}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

const raw = [
  ["IMG_1842.HEIC", "2024-07-14T18:42:11-04:00", "4032 × 3024", 4_822_144, "porch", 0.94],
  ["IMG_1843.HEIC", "2024-07-14T18:42:18-04:00", "4032 × 3024", 4_996_010, "porch", 0.92],
  ["IMG_1844.HEIC", "2024-07-14T18:43:02-04:00", "4032 × 3024", 5_242_880, "vehicle", 0.81],
  ["IMG_1845.HEIC", "2024-07-14T18:43:10-04:00", "4032 × 3024", 4_577_280, "vehicle", 0.84],
  ["Screenshot_20240714.png", "2024-07-14T20:06:41-04:00", "1179 × 2556", 1_368_064, "message", 0.89],
  ["IMG_1851.HEIC", "2024-07-14T20:22:08-04:00", "4032 × 3024", 5_701_632, "document", 0.76],
  ["IMG_1852.HEIC", "2024-07-14T20:22:16-04:00", "4032 × 3024", 5_439_488, "document", 0.78],
  ["IMG_1858.HEIC", "2024-07-15T08:14:50-04:00", "4032 × 3024", 4_128_768, "context", 0.64],
] as const;

export const sampleSnapshot: AlbumSnapshot = {
  id: "snapshot-immich-july-incident-v1",
  connector: "immich",
  instanceId: "immich-home",
  remoteAlbumId: "album-july-incident",
  remoteAlbumName: "July incident — review",
  capturedAt: "2026-08-30T07:30:00-04:00",
  memberRemoteIds: raw.map((_, index) => `immich-asset-${1842 + index}`),
  membershipDigest: "sha256:7bff…c412",
};

export const sampleReviewItems: ReviewItem[] = raw.map((entry, index) => {
  const [filename, capturedAt, dimensions, byteSize, tag, confidence] = entry;
  return {
    id: `CB-PHOTO-${String(index + 1).padStart(5, "0")}`,
    source: Object.freeze({
      filename,
      albumName: sampleSnapshot.remoteAlbumName,
      capturedAt,
      dimensions,
      byteSize,
      mimeType: filename.endsWith(".png") ? "image/png" : "image/heic",
      thumbnail: thumbnail(index, filename),
      atomicContainer: index === 4,
    }),
    proposal: Object.freeze({
      groupLabel: index < 2 ? "same scene" : index < 4 ? "vehicle sequence" : undefined,
      tags: [tag, index === 4 ? "atomic" : "needs-review"],
      confidence,
      rationale: index < 4 ? "Capture times and visual continuity are close." : "Filename and album context suggest review relevance.",
      producer: "album-sort proposal 0.3",
    }),
    annotations: {
      groupId: index < 2 ? "G-000018" : index < 4 ? "G-000019" : undefined,
      tags: [],
      status: index < 4 ? "candidate" : "unreviewed",
    },
    remoteReferences: [{
      connector: "immich",
      instanceId: sampleSnapshot.instanceId,
      remoteAssetId: sampleSnapshot.memberRemoteIds[index],
      remoteAlbumIds: [sampleSnapshot.remoteAlbumId],
      remoteUpdatedAt: "2026-08-29T21:18:00Z",
    }],
  } satisfies ReviewItem;
});

