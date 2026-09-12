/** Case Bible Workbench · Byline: Codex · GPT-5 · 2026-08-30 */

import type { ReviewItem } from "../../domain/types";

export type ImportedValue = string | number | boolean | null;
export type ImportedRow = Record<string, ImportedValue>;
export type InferredType = "text" | "number" | "boolean" | "date" | "mixed" | "empty";

export interface ImportedColumn {
  key: string;
  type: InferredType;
  populated: number;
  sample: string;
}

export interface ImportedDataset {
  id: string;
  filename: string;
  format: "csv" | "json";
  rows: ImportedRow[];
  columns: ImportedColumn[];
  importedAt: string;
  titleField?: string;
  visibleFields: string[];
}

function normalizeValue(value: unknown): ImportedValue {
  if (value === null || value === undefined) return null;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return value;
  return JSON.stringify(value);
}

function normalizeRows(input: unknown): ImportedRow[] {
  const candidate = Array.isArray(input)
    ? input
    : input && typeof input === "object"
      ? ["items", "records", "data", "objects"].map((key) => (input as Record<string, unknown>)[key]).find(Array.isArray)
      : undefined;
  if (!Array.isArray(candidate)) throw new Error("JSON must contain an array, or an items, records, data, or objects array.");
  if (candidate.length === 0) throw new Error("The file contains no rows.");
  return candidate.map((row, index) => {
    if (!row || typeof row !== "object" || Array.isArray(row)) return { value: normalizeValue(row), _row: index + 1 };
    return Object.fromEntries(Object.entries(row).map(([key, value]) => [key, normalizeValue(value)]));
  });
}

export function parseCsv(text: string): ImportedRow[] {
  const table: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (char === '"' && text[index + 1] === '"') { field += '"'; index += 1; }
      else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") { row.push(field); field = ""; }
    else if (char === "\n") { row.push(field.replace(/\r$/, "")); table.push(row); row = []; field = ""; }
    else field += char;
  }
  if (quoted) throw new Error("CSV contains an unterminated quoted field.");
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); table.push(row); }
  const nonEmpty = table.filter((cells) => cells.some((cell) => cell.trim() !== ""));
  if (nonEmpty.length < 2) throw new Error("CSV must contain a header and at least one data row.");
  const headers = nonEmpty[0].map((header, index) => header.trim() || `column_${index + 1}`);
  if (new Set(headers).size !== headers.length) throw new Error("CSV column names must be unique.");
  return nonEmpty.slice(1).map((cells) => Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? null])));
}

function inferValue(value: ImportedValue): Exclude<InferredType, "mixed" | "empty"> | "empty" {
  if (value === null || value === "") return "empty";
  if (typeof value === "number" || (typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value))) return "number";
  if (typeof value === "boolean" || value === "true" || value === "false") return "boolean";
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}(?:T|$)/.test(value) && !Number.isNaN(Date.parse(value))) return "date";
  return "text";
}

export function inferColumns(rows: ImportedRow[]): ImportedColumn[] {
  const keys = [...new Set(rows.flatMap(Object.keys))];
  return keys.map((key) => {
    const values = rows.map((row) => row[key] ?? null);
    const populated = values.filter((value) => value !== null && value !== "").length;
    const types = new Set(values.map(inferValue).filter((type) => type !== "empty"));
    const type: InferredType = types.size === 0 ? "empty" : types.size === 1 ? [...types][0] : "mixed";
    const first = values.find((value) => value !== null && value !== "");
    return { key, type, populated, sample: first === undefined ? "—" : String(first).slice(0, 80) };
  });
}

export function parseDataset(filename: string, text: string, now = new Date()): ImportedDataset {
  if (text.length > 5 * 1024 * 1024) throw new Error("Local preview is limited to 5 MiB.");
  const lower = filename.toLowerCase();
  const format = lower.endsWith(".json") ? "json" : lower.endsWith(".csv") ? "csv" : undefined;
  if (!format) throw new Error("Choose a .json or .csv file.");
  const rows = format === "json" ? normalizeRows(JSON.parse(text) as unknown) : parseCsv(text);
  if (rows.length > 2000) throw new Error("Local preview is limited to 2,000 rows. Use backend intake for larger datasets.");
  if (new Set(rows.flatMap(Object.keys)).size > 100) throw new Error("Local preview is limited to 100 fields.");
  const importedAt = now.toISOString();
  const columns = inferColumns(rows);
  const preferredTitles = ["title", "name", "filename", "file", "subject", "id"];
  const titleField = preferredTitles.find((key) => columns.some((column) => column.key === key)) ?? columns[0]?.key;
  return {
    id: `import-${importedAt}`,
    filename,
    format,
    rows,
    columns,
    importedAt,
    titleField,
    visibleFields: columns.slice(0, 8).map((column) => column.key),
  };
}

function documentThumbnail(label: string): string {
  const safe = label.replace(/[<>&]/g, "").slice(0, 28);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320"><rect width="480" height="320" fill="#EBE8E0"/><rect x="126" y="42" width="228" height="236" rx="4" fill="#FFFEFB" stroke="#B8B6B0"/><path d="M154 96h172M154 132h132M154 168h172M154 204h108" stroke="#687078" stroke-width="8"/><text x="24" y="300" fill="#1D2228" font-family="monospace" font-size="16">${safe}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export function datasetToReviewItems(dataset: ImportedDataset): ReviewItem[] {
  return dataset.rows.map((fields, index) => {
    const titleValue = dataset.titleField ? fields[dataset.titleField] : undefined;
    const title = titleValue === null || titleValue === undefined || titleValue === "" ? `Row ${index + 1}` : String(titleValue);
    return {
      id: `${dataset.id}-${String(index + 1).padStart(6, "0")}`,
      source: Object.freeze({
        filename: title,
        albumName: dataset.filename,
        capturedAt: dataset.importedAt,
        dimensions: "Structured record",
        byteSize: 0,
        mimeType: dataset.format === "json" ? "application/json" : "text/csv",
        thumbnail: documentThumbnail(title),
        atomicContainer: false,
        sourceKind: "object" as const,
        fields: Object.freeze({ ...fields }),
      }),
      annotations: { tags: [], status: "unreviewed" },
      remoteReferences: [{
        connector: "local-file" as const,
        instanceId: "local-import",
        remoteAssetId: `${dataset.filename}:${index + 1}`,
        remoteAlbumIds: [dataset.id],
      }],
    } satisfies ReviewItem;
  });
}
