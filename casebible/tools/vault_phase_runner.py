# Byline: Claude Code · Opus 5 · 2026-09-16 07:42 EDT (session propria-79)
"""Hard-delete a checked key list on B2 in small folder phases: delete one folder chunk → check → next.

Owner 2026-09-16 07:34/07:38: "doing these things in phases … in chunks rather than two million item[s]" ·
"Check. Remove next folder. Check. Remove next folder. Small bits. Easy to reverse, easy to fix, easy to check."

A phase = one folder prefix with <= --cap listed keys (large folders split into subfolders; files sitting directly in a
split folder form their own phases with --max-depth 1). For each phase:
  1. rclone delete b2:<bucket>/<base><prefix> --files-from-raw <phase keys> --b2-hard-delete
  2. fresh rclone lsf of the same prefix (same depth)
  3. PASS only if none of the phase keys is still listed; otherwise STOP (exit 2)
Every phase result is appended to <workdir>/phases.jsonl; a rerun skips phases already recorded PASS.
Run ON ovh-files with the B2 credentials in the environment (systemd EnvironmentFile).

  vault_phase_runner.py --list intake_delete.list --base consignatio/intake/raw-dedupe/v1/source-buckets/ --workdir phases-intake
"""
import argparse
import json
import os
import subprocess
import sys
import time


def build_phases(rel_keys, cap):
    phases = []

    def split(prefix, keys):
        if len(keys) <= cap:
            phases.append((prefix, None, sorted(keys)))
            return
        loose, children = [], {}
        for k in keys:
            head, sep, rest = k.partition("/")
            if sep:
                children.setdefault(head, []).append(rest)
            else:
                loose.append(k)
        loose.sort()
        for i in range(0, len(loose), cap):
            phases.append((prefix, 1, loose[i:i + cap]))
        for head in sorted(children):
            sub = children[head]
            split(prefix + head + "/", sub)

    split("", list(rel_keys))
    return phases


