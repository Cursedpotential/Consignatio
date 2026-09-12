/** Case Bible Workbench · Byline: Codex · GPT-5 · 2026-08-30 */

import { describe, expect, it } from "vitest";
import { datasetToReviewItems, parseDataset } from "./dataset";

describe("dataset import", () => {
  it("bounds preview rows and fields", () => {
    expect(() => parseDataset("big.json", JSON.stringify(Array.from({ length: 2001 }, () => ({ id: 1 }))))).toThrow("2,000 rows");
    expect(() => parseDataset("wide.json", JSON.stringify([Object.fromEntries(Array.from({ length: 101 }, (_, i) => [String(i), i]))]))).toThrow("100 fields");
  });
  it("parses quoted CSV without losing commas or line breaks", () => {
    const dataset = parseDataset("objects.csv", 'id,note\n1,"hello, world"\n2,"two\nlines"', new Date("2026-08-30T12:00:00Z"));
    expect(dataset.rows).toEqual([{ id: "1", note: "hello, world" }, { id: "2", note: "two\nlines" }]);
    expect(dataset.columns.find((column) => column.key === "id")?.type).toBe("number");
  });

  it("accepts a wrapped JSON records array", () => {
    const dataset = parseDataset("objects.json", JSON.stringify({ records: [{ title: "Alpha", count: 3 }] }));
    expect(dataset.rows).toHaveLength(1);
    expect(dataset.columns.map((column) => column.key)).toEqual(["title", "count"]);
    expect(dataset.titleField).toBe("title");
    expect(dataset.visibleFields).toEqual(["title", "count"]);
  });

  it("creates immutable-source review records", () => {
    const dataset = parseDataset("objects.json", '[{"name":"Document A","category":"filing"}]');
    const [item] = datasetToReviewItems(dataset);
    expect(item.source.filename).toBe("Document A");
    expect(item.source.fields?.category).toBe("filing");
    expect(Object.isFrozen(item.source)).toBe(true);
  });

  it("uses the selected title mapping for review rows", () => {
    const dataset = parseDataset("objects.json", '[{"case_id":"FC-12","description":"Motion"}]');
    dataset.titleField = "case_id";
    expect(datasetToReviewItems(dataset)[0].source.filename).toBe("FC-12");
  });
});
