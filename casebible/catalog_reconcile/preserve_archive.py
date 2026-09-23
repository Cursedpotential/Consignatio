"""Byline: Codex | 2026-09-20. Verify and register the authorized B2 archive."""
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from io_utils import B2, Postgres, sha256_file

OUT = Path('docs/receipts/source-recovery-2026-09-20/native-platform-archive-01')
PREFIX = 'consignatio/reconciliation/2026-09-20/platform-preservation-01/'
RCLONE = 'C:/Users/matts/scoop/apps/rclone/current/rclone.exe'
B = B2(r'C:\Users\matts\scoop\apps\rclone\current\rclone.conf')

def verify(path, key):
    before = B.call('b2_list_file_names', {'bucketId': B.bucket['bucketId'], 'prefix': key, 'maxFileCount': 1})['files'][0]
    assert before['fileName'] == key
    code = '''import subprocess,hashlib,json
p=subprocess.Popen(['rclone','cat',TARGET],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
h=hashlib.sha256(); n=0
while True:
 b=p.stdout.read(8388608)
 if not b: break
 h.update(b); n+=len(b)
e=p.stderr.read(); assert p.wait()==0, 'Remote read failed'
print(json.dumps({'sha256':h.hexdigest(),'bytes':n}))
'''.replace('TARGET', repr('b2native-full:salem-data/' + key))
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', 'ovh-files-ts', 'sudo -n python3 -c ' + shlex.quote(code)], capture_output=True, timeout=1200)
    assert result.returncode == 0, 'Remote archive verification failed'
    measured = json.loads(result.stdout)
    assert measured == {'sha256': sha256_file(path), 'bytes': path.stat().st_size}
    after = B.call('b2_list_file_names', {'bucketId': B.bucket['bucketId'], 'prefix': key, 'maxFileCount': 1})['files'][0]
    assert before == after, 'B2 metadata changed during readback'
    return {'key': key, 'sha256': measured['sha256'], 'bytes': measured['bytes'], 'provider_metadata': after, 'full_remote_readback_verified': True}

def upload(path):
    key = PREFIX + path.name
    subprocess.run([RCLONE, 'copyto', str(path), 'b2:salem-data/' + key, '--immutable'], check=True, capture_output=True)
    return verify(path, key)

objects = []
for name in ('analysis-artifacts.tar.gz', 'artifact-inventory.json', 'archive-verified.json'):
    objects.append(verify(OUT / name, PREFIX + name))
    print('Verified ' + name, flush=True)
objects.append(upload(Path(__file__)))
receipt = {'byline': 'Codex | 2026-09-20', 'archive_id': 'platform-preservation-20260920-01', 'verified_at': datetime.now(timezone.utc).isoformat(), 'bucket': 'salem-data', 'objects': objects, 'archive_validation': json.loads((OUT / 'archive-verified.json').read_text()), 'docstore_status': 'registration_pending_connector_unavailable', 'r2_retirement_status': 'not_cleared_whole_source_review_outstanding', 'scope': 'Generated analysis, platform exports and source occurrence metadata; unchanged binary mirrors referenced separately.'}
receipt_path = OUT / 'b2-preserved.json'
with receipt_path.open('x', encoding='utf-8') as f:
    json.dump(receipt, f, indent=2, ensure_ascii=False)
receipt_object = upload(receipt_path)
payload = json.dumps(receipt, ensure_ascii=False).replace("'", "''")
sql = "BEGIN; CREATE TABLE IF NOT EXISTS raw_duck.analysis_preservation_20260920 (archive_id text PRIMARY KEY, payload jsonb NOT NULL); INSERT INTO raw_duck.analysis_preservation_20260920 VALUES ('platform-preservation-20260920-01', '" + payload + "'::jsonb); COMMIT;"
p = subprocess.run(Postgres().command(writable=True), input=sql.encode(), capture_output=True)
assert p.returncode == 0, 'Archive database registration failed'
rows = list(Postgres().rows("SELECT payload FROM raw_duck.analysis_preservation_20260920 WHERE archive_id='platform-preservation-20260920-01'"))
assert rows == [{'payload': receipt}], 'Database readback mismatch'
completion = {'byline': 'Codex | 2026-09-20', 'receipt_object': receipt_object, 'postgres_readback_equal': True}
with (OUT / 'publication-verified.json').open('x', encoding='utf-8') as f:
    json.dump(completion, f, indent=2)
upload(OUT / 'publication-verified.json')
print(json.dumps({'archive_bytes': objects[0]['bytes'], 'archive_sha256': objects[0]['sha256'], 'postgres_readback_equal': True, 'receipt_preserved_and_verified': True}), flush=True)
