"""Byline: Codex | 2026-09-20. Recover existing SHA-256 receipts and occurrence metadata."""
import argparse
import collections
import gzip
import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path

from io_utils import Postgres,records,sha256_file,write_records
from run import save_json,emit


def capture(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    directory='/data/consignatio/migrations/r2-to-b2/hash-ledger-partitions'
    proc=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','ovh-files-ts',
                           'sudo -n tar -C '+directory+' -cf - .'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    actual={};expected={};counter=collections.Counter();algorithms=collections.Counter()
    def rows():
        with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:
            for member in archive:
                if member.isdir():continue
                name=member.name.removeprefix('./')
                if not re.fullmatch(r'[0-9a-f]{2}\.ndjson\.gz(?:\.sha256|\.receipt)?',name):raise ValueError('Unexpected metadata archive member')
                data=archive.extractfile(member).read()
                if name.endswith('.sha256'):
                    declared=data.decode('utf-8').split()[0]
                    if not re.fullmatch('[0-9a-f]{64}',declared):raise ValueError('Invalid receipt fingerprint')
                    expected[name.removesuffix('.sha256')]=declared
                elif name.endswith('.ndjson.gz'):
                    actual[name]=hashlib.sha256(data).hexdigest()
                    for line in gzip.decompress(data).splitlines():
                        row=json.loads(line);counter[row.get('sourceBucket')]+=1;algorithms[row.get('algorithm')]+=1
                        yield {'ledger_partition':name,'ledger_partition_sha256':actual[name],'receipt':row}
        error=proc.stderr.read().decode('utf-8',errors='replace')
        if proc.wait(timeout=30):raise RuntimeError('Ledger metadata transfer failed: '+error[:200])
    count=write_records(root/'hash-ledger.parquet',rows())
    if len(actual)!=256 or actual!=expected:raise ValueError('Ledger partition fingerprints differ; not validated')
    save_json(root/'capture.json',{'source_directory':directory,'records':count,'verified_partitions':len(actual),
              'source_buckets':dict(counter),'algorithms':dict(algorithms),'partition_sha256':actual,
              'artifact_sha256':sha256_file(root/'hash-ledger.parquet'),'claim_status':'historical_receipt_not_new_source_hash',
              'content_downloads':0,'source_mutations':0})
    emit('ledger_metadata_recovered',records=count,verified_partitions=len(actual),source_buckets=dict(counter))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);capture(p.parse_args().output)
