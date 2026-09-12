import type { HumanAnnotations, ReviewItem } from "./types";

export interface ReviewQuery {
  text: string;
  lens: "all" | "unreviewed" | "grouped";
  sort: "source-order" | "filename" | "size" | `field:${string}`;
  direction: "asc" | "desc";
}

function searchable(value: unknown): string {
  if (value == null) return "";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

function missing(value: unknown): boolean {
  return value == null || value === "" || (typeof value === "number" && !Number.isFinite(value));
}

/** Sort known values before absent ones in either direction; never guess date semantics. */
function compare(a: unknown, b: unknown, direction: ReviewQuery["direction"]): number {
  if (missing(a) || missing(b)) return missing(a) === missing(b) ? 0 : missing(a) ? 1 : -1;
  const result = typeof a === "number" && typeof b === "number"
    ? a - b
    : searchable(a).localeCompare(searchable(b), "en", { numeric: true, sensitivity: "base" });
  return direction === "asc" ? result : -result;
}

export function queryReviewItems(
  items: readonly ReviewItem[],
  annotations: Readonly<Record<string, HumanAnnotations>>,
  query: ReviewQuery,
): ReviewItem[] {
  const needle = query.text.trim().toLowerCase();
  const found = items.filter((item) => {
    const human = annotations[item.id] ?? item.annotations;
    if (query.lens === "unreviewed" && human.status !== "unreviewed") return false;
    if (query.lens === "grouped" && !human.groupId) return false;
    const text = [item.id, item.source.filename, item.source.albumName, item.source.mimeType,
      ...Object.entries(item.source.fields ?? {}).flatMap(([key, value]) => [key, searchable(value)]),
      ...item.remoteReferences.flatMap((ref) => [ref.connector, ref.instanceId, ref.remoteAssetId, ref.sourceChecksum]),
      human.groupId, human.status, human.note, ...human.tags, ...(item.proposal?.tags ?? [])]
      .join(" ").toLowerCase();
    return text.includes(needle);
  });
  if (query.sort === "source-order") return found;
  const value = (item: ReviewItem): unknown => {
    if (query.sort === "filename") return item.source.filename;
    // Structured imports use a placeholder size; do not represent that as measured zero bytes.
    if (query.sort === "size") return item.source.sourceKind === "object" ? undefined : item.source.byteSize;
    return item.source.fields?.[query.sort.slice(6)];
  };
  return found.sort((a, b) => compare(value(a), value(b), query.direction));
}

export function selectedVisibleRows(items: readonly ReviewItem[], selected: ReadonlySet<string>): number[] {
  return items.flatMap((item, index) => selected.has(item.id) ? [index] : []);
}

/** Grid edits replace visible membership only. Hidden selections remain explicit in the tray. */
export function updateVisibleSelection(
  current: ReadonlySet<string>, visible: readonly ReviewItem[], rows: readonly number[],
): Set<string> {
  const visibleIds = new Set(visible.map((item) => item.id));
  const next = new Set([...current].filter((id) => !visibleIds.has(id)));
  for (const row of rows) if (Number.isInteger(row) && visible[row]) next.add(visible[row].id);
  return next;
}
