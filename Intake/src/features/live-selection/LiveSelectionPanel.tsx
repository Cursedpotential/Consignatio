/**
 * Byline: Claude Code · Sonnet 5 · 2026-09-14
 *
 * Docked panel showing the selection currently held by the Xplorer engine
 * (embedded alongside this app in the Consignatio Intake co-workspace shell).
 * This is the first working link between the two previously-independent
 * components: selecting files in Xplorer now visibly updates this panel.
 *
 * Honesty boundary: this app never reads file bytes for the shared selection.
 * It shows metadata only (name/path/type/size) per the shared result-presentation
 * contract's "chat context" rule (visible, bounded, five names then a remainder
 * count). Content preview is out of scope here -- open the file in Xplorer itself.
 *
 * 2026-09-14: each of the up-to-5 shown items is also looked up against the
 * Case Bible catalog (see use-catalog-lookup.ts) and its real occurrences are
 * rendered inline. An item with no catalog row gets one small flag; an item
 * with real rows gets no flag at all -- never a banner, per the "one flag, no
 * disclaimers" UI rule.
 */
import { useIntakeSelectionBridge } from "./use-intake-selection-bridge";
import { useCatalogLookup } from "./use-catalog-lookup";

const VISIBLE_NAMES = 5;

function formatOccurrenceSize(size: string | number): string {
  const n = typeof size === "string" ? Number(size) : size;
  return Number.isFinite(n) ? formatSize(n) : String(size);
}

function formatSize(size?: number): string {
  if (size === undefined) return "size unknown";
  if (size === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(
    Math.floor(Math.log(size) / Math.log(1024)),
    units.length - 1,
  );
  const value = size / 1024 ** exponent;
  return `${exponent === 0 ? size : value.toFixed(1)} ${units[exponent]}`;
}

export function LiveSelectionPanel() {
  const { connected, currentPath, count, selection } =
    useIntakeSelectionBridge();
  const shown = selection.slice(0, VISIBLE_NAMES);
  const remaining = count - shown.length;
  const catalog = useCatalogLookup(shown.map((item) => item.path));

  return (
    <section
      aria-label="Live selection from Explorer"
      style={{
        border: "1px solid var(--border)",
        borderRadius: 6,
        background: "var(--surface)",
        padding: 16,
        margin: "0 0 16px 0",
        fontFamily: "var(--font-ui, inherit)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
        }}
      >
        <h2
          style={{
            fontSize: 14,
            fontWeight: 600,
            margin: 0,
            color: "var(--ink)",
          }}
        >
          Live selection
        </h2>
        <span
          style={{
            fontSize: 12,
            color: connected ? "var(--success, var(--indigo))" : "var(--muted)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span
            aria-hidden="true"
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: connected
                ? "var(--success, #2f9d67)"
                : "var(--muted)",
              display: "inline-block",
            }}
          />
          {connected ? "Connected to Explorer" : "Waiting for Explorer"}
        </span>
      </header>

      {!connected && (
        <p style={{ fontSize: 13, color: "var(--muted)", margin: 0 }}>
          No selection has been received yet. This panel updates automatically
          once the Explorer engine (docked alongside it) reports a selection --
          unavailable, not empty, until then.
        </p>
      )}

      {connected && count === 0 && (
        <p style={{ fontSize: 13, color: "var(--muted)", margin: 0 }}>
          Nothing selected in Explorer
          {currentPath ? ` (browsing ${currentPath})` : ""}.
        </p>
      )}

      {connected && count > 0 && (
        <>
          <p
            style={{ fontSize: 13, color: "var(--muted)", margin: "0 0 8px 0" }}
          >
            {count} item{count === 1 ? "" : "s"} selected
            {currentPath ? ` in ${currentPath}` : ""}.
          </p>
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              display: "grid",
              gap: 4,
            }}
          >
            {shown.map((item) => {
              const lookup = catalog[item.path];
              const occurrences = lookup?.occurrences ?? [];
              const noMatch =
                item.file_type !== "directory" &&
                lookup !== undefined &&
                !lookup.error &&
                occurrences.length === 0;
              return (
                <li key={item.path} style={{ display: "grid", gap: 2 }}>
                  <div
                    style={{
                      fontSize: 13,
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 8,
                      color: "var(--ink)",
                    }}
                    title={item.path}
                  >
                    <span
                      style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {item.file_type === "directory" ? "\u{1F4C1}" : "\u{1F4C4}"}{" "}
                      {item.name}
                      {noMatch && (
                        <span
                          aria-hidden="true"
                          title="No catalog match for this file"
                          style={{ color: "var(--muted)", marginLeft: 4 }}
                        >
                          {"⚠"}
                        </span>
                      )}
                    </span>
                    <span
                      style={{
                        color: "var(--muted)",
                        flexShrink: 0,
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {item.file_type === "directory"
                        ? "dir"
                        : formatSize(item.size)}
                    </span>
                  </div>
                  {occurrences.length > 0 && (
                    <ul
                      style={{
                        listStyle: "none",
                        margin: "0 0 4px 20px",
                        padding: 0,
                        display: "grid",
                        gap: 2,
                      }}
                    >
                      {occurrences.map((occ, i) => (
                        <li
                          key={`${occ.source}:${occ.path}:${i}`}
                          style={{
                            fontSize: 11,
                            color: "var(--muted)",
                            display: "flex",
                            justifyContent: "space-between",
                            gap: 8,
                          }}
                          title={occ.path}
                        >
                          <span
                            style={{
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {occ.source}: {occ.path}
                          </span>
                          <span
                            style={{
                              flexShrink: 0,
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {formatOccurrenceSize(occ.size)}
                            {occ.md5 ? ` · ${occ.md5.slice(0, 8)}` : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
          {remaining > 0 && (
            <p
              style={{
                fontSize: 12,
                color: "var(--muted)",
                margin: "8px 0 0 0",
              }}
            >
              +{remaining} more (full manifest retained, not shown)
            </p>
          )}
          <p
            style={{ fontSize: 12, color: "var(--muted)", margin: "8px 0 0 0" }}
          >
            Metadata only -- names, paths, sizes. Content preview is unavailable
            here; open the item in Explorer to view it.
          </p>
        </>
      )}
    </section>
  );
}
