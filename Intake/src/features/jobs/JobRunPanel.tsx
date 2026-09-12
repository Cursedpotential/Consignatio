/**
 * Case Bible Workbench
 * Byline: Codex · GPT-5 · 2026-08-30
 */

import type { JobRun } from "../../jobs/contracts";

interface JobRunPanelProps {
  runs: JobRun[];
  open: boolean;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onCancel: (runId: string) => void;
}

function displayKind(kind: JobRun["kind"]): string {
  return kind === "prepare-intake" ? "Prepare intake" : kind;
}

export function JobRunPanel({ runs, open, busy, error, onClose, onCancel }: JobRunPanelProps) {
  return (
    <aside className={`job-panel ${open ? "open" : ""}`} aria-label="Backend jobs" aria-hidden={!open}>
      <header>
        <div>
          <p className="panel-label">Backend activity</p>
          <h2>Job runs</h2>
        </div>
        <button className="quiet-button" onClick={onClose} aria-label="Close backend jobs">Close</button>
      </header>

      {error && <p className="job-error" role="alert">{error}</p>}
      {runs.length === 0 ? (
        <div className="job-empty">
          <strong>No jobs started</strong>
          <p>Select records in the review tray, then choose Prepare intake.</p>
        </div>
      ) : (
        <ol className="job-list">
          {runs.map((run) => {
            const percent = run.progress.total === 0 ? 0 : Math.round(run.progress.completed / run.progress.total * 100);
            const active = run.status === "queued" || run.status === "running";
            return (
              <li key={run.id} className={`job-run status-${run.status}`}>
                <div className="job-run-heading">
                  <div><strong>{displayKind(run.kind)}</strong><code>{run.id}</code></div>
                  <span className="job-status">{run.status}</span>
                </div>
                <p>{run.progress.message}</p>
                <div className="job-progress" aria-label={`${percent}% complete`}>
                  <i style={{ width: `${percent}%` }} />
                </div>
                <div className="job-run-footer">
                  <span>{run.progress.completed} / {run.progress.total} records</span>
                  {active && <button onClick={() => onCancel(run.id)} disabled={busy}>Cancel</button>}
                  {run.receipt && <code>{run.receipt.receiptId}</code>}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </aside>
  );
}
