/**
 * Case Bible Workbench
 * Byline: Codex · GPT-5 · 2026-08-30
 */

import type { JobGateway, JobRequest, JobRun } from "./contracts";

const terminalCopies = new Set(["succeeded", "failed", "cancelled"]);

export class HttpJobGateway implements JobGateway {
  constructor(private readonly baseUrl: string) {}

  async start(request: JobRequest): Promise<JobRun> {
    return this.send("/jobs", {
      method: "POST",
      headers: { "Idempotency-Key": request.idempotencyKey },
      body: JSON.stringify(request),
    });
  }

  async get(runId: string): Promise<JobRun> {
    return this.send(`/jobs/${encodeURIComponent(runId)}`, { method: "GET" });
  }

  async cancel(runId: string): Promise<JobRun> {
    return this.send(`/jobs/${encodeURIComponent(runId)}/cancel`, { method: "POST" });
  }

  private async send(path: string, init: RequestInit): Promise<JobRun> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...init.headers },
    });
    if (!response.ok) throw new Error(`Backend returned ${response.status} ${response.statusText}.`);
    return response.json() as Promise<JobRun>;
  }
}

interface StoredDemoRun {
  run: JobRun;
  itemCount: number;
  polls: number;
  idempotencyKey: string;
}

export class DemoJobGateway implements JobGateway {
  private readonly runs = new Map<string, StoredDemoRun>();
  private sequence = 0;

  async start(request: JobRequest): Promise<JobRun> {
    const existing = [...this.runs.values()].find((entry) => entry.idempotencyKey === request.idempotencyKey);
    if (existing) return structuredClone(existing.run);

    this.sequence += 1;
    const id = `RUN-${String(this.sequence).padStart(6, "0")}`;
    const run: JobRun = {
      id,
      kind: request.kind,
      status: "queued",
      createdAt: request.requestedAt,
      updatedAt: request.requestedAt,
      progress: { completed: 0, total: request.recordIds.length, message: "Waiting for a backend worker" },
    };
    this.runs.set(id, { run, itemCount: request.recordIds.length, polls: 0, idempotencyKey: request.idempotencyKey });
    return this.publicRun(run);
  }

  async get(runId: string): Promise<JobRun> {
    const stored = this.requireRun(runId);
    if (terminalCopies.has(stored.run.status)) return this.publicRun(stored.run);

    stored.polls += 1;
    const now = new Date().toISOString();
    if (stored.polls === 1) {
      stored.run = {
        ...stored.run,
        status: "running",
        updatedAt: now,
        progress: { ...stored.run.progress, message: "Validating selected records" },
      };
    } else if (stored.polls < 4) {
      const completed = Math.max(1, Math.floor(stored.itemCount * (stored.polls - 1) / 3));
      stored.run = {
        ...stored.run,
        updatedAt: now,
        progress: { completed, total: stored.itemCount, message: "Preparing governed intake request" },
      };
    } else {
      stored.run = {
        ...stored.run,
        status: "succeeded",
        updatedAt: now,
        progress: { completed: stored.itemCount, total: stored.itemCount, message: "Intake request prepared" },
        receipt: {
          receiptId: `RCPT-${runId.slice(4)}`,
          resultReference: `workbench://intake/${runId}`,
          completedAt: now,
        },
      };
    }
    return this.publicRun(stored.run);
  }

  async cancel(runId: string): Promise<JobRun> {
    const stored = this.requireRun(runId);
    if (!terminalCopies.has(stored.run.status)) {
      const now = new Date().toISOString();
      stored.run = {
        ...stored.run,
        status: "cancelled",
        updatedAt: now,
        progress: { ...stored.run.progress, message: "Cancelled by reviewer" },
      };
    }
    return this.publicRun(stored.run);
  }

  private requireRun(runId: string): StoredDemoRun {
    const run = this.runs.get(runId);
    if (!run) throw new Error(`Unknown job run ${runId}.`);
    return run;
  }

  private publicRun(run: JobRun): JobRun {
    return structuredClone(run);
  }
}

export function createJobGateway(): JobGateway {
  const configuredUrl = import.meta.env.VITE_WORKBENCH_API_URL?.trim();
  return configuredUrl ? new HttpJobGateway(configuredUrl.replace(/\/$/, "")) : new DemoJobGateway();
}
