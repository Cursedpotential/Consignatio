/**
 * Case Bible Workbench
 * Byline: Codex · GPT-5 · 2026-08-30
 */

export type JobKind = "prepare-intake";
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export interface JobProgress {
  completed: number;
  total: number;
  message: string;
}

export interface JobRequest {
  kind: JobKind;
  reviewSetId: string;
  recordIds: string[];
  idempotencyKey: string;
  requestedAt: string;
}

export interface JobReceipt {
  receiptId: string;
  resultReference: string;
  completedAt: string;
}

export interface JobRun {
  id: string;
  kind: JobKind;
  status: JobStatus;
  createdAt: string;
  updatedAt: string;
  progress: JobProgress;
  receipt?: JobReceipt;
  error?: string;
}

export interface JobGateway {
  start(request: JobRequest): Promise<JobRun>;
  get(runId: string): Promise<JobRun>;
  cancel(runId: string): Promise<JobRun>;
}

export function isTerminalJobStatus(status: JobStatus): boolean {
  return status === "succeeded" || status === "failed" || status === "cancelled";
}

export function createJobRequest(
  reviewSetId: string,
  recordIds: Iterable<string>,
  now = new Date(),
): JobRequest {
  const stableIds = [...new Set(recordIds)].sort();
  if (stableIds.length === 0) throw new Error("At least one record must be selected.");

  const requestedAt = now.toISOString();
  return {
    kind: "prepare-intake",
    reviewSetId,
    recordIds: stableIds,
    requestedAt,
    idempotencyKey: `${reviewSetId}:${stableIds.join(",")}:${requestedAt}`,
  };
}