def rclone(args, conf):
    return subprocess.run(["/usr/bin/rclone", *args, "--config", conf], capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", required=True)
    ap.add_argument("--base", required=True, help="bucket-relative prefix every key starts with")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--bucket", default="salem-data")
    ap.add_argument("--remote", default="b2")
    ap.add_argument("--config", default="/opt/casebible/rclone.conf")
    ap.add_argument("--cap", type=int, default=20000)
    ap.add_argument("--only-plan", action="store_true")
    ap.add_argument("--catalog", default="", help="CSV key,size,sha1 of the proven objects (for extra stored versions)")
    a = ap.parse_args()
    catalog = {}
    if a.catalog:
        import csv
        with open(a.catalog, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                catalog[row["key"]] = (int(row["size"]), row["sha1"])

    os.makedirs(a.workdir, exist_ok=True)
    with open(a.list, encoding="utf-8") as fh:
        keys = [line.rstrip("\n") for line in fh if line.strip()]
    bad = [k for k in keys if not k.startswith(a.base)]
    if bad:
        sys.exit(f"ABORT: {len(bad)} keys outside base {a.base}, e.g. {bad[0]}")
    phases = build_phases([k[len(a.base):] for k in keys], a.cap)
    print(f"{len(keys):,} keys → {len(phases):,} phases (cap {a.cap:,})", flush=True)
    if a.only_plan:
        for prefix, depth, pk in phases:
            print(f"  {len(pk):>6,}  {prefix or '(root)'}{'  [files directly in this folder]' if depth else ''}")
        return 0

    log_path = os.path.join(a.workdir, "phases.jsonl")
    done = set()
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("status") == "PASS":
                    done.add((r["prefix"], r["max_depth"], r["first_key"]))

    for n, (prefix, depth, pk) in enumerate(phases, 1):
        ident = (prefix, depth, pk[0])
        if ident in done:
            continue
        remote = f"{a.remote}:{a.bucket}/{a.base}{prefix}"
        # pk is already relative to prefix (build_phases strips it). 2026-09-16 bug: stripping it a second time sent
        # blank / cut-off names to rclone and to the check, which then "passed" without deleting (0 wrong deletes,
        # verified by a full before/after intake listing).
        rel = list(pk)
        if any(not k or k.startswith("/") for k in rel):
            print(f"STOPPED: phase {n} has an empty or absolute key", flush=True)
            return 2
        phase_list = os.path.join(a.workdir, f"phase-{n:05d}.list")
        with open(phase_list, "w", encoding="utf-8") as fh:
            fh.writelines(k + "\n" for k in rel)
        depth_args = ["--max-depth", str(depth)] if depth else []
        lsf_args = ["lsf", remote, "--files-only", "--fast-list", *(depth_args or ["-R"])]
        started = time.time()
        pre = rclone(["lsjson", remote, "--files-only", "--no-mimetype", "--hash", "--hash-type", "sha1",
                      "--fast-list", *(depth_args or ["-R"])], a.config)
        if pre.returncode != 0:
            print(f"STOPPED: listing before phase {n} failed: {pre.stderr[-500:]}", flush=True)
            return 2
        pre_items = {i["Path"]: i for i in json.loads(pre.stdout or "[]")}
        before = set(pre_items)
        differ = set()  # keys whose visible stored version is NOT the proven content (kept, recorded)
        if catalog:
            for k in rel:
                item = pre_items.get(k)
                want = catalog.get(a.base + prefix + k)
                if item is None or want is None:
                    continue
                got_sha = ((item.get("Hashes") or {}).get("sha1", ""))
                if int(item["Size"]) != want[0] or (want[1] and got_sha and got_sha != want[1]):
                    differ.add(k)
            if differ:
                with open(os.path.join(a.workdir, "versions_differ.tsv"), "a", encoding="utf-8") as fh:
                    for k in sorted(differ):
                        item = pre_items[k]
                        fh.write(f"{a.base}{prefix}{k}\t{item['Size']}\t"
                                 f"{((item.get('Hashes') or {}).get('sha1', ''))}\tphase {n} (before delete)\n")
                print(f"phase {n}: {len(differ)} key(s) show content that differs from the proven copy — kept, "
                      f"recorded in versions_differ.tsv: {sorted(differ)[:5]}", flush=True)
        targets = [k for k in rel if k in before and k not in differ]
        already_gone = sum(1 for k in rel if k not in before)
        if not targets:
            d_rc, post_listed = 0, before
        else:
            target_list = phase_list + ".present"
            with open(target_list, "w", encoding="utf-8") as fh:
                fh.writelines(k + "\n" for k in targets)
            d = rclone(["delete", remote, "--files-from-raw", target_list, "--b2-hard-delete", "--fast-list",
                        "--checkers", "32", "--transfers", "32", "--retries", "3", "--low-level-retries", "10",
                        *depth_args], a.config)
            d_rc = d.returncode
            post = rclone(lsf_args, a.config)
            post_listed = set(post.stdout.splitlines()) if post.returncode == 0 else None
            # 2026-09-16: some keys hold several stored versions of the SAME bytes (upload retries); a hard delete
            # removes the newest and the next one becomes visible. Delete again only while every remaining version
            # matches the catalog size + sha1 of the proven object; any difference stops the run.
            rounds = 0
            while d_rc == 0 and post_listed is not None and rounds < 5:
                again = sorted((set(targets) & post_listed) - differ)
                if not again:
                    break
                rounds += 1
                lj = rclone(["lsjson", remote, "--files-only", "--no-mimetype", "--hash", "--hash-type", "sha1",
                             "--fast-list", *(depth_args or ["-R"])], a.config)
                if lj.returncode != 0:
                    break
                seen = {i["Path"]: i for i in json.loads(lj.stdout or "[]")}
                mismatch = []
                for k in again:
                    item = seen.get(k)
                    want = catalog.get(a.base + prefix + k)
                    got_sha = ((item or {}).get("Hashes") or {}).get("sha1", "")
                    if (item is None or want is None or int(item["Size"]) != want[0]
                            or (want[1] and got_sha and got_sha != want[1])):
                        mismatch.append(k)
                if mismatch:
                    # an older stored version is DIFFERENT content: never delete it; it stays in intake and is recorded
                    # for the move step (it is not in the vault). Found 2026-09-16 in gdrive/salemnet/.
                    with open(os.path.join(a.workdir, "versions_differ.tsv"), "a", encoding="utf-8") as fh:
                        for k in mismatch:
                            item = seen.get(k) or {}
                            fh.write(f"{a.base}{prefix}{k}\t{item.get('Size', '')}\t"
                                     f"{((item.get('Hashes') or {}).get('sha1', ''))}\tphase {n}\n")
                    differ.update(mismatch)
                    print(f"phase {n}: {len(mismatch)} key(s) have an older DIFFERENT version — kept in intake, "
                          f"recorded in versions_differ.tsv: {mismatch[:5]}", flush=True)
                    again = [k for k in again if k not in set(mismatch)]
                    if not again:
                        break
                with open(target_list + ".again", "w", encoding="utf-8") as fh:
                    fh.writelines(k + "\n" for k in again)
                d = rclone(["delete", remote, "--files-from-raw", target_list + ".again", "--b2-hard-delete",
                            "--fast-list", "--checkers", "32", "--transfers", "32", "--retries", "3",
                            "--low-level-retries", "10", *depth_args], a.config)
                d_rc = d.returncode
                post = rclone(lsf_args, a.config)
                post_listed = set(post.stdout.splitlines()) if post.returncode == 0 else None
        still = None if post_listed is None else sorted((set(targets) & post_listed) - differ)
        other_gone = None if post_listed is None else sorted((before - set(targets)) - post_listed)
        removed = None if post_listed is None else len(before) - len(post_listed)
        ok = (d_rc == 0 and post_listed is not None and not still and not other_gone
              and removed == len(targets) - len(differ & set(targets) & post_listed))
        status = "PASS" if ok else "FAIL"
        rec = {"phase": n, "of": len(phases), "prefix": prefix, "max_depth": depth, "first_key": pk[0],
               "on_list": len(rel), "present_before": len(targets), "already_gone": already_gone,
               "kept_differs": len(differ),
               "removed": removed, "still_present": None if still is None else len(still),
               "other_files_gone": None if other_gone is None else len(other_gone),
               "left_in_folder": None if post_listed is None else len(post_listed),
               "seconds": round(time.time() - started, 1), "rclone_delete_rc": d_rc, "status": status,
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"[{n}/{len(phases)}] {status} {prefix or '(root)'}{' (loose files)' if depth else ''}: "
              f"removed {removed} of {len(targets)} present ({already_gone} already gone), still there "
              f"{rec['still_present']}, other files gone {rec['other_files_gone']}, left in folder "
              f"{rec['left_in_folder']}, {rec['seconds']}s", flush=True)
        if status != "PASS":
            print("STOPPED: check failed", still[:10] if still else "", other_gone[:10] if other_gone else "", flush=True)
            return 2
    print("ALL PHASES PASS", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
