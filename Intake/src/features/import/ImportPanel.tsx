/** Case Bible Workbench · Byline: Codex · GPT-5 · 2026-08-30 */

import { useRef, useState } from "react";
import { parseDataset, type ImportedDataset } from "./dataset";

interface ImportPanelProps {
  open: boolean;
  onClose: () => void;
  onLoad: (dataset: ImportedDataset) => void;
}

export function ImportPanel({ open, onClose, onLoad }: ImportPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dataset, setDataset] = useState<ImportedDataset>();
  const [error, setError] = useState<string>();
  const [reading, setReading] = useState(false);

  const chooseFile = async (file?: File) => {
    if (!file) return;
    setReading(true);
    setError(undefined);
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error("Local preview is limited to 5 MiB. Use bounded backend intake for larger files.");
      setDataset(parseDataset(file.name, await file.text()));
    } catch (reason) {
      setDataset(undefined);
      setError(reason instanceof Error ? reason.message : "The file could not be read.");
    } finally {
      setReading(false);
    }
  };

  const load = () => {
    if (!dataset) return;
    onLoad(dataset);
    onClose();
  };

  const setTitleField = (titleField: string) => {
    setDataset((current) => current ? { ...current, titleField } : current);
  };

  const toggleVisibleField = (key: string) => {
    setDataset((current) => {
      if (!current) return current;
      const selected = current.visibleFields.includes(key);
      if (selected && current.visibleFields.length === 1) return current;
      return {
        ...current,
        visibleFields: selected ? current.visibleFields.filter((field) => field !== key) : [...current.visibleFields, key],
      };
    });
  };

  return (
    <aside className={`import-panel ${open ? "open" : ""}`} aria-label="Import JSON or CSV" aria-hidden={!open}>
      <header>
        <div><p className="panel-label">Local dataset</p><h2>Import JSON or CSV</h2></div>
        <button className="quiet-button" onClick={onClose}>Close</button>
      </header>

      <section className="import-source">
        <input
          ref={inputRef}
          type="file"
          accept=".json,.csv,application/json,text/csv"
          onChange={(event) => void chooseFile(event.target.files?.[0])}
        />
        <button className="file-picker" onClick={() => inputRef.current?.click()} disabled={reading}>
          {reading ? "Reading file…" : dataset ? "Choose another file" : "Choose JSON or CSV"}
        </button>
        <p>The original file is read locally and remains unchanged.</p>
      </section>

      {error && <p className="import-error" role="alert">{error}</p>}
      {dataset && (
        <>
          <section className="import-facts">
            <div><span>File</span><strong>{dataset.filename}</strong></div>
            <div><span>Rows</span><strong>{dataset.rows.length.toLocaleString()}</strong></div>
            <div><span>Fields</span><strong>{dataset.columns.length}</strong></div>
            <div><span>Format</span><strong>{dataset.format.toUpperCase()}</strong></div>
          </section>
          <section className="schema-tape" aria-label="Detected fields">
            <div className="schema-heading"><p className="panel-label">Detected fields</p><span>Review before loading</span></div>
            <label className="title-field-map">
              <span>Row title</span>
              <select value={dataset.titleField} onChange={(event) => setTitleField(event.target.value)}>
                {dataset.columns.map((column) => <option value={column.key} key={column.key}>{column.key}</option>)}
              </select>
              <small>This field identifies each row in the review tray and inspector.</small>
            </label>
            <div className="schema-table">
              <div className="schema-row schema-header"><span>Show</span><span>Field</span><span>Type</span><span>Filled</span><span>Sample</span></div>
              {dataset.columns.map((column) => (
                <div className="schema-row" key={column.key}>
                  <label className="field-visibility" title={`Show ${column.key} in the grid`}>
                    <input
                      type="checkbox"
                      checked={dataset.visibleFields.includes(column.key)}
                      onChange={() => toggleVisibleField(column.key)}
                      disabled={dataset.visibleFields.length === 1 && dataset.visibleFields.includes(column.key)}
                    />
                  </label>
                  <code>{column.key}</code><span>{column.type}</span><span>{column.populated}/{dataset.rows.length}</span><span title={column.sample}>{column.sample}</span>
                </div>
              ))}
            </div>
          </section>
          <footer className="import-actions">
            <p>{dataset.visibleFields.length} grid fields selected. All source fields remain available in the inspector.</p>
            <button className="primary-action" onClick={load}>Load {dataset.rows.length.toLocaleString()} rows</button>
          </footer>
        </>
      )}
    </aside>
  );
}
