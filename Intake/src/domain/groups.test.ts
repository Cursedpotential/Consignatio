import { describe, expect, it } from "vitest";
import { allocateNextGroupId, formatBytes } from "./groups";

describe("allocateNextGroupId", () => {
  it("starts at a stable padded identifier", () => {
    expect(allocateNextGroupId([])).toBe("G-000001");
  });

  it("never reuses a lower or malformed identifier", () => {
    expect(allocateNextGroupId(["G-000004", undefined, "proposal-7", "G-000012"]))
      .toBe("G-000013");
  });
});

describe("formatBytes", () => {
  it("formats review metadata without mutating the numeric value", () => {
    expect(formatBytes(5_242_880)).toBe("5.00 MB");
  });
});

