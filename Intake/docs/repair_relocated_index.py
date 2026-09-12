"""One-time, owner-authorized path migration; retains existing Git blob identities."""
import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args, data=None):
    return subprocess.run(
        ['git', '-C', str(ROOT), *args], input=data, check=True, capture_output=True
    ).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() != ROOT:
        raise RuntimeError('Unexpected Git root')
    if git('diff', '--cached', '--name-only'):
        raise RuntimeError('Existing staged changes need review before migration')
    raw = git('ls-files', '--stage', '-z')
    moves, missing = [], []
    for record in raw.split(b'\0'):
        if not record:
            continue
        metadata, path_bytes = record.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        if stage != b'0':
            raise RuntimeError('Unmerged index entry')
        old = path_bytes.decode('utf-8')
        if (ROOT / old).exists():
            continue
        if old.startswith('workbench/'):
            new = 'Intake/' + old[len('workbench/'):]
        elif old.startswith('cocoindex-casebible/'):
            new = 'Intake/backend/' + old[len('cocoindex-casebible/'):]
        else:
            new = 'casebible/' + old
        if not (ROOT / new).exists():
            missing.append(old)
            continue
        moves.append((old, new, mode, oid))
    destinations = [row[1] for row in moves]
    if len(destinations) != len(set(destinations)):
        raise RuntimeError('Duplicate mapped destination')
    tracked = set(git('ls-files', '-z').split(b'\0'))
    if any(new.encode() in tracked for new in destinations):
        raise RuntimeError('Destination already tracked')
    counts = {}
    for old, new, mode, oid in moves:
        key = 'frontend' if old.startswith('workbench/') else 'backend' if old.startswith('cocoindex-casebible/') else 'original-casebible'
        counts[key] = counts.get(key, 0) + 1
    result = {'mode': 'apply' if args.apply else 'dry-run', 'root': str(ROOT), 'moves': counts, 'unmapped_count': len(missing), 'unmapped': missing}
    if args.apply:
        index = ROOT / '.git' / 'index'
        backup = index.with_name('index.before-intake-rename-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        shutil.copy2(index, backup)
        payload = b''
        for old, new, mode, oid in moves:
            payload += b'0 ' + b'0' * len(oid) + b'\t' + old.encode() + b'\0'
            payload += mode + b' ' + oid + b'\t' + new.encode() + b'\0'
        git('update-index', '-z', '--index-info', data=payload)
        result['index_backup'] = str(backup)
        result['blob_content_changed'] = False
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
