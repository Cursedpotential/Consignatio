/**
 * Case Bible Workbench
 * Byline: Codex · GPT-5 · 2026-08-30
 */

import { describe, expect, it } from "vitest";
import { createJobRequest, isTerminalJobStatus } from "./contracts";
import { DemoJobGateway } from "./gateway";

describe("job contracts", () => {
  it("creates stable, deduplicated record scope", () => {
    const request = createJobRequest("set-1", ["b", "a", "b"], new Date("2026-08-30T12:00:00Z"));
    expect(request.recordIds).toEqual(["a", "b"]);
    expect(request.idempotencyKey).toContain("set-1:a,b:");
  });

  it("rejects an empty job scope", () => {
    expect(() => createJobRequest("set-1", [])).toThrow("At least one record");
  });

  it("advances a demo job through a terminal receipt", async () => {
    const gateway = new DemoJobGateway();
    const request = createJobRequest("set-1", ["a", "b"], new Date("2026-08-30T12:00:00Z"));
    let run = await gateway.start(request);
    expect(run.status).toBe("queued");
    for (let poll = 0; poll < 4; poll += 1) run = await gateway.get(run.id);
    expect(run.status).toBe("succeeded");
    expect(run.receipt?.receiptId).toBe("RCPT-000001");
    expect(isTerminalJobStatus(run.status)).toBe(true);
  });

  it("returns the same run when the same idempotent request is retried", async () => {
    const gateway = new DemoJobGateway();
    const request = createJobRequest("set-1", ["a"], new Date("2026-08-30T12:00:00Z"));
    const first = await gateway.start(request);
    const retried = await gateway.start(request);
    expect(retried.id).toBe(first.id);
  });
});
