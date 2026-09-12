/**
 * Case Bible Workbench
 * Byline: Codex · GPT-5 · 2026-08-30
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import DataEditor, {
  CompactSelection,
  GridCellKind,
  type GridCell,
  type GridColumn,
  type GridSelection,
  type Item,
} from "@glideapps/glide-data-grid";
import { allocateNextGroupId, formatBytes } from "../../domain/groups";
import type { HumanAnnotations, ReviewItem } from "../../domain/types";
import { sampleReviewItems, sampleSnapshot } from "../../data/sampleReviewSet";
import { createJobRequest, isTerminalJobStatus, type JobRun } from "../../jobs/contracts";
import { createJobGateway } from "../../jobs/gateway";
import { JobRunPanel } from "../jobs/JobRunPanel";
import { queryReviewItems, selectedVisibleRows, updateVisibleSelection, type ReviewQuery } from "../../domain/reviewQuery";

type ViewMode = "grid" | "gallery";
type Lens = "all" | "unreviewed" | "grouped";

interface ReviewWorkbenchProps {
  initialItems?: ReviewItem[];
  initialMode?: ViewMode;
  reviewSetId?: string;
  reviewSetTitle?: string;
  sourceLabel?: string;
  visibleFieldKeys?: string[];
  onImportRequest?: () => void;
}

const photoColumns: GridColumn[] = [
  { title: "Preview", id: "preview", width: 92 },
  { title: "File", id: "filename", width: 190 },
  { title: "Captured", id: "captured", width: 168 },
  { title: "Group", id: "group", width: 108 },
  { title: "Tags", id: "tags", width: 190 },
  { title: "Review", id: "status", width: 118 },
  { title: "Size", id: "size", width: 92 },
  { title: "Source", id: "source", width: 104 },
];

function cloneAnnotations(items: ReviewItem[]): Record<string, HumanAnnotations> {
  return Object.fromEntries(items.map((item) => [item.id, { ...item.annotations, tags: [...item.annotations.tags] }]));
}

function buildRowSelection(indices: number[]): CompactSelection {
  return indices.reduce((selection, index) => selection.add(index), CompactSelection.empty());
}

export function ReviewWorkbench({
  initialItems = sampleReviewItems,
  initialMode = "grid",
  reviewSetId = sampleSnapshot.id,
  reviewSetTitle = sampleSnapshot.remoteAlbumName,
  sourceLabel = "Immich snapshot",
  visibleFieldKeys,
  onImportRequest,
}: ReviewWorkbenchProps) {
  const [mode, setMode] = useState<ViewMode>(initialMode);
  const [lens, setLens] = useState<Lens>("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<ReviewQuery["sort"]>("source-order");
  const [direction, setDirection] = useState<ReviewQuery["direction"]>("asc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [activeId, setActiveId] = useState(initialItems[0]?.id);
  const [annotations, setAnnotations] = useState(() => cloneAnnotations(initialItems));
  const [lastAction, setLastAction] = useState("No human decision recorded in this session.");
  const [jobGateway] = useState(createJobGateway);
  const [jobRuns, setJobRuns] = useState<JobRun[]>([]);
  const [jobsOpen, setJobsOpen] = useState(false);
  const [jobBusy, setJobBusy] = useState(false);
  const [jobError, setJobError] = useState<string>();

  const sourceFieldKeys = useMemo(
    () => visibleFieldKeys ?? [...new Set(initialItems.flatMap((item) => Object.keys(item.source.fields ?? {})))],
    [initialItems, visibleFieldKeys],
  );
  const columns = useMemo<GridColumn[]>(() => sourceFieldKeys.length
    ? [
        ...sourceFieldKeys.slice(0, 8).map((key) => ({ title: key, id: `field:${key}`, width: 150 })),
        { title: "Group", id: "group", width: 108 },
        { title: "Tags", id: "tags", width: 190 },
        { title: "Review", id: "status", width: 118 },
      ]
    : photoColumns, [sourceFieldKeys]);

  useEffect(() => {
    const activeIds = jobRuns.filter((run) => !isTerminalJobStatus(run.status)).map((run) => run.id);
    if (activeIds.length === 0) return;

    const timer = window.setInterval(() => {
      void Promise.all(activeIds.map((id) => jobGateway.get(id)))
        .then((updates) => {
          const byId = new Map(updates.map((run) => [run.id, run]));
          setJobRuns((current) => current.map((run) => byId.get(run.id) ?? run));
        })
        .catch((error: unknown) => setJobError(error instanceof Error ? error.message : "Could not refresh backend jobs."));
    }, 900);
    return () => window.clearInterval(timer);
  }, [jobGateway, jobRuns]);

  const visibleItems = useMemo(() => queryReviewItems(initialItems, annotations,
    { text: query, lens, sort, direction }), [annotations, initialItems, lens, query, sort, direction]);
  const gridSelection = useMemo<GridSelection>(() => ({
    columns: CompactSelection.empty(),
    rows: buildRowSelection(selectedVisibleRows(visibleItems, selectedIds)),
  }), [visibleItems, selectedIds]);

  const activeItem = initialItems.find((item) => item.id === activeId) ?? visibleItems[0];
  const activeAnnotation = activeItem ? annotations[activeItem.id] : undefined;
  const selectedVisibleCount = visibleItems.filter((item) => selectedIds.has(item.id)).length;

  const syncSelection = useCallback((ids: Set<string>) => {
    setSelectedIds(ids);
  }, []);

  const onGridSelectionChange = useCallback((selection: GridSelection) => {
    setSelectedIds((current) => updateVisibleSelection(current, visibleItems, selection.rows.toArray()));
  }, [visibleItems]);

  const getCellContent = useCallback(([column, row]: Item): GridCell => {
    const item = visibleItems[row];
    const annotation = annotations[item.id];
    const columnId = columns[column]?.id ?? "";
    if (columnId.startsWith("field:")) {
      const key = columnId.slice(6);
      const value = item.source.fields?.[key];
      const display = value === null || value === undefined || value === "" ? "—" : String(value);
      return { kind: GridCellKind.Text, data: display, displayData: display, allowOverlay: true, readonly: true };
    }
    switch (columnId) {
      case "preview":
        return {
          kind: GridCellKind.Image,
          data: [item.source.thumbnail],
          displayData: [item.source.thumbnail],
          allowOverlay: true,
          readonly: true,
        };
      case "filename":
        return { kind: GridCellKind.Text, data: item.source.filename, displayData: item.source.filename, allowOverlay: true, readonly: true };
      case "captured":
        return { kind: GridCellKind.Text, data: item.source.capturedAt, displayData: new Date(item.source.capturedAt).toLocaleString(), allowOverlay: true, readonly: true };
      case "group":
        return { kind: GridCellKind.Text, data: annotation.groupId ?? "", displayData: annotation.groupId ?? "—", allowOverlay: false, readonly: true };
      case "tags": {
        const tags = [...new Set([...(item.proposal?.tags ?? []), ...annotation.tags])];
        return { kind: GridCellKind.Bubble, data: tags, allowOverlay: true };
      }
      case "status":
        return { kind: GridCellKind.Text, data: annotation.status, displayData: annotation.status, allowOverlay: false, readonly: true };
      case "size":
        return { kind: GridCellKind.Text, data: String(item.source.byteSize), displayData: formatBytes(item.source.byteSize), allowOverlay: false, readonly: true };
      default:
        return { kind: GridCellKind.Text, data: item.remoteReferences[0]?.connector ?? "unknown", displayData: item.remoteReferences[0]?.connector ?? "unknown", allowOverlay: false, readonly: true };
    }
  }, [annotations, columns, visibleItems]);

  const createGroup = () => {
    if (selectedIds.size === 0) return;
    const nextId = allocateNextGroupId(Object.values(annotations).map((value) => value.groupId));
    setAnnotations((current) => Object.fromEntries(Object.entries(current).map(([id, value]) => [
      id,
      selectedIds.has(id) ? { ...value, groupId: nextId, status: "candidate" } : value,
    ])));
    setLastAction(`Created ${nextId} for ${selectedIds.size} selected item${selectedIds.size === 1 ? "" : "s"}.`);
  };

  const tagSelected = () => {
    if (selectedIds.size === 0) return;
    setAnnotations((current) => Object.fromEntries(Object.entries(current).map(([id, value]) => [
      id,
      selectedIds.has(id) ? { ...value, tags: [...new Set([...value.tags, "human-reviewed"])] } : value,
    ])));
    setLastAction(`Added “human-reviewed” to ${selectedIds.size} selected item${selectedIds.size === 1 ? "" : "s"}.`);
  };

  const prepareIntake = async () => {
    if (selectedIds.size === 0 || jobBusy) return;
    setJobBusy(true);
    setJobError(undefined);
    setJobsOpen(true);
    try {
      const request = createJobRequest(reviewSetId, selectedIds);
      const run = await jobGateway.start(request);
      setJobRuns((current) => [run, ...current.filter((item) => item.id !== run.id)]);
      setLastAction(`Started ${run.id} for ${request.recordIds.length} selected item${request.recordIds.length === 1 ? "" : "s"}.`);
    } catch (error) {
      setJobError(error instanceof Error ? error.message : "Could not start the backend job.");
    } finally {
      setJobBusy(false);
    }
  };

  const cancelJob = async (runId: string) => {
    setJobBusy(true);
    setJobError(undefined);
    try {
      const updated = await jobGateway.cancel(runId);
      setJobRuns((current) => current.map((run) => run.id === runId ? updated : run));
    } catch (error) {
      setJobError(error instanceof Error ? error.message : "Could not cancel the backend job.");
    } finally {
      setJobBusy(false);
    }
  };

  const toggleGalleryItem = (item: ReviewItem, additive: boolean) => {
    const next = additive ? new Set(selectedIds) : new Set<string>();
    if (next.has(item.id)) next.delete(item.id); else next.add(item.id);
    setActiveId(item.id);
    syncSelection(next);
  };

  return (
    <main className="workbench-shell">
      <header className="workbench-header">
        <div className="title-cluster">
          <span className="product-mark" aria-hidden="true">CB</span>
          <div>
            <p className="eyebrow">Intake · Consignatio</p>
            <h1>{reviewSetTitle}</h1>
          </div>
        </div>
        <div className="snapshot-facts" aria-label="Review set facts">
          <span><strong>{initialItems.length}</strong> items</span>
          <span>{sourceLabel}</span>
          <code>{sourceFieldKeys.length ? `${sourceFieldKeys.length} fields` : sampleSnapshot.membershipDigest}</code>
        </div>
        <div className="header-actions">
          {onImportRequest && <button className="header-import" onClick={onImportRequest}>Import file</button>}
          <div className="segmented-control" aria-label="View mode">
            <button className={mode === "grid" ? "active" : ""} onClick={() => setMode("grid")}>Grid</button>
            <button className={mode === "gallery" ? "active" : ""} onClick={() => setMode("gallery")}>Gallery</button>
          </div>
          <button className="primary-action" onClick={() => setJobsOpen(true)}>
            Jobs <span className="job-count">{jobRuns.filter((run) => !isTerminalJobStatus(run.status)).length}</span>
          </button>
        </div>
      </header>

      <section className="workbench-body">
        <aside className="lens-panel" aria-label="Review lenses">
          <label className="search-field">
            <span>Find in loaded metadata</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Path, hash, file, tag…" />
          </label>
          <p>Local metadata filter. Corpus and visual search are not connected yet.</p>
          <label className="search-field">
            <span>Sort by</span>
            <select value={sort} onChange={(event) => setSort(event.target.value as ReviewQuery["sort"])}>
              <option value="source-order">Original row order</option>
              <option value="filename">Filename / row title</option>
              <option value="size">Known source byte size</option>
              {sourceFieldKeys.map((field) => <option key={field} value={`field:${field}`}>{field} (imported)</option>)}
            </select>
          </label>
          <label className="search-field">
            <span>Order</span>
            <select value={direction} disabled={sort === "source-order"} onChange={(event) => setDirection(event.target.value as ReviewQuery["direction"])}>
              <option value="asc">Ascending</option><option value="desc">Descending</option>
            </select>
          </label>

          <nav className="lens-list" aria-label="Saved lenses">
            <p className="panel-label">Lenses</p>
            <button className={lens === "all" ? "selected" : ""} onClick={() => setLens("all")}><span>All items</span><b>{initialItems.length}</b></button>
            <button className={lens === "unreviewed" ? "selected" : ""} onClick={() => setLens("unreviewed")}><span>Unreviewed</span><b>{Object.values(annotations).filter((item) => item.status === "unreviewed").length}</b></button>
            <button className={lens === "grouped" ? "selected" : ""} onClick={() => setLens("grouped")}><span>Grouped</span><b>{Object.values(annotations).filter((item) => item.groupId).length}</b></button>
          </nav>

          <div className="group-index">
            <p className="panel-label">Human groups</p>
            {[...new Set(Object.values(annotations).flatMap((item) => item.groupId ?? []))].map((groupId) => (
              <button key={groupId}><span className="group-swatch" />{groupId}<b>{Object.values(annotations).filter((item) => item.groupId === groupId).length}</b></button>
            ))}
            <button><span className="group-swatch unresolved" />Ungrouped<b>{Object.values(annotations).filter((item) => !item.groupId).length}</b></button>
          </div>

          <div className="snapshot-note">
            <span>Frozen source</span>
            <p>{sourceFieldKeys.length ? "Imported values are locked for this review session." : `Album membership captured ${new Date(sampleSnapshot.capturedAt).toLocaleDateString()}.`}</p>
          </div>
        </aside>

        <section className="review-surface" aria-label={`${mode} review surface`}>
          <div className="surface-heading">
            <div>
              <p className="panel-label">Review set</p>
              <p>{visibleItems.length} visible · source values locked</p>
            </div>
            <span className="status-key"><i /> Proposal pending</span>
          </div>

          {mode === "grid" ? (
            <div className="grid-frame" data-testid="grid-frame">
              <DataEditor
                columns={columns}
                rows={visibleItems.length}
                getCellContent={getCellContent}
                gridSelection={gridSelection}
                onGridSelectionChange={onGridSelectionChange}
                onCellClicked={([, row]) => setActiveId(visibleItems[row]?.id)}
                rowMarkers="both"
                rowMarkerWidth={48}
                rowHeight={54}
                headerHeight={38}
                smoothScrollX
                smoothScrollY
                getCellsForSelection
                width="100%"
                height="100%"
              />
            </div>
          ) : (
            <div className="gallery-frame" data-testid="gallery-frame">
              {visibleItems.map((item) => {
                const selected = selectedIds.has(item.id);
                return (
                  <button
                    key={item.id}
                    className={`photo-card ${selected ? "selected" : ""}`}
                    onClick={(event) => toggleGalleryItem(item, event.ctrlKey || event.metaKey)}
                    aria-pressed={selected}
                  >
                    <img src={item.source.thumbnail} alt="" />
                    <span className="photo-check" aria-hidden="true">{selected ? "✓" : ""}</span>
                    <span className="photo-caption"><strong>{item.source.filename}</strong><small>{annotations[item.id].groupId ?? "Ungrouped"}</small></span>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <aside className="provenance-panel" aria-label="Decision record">
          <div className="provenance-heading">
            <p className="panel-label">Decision record</p>
            <code>{activeItem?.id ?? "No item"}</code>
          </div>
          {activeItem && activeAnnotation ? (
            <>
              <section className="provenance-layer source-layer">
                <span className="layer-marker">Source</span>
                <h2>{activeItem.source.filename}</h2>
                {activeItem.source.fields ? (
                  <dl className="source-fields">
                    {Object.entries(activeItem.source.fields).slice(0, 12).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value === null || value === "" ? "—" : String(value)}</dd></div>)}
                  </dl>
                ) : (
                  <dl>
                    <div><dt>Album</dt><dd>{activeItem.source.albumName}</dd></div>
                    <div><dt>Captured</dt><dd>{new Date(activeItem.source.capturedAt).toLocaleString()}</dd></div>
                    <div><dt>Dimensions</dt><dd>{activeItem.source.dimensions}</dd></div>
                    <div><dt>Remote ID</dt><dd><code>{activeItem.remoteReferences[0]?.remoteAssetId ?? "—"}</code></dd></div>
                  </dl>
                )}
              </section>
              <section className="provenance-layer proposal-layer">
                <span className="layer-marker">Proposal</span>
                <div className="confidence"><strong>{Math.round((activeItem.proposal?.confidence ?? 0) * 100)}%</strong><span>confidence</span></div>
                <p>{activeItem.proposal?.rationale}</p>
                <div className="tag-row">{activeItem.proposal?.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
                <small>{activeItem.proposal?.producer}</small>
              </section>
              <section className="provenance-layer human-layer">
                <span className="layer-marker">Human decision</span>
                <p className="decision-state">{activeAnnotation.status}</p>
                <dl>
                  <div><dt>Group</dt><dd>{activeAnnotation.groupId ?? "Not assigned"}</dd></div>
                  <div><dt>Tags</dt><dd>{activeAnnotation.tags.join(", ") || "None added"}</dd></div>
                </dl>
                <p className="action-receipt">{lastAction}</p>
              </section>
            </>
          ) : <p className="empty-state">Select a picture to inspect its decision record.</p>}
        </aside>
      </section>

      <footer className={`selection-ledger ${selectedIds.size > 0 ? "raised" : ""}`}>
        <div className="ledger-count">
          <strong>{selectedIds.size}</strong>
          <span>selected</span>
          <small>{selectedVisibleCount} visible · {selectedIds.size - selectedVisibleCount} hidden</small>
        </div>
        <p>{selectedIds.size ? "Apply a human decision to the exact selection." : "Select rows or pictures to open the review tray."}</p>
        <div className="ledger-actions">
          <button onClick={tagSelected} disabled={!selectedIds.size}>Add review tag</button>
          <button onClick={createGroup} disabled={!selectedIds.size}>Create group</button>
          <button className="prepare-job" onClick={() => void prepareIntake()} disabled={!selectedIds.size || jobBusy}>Prepare intake</button>
          <button onClick={() => syncSelection(new Set())} disabled={!selectedIds.size}>Clear</button>
        </div>
      </footer>
      <JobRunPanel
        runs={jobRuns}
        open={jobsOpen}
        busy={jobBusy}
        error={jobError}
        onClose={() => setJobsOpen(false)}
        onCancel={(runId) => void cancelJob(runId)}
      />
    </main>
  );
}
