import { describe, expect, it } from "vitest";
import type { ReviewItem } from "./types";
import { queryReviewItems, selectedVisibleRows, updateVisibleSelection, type ReviewQuery } from "./reviewQuery";

const item = (id: string, filename: string, size: number): ReviewItem => ({
  id, source: { filename, albumName: "Recovery", byteSize: size, capturedAt: "", dimensions: "",
    mimeType: "application/pdf", thumbnail: "", atomicContainer: false },
  annotations: { tags: [], status: "unreviewed" }, remoteReferences: [],
});
const a = item("a", "file10.pdf", 10);
const b = item("b", "file2.pdf", 2);
const base: ReviewQuery = { text: "", lens: "all", sort: "source-order", direction: "asc" };

describe("local investigation query", () => {
  it("searches human tags and notes without changing source", () => {
    const source = JSON.stringify(a);
    expect(queryReviewItems([a, b], { a: { tags: ["anchor"], note: "missing attachment", status: "candidate" } },
      { ...base, text: "ANCHOR" }).map((x) => x.id)).toEqual(["a"]);
    expect(JSON.stringify(a)).toBe(source);
  });
  it("finds imported hashes, paths and structured metadata", () => {
    const value = { ...a, source: { ...a.source, fields: { sha256: "abc123", original_path: "takeout/messages", details: { origin: "phone" } } } };
    for (const text of ["abc123", "takeout/messages", "phone"]) {
      expect(queryReviewItems([value], {}, { ...base, text })).toHaveLength(1);
    }
  });
  it("sorts naturally and does not mutate input order", () => {
    const input = [a, b];
    expect(queryReviewItems(input, {}, { ...base, sort: "filename" }).map((x) => x.id)).toEqual(["b", "a"]);
    expect(input.map((x) => x.id)).toEqual(["a", "b"]);
    expect(queryReviewItems(input, {}, { ...base, sort: "size", direction: "desc" }).map((x) => x.id)).toEqual(["a", "b"]);
  });
  it("sorts a selected imported field and puts missing values last", () => {
    const input = [a, { ...b, source: { ...b.source, fields: { bytes: 2 } } }];
    for (const direction of ["asc", "desc"] as const) {
      expect(queryReviewItems(input, {}, { ...base, sort: "field:bytes", direction }).map((x) => x.id)).toEqual(["b", "a"]);
    }
  });
  it("does not treat import placeholder sizes as actual zero-byte files", () => {
    const imported = { ...a, source: { ...a.source, sourceKind: "object" as const, byteSize: 0 } };
    expect(queryReviewItems([imported, b], {}, { ...base, sort: "size" }).map((x) => x.id)).toEqual(["b", "a"]);
  });
  it("uses overlays for grouped and unreviewed filters", () => {
    const annotations = { a: { tags: [], status: "candidate" as const, groupId: "unit-1" } };
    expect(queryReviewItems([a, b], annotations, { ...base, lens: "grouped" })).toEqual([a]);
    expect(queryReviewItems([a, b], annotations, { ...base, lens: "unreviewed" })).toEqual([b]);
  });
  it("keeps selected identity through sorting and preserves hidden selections", () => {
    expect(selectedVisibleRows([b, a], new Set(["a"]))).toEqual([1]);
    expect([...updateVisibleSelection(new Set(["a"]), [b], [0, 99])]).toEqual(["a", "b"]);
    expect([...updateVisibleSelection(new Set(["a", "b"]), [b], [])]).toEqual(["a"]);
  });
});
