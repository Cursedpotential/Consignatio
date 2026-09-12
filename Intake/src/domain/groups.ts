const GROUP_PREFIX = "G-";

export function allocateNextGroupId(existing: Iterable<string | undefined>): string {
  let maximum = 0;
  for (const candidate of existing) {
    if (!candidate?.startsWith(GROUP_PREFIX)) continue;
    const value = Number.parseInt(candidate.slice(GROUP_PREFIX.length), 10);
    if (Number.isFinite(value)) maximum = Math.max(maximum, value);
  }
  return `${GROUP_PREFIX}${String(maximum + 1).padStart(6, "0")}`;
}

export function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let amount = value;
  let unit = -1;
  do {
    amount /= 1024;
    unit += 1;
  } while (amount >= 1024 && unit < units.length - 1);
  return `${amount.toFixed(amount >= 10 ? 1 : 2)} ${units[unit]}`;
}

