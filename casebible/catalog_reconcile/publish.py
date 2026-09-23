"""Byline: Codex | 2026-09-20. Publish validated generations to dated PG tables."""
import argparse
import csv
import io
import gzip
import json
import shlex
import subprocess
import uuid
from pathlib import Path

from core import stable_id
from io_utils import Postgres, records, sha256_file
from run import save_json, emit


def publish(root, apply=False):
    root=Path(root)
    manifest=json.loads((root/"validated.json").read_text(encoding="utf-8"))
    if str(uuid.UUID(manifest['generation_id']))!=manifest['generation_id']:
        raise ValueError('Invalid generation identity')
    if manifest["status"]!="validated_metadata_reconciliation" or not all(manifest["checks"].values()):
        raise ValueError("Unvalidated generation")
    for name,expected in manifest["files"].items():
        if sha256_file(root/name)!=expected: raise ValueError("Fingerprint mismatch: "+name)
    manifest['capture']=json.loads((root/'capture.json').read_text(encoding='utf-8'))
    manifest['byline']='Codex | 2026-09-20'
    if not apply:
        emit("publication_plan",generation_id=manifest["generation_id"],objects="new dated raw_duck reconciliation tables and catalog_reconcile views")
        return
    if (root/"published.json").exists(): raise FileExistsError("Generation already published locally")
    pg=Postgres()
    present=list(pg.rows("SELECT count(*) AS n FROM information_schema.schemata WHERE schema_name='catalog_reconcile'"))[0]["n"]
    if present:
        check=list(pg.rows("SELECT obj_description(oid,'pg_namespace') AS contract FROM pg_namespace WHERE nspname='catalog_reconcile'"))[0]
        if check["contract"]!='Case Bible metadata reconciliation contract v1; raw_duck dated facts are authoritative':
            raise ValueError("Schema owner/contract mismatch")
    # stdout/stderr go to dated local receipts, avoiding pipe deadlocks and credential logging.
    with (root/"publish.stdout").open("x",encoding="utf-8") as stdout, (root/"publish.stderr").open("x",encoding="utf-8") as stderr:
        command=pg.command(writable=True)
        command[-1]="bash -o pipefail -c "+shlex.quote("gzip -dc | "+command[-1])
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
        stream=io.TextIOWrapper(gzip.GzipFile(fileobj=proc.stdin,mode="wb",compresslevel=1),encoding="utf-8",newline="")
        try:
            stream.write("BEGIN; SELECT pg_advisory_xact_lock(20260920,1);\n")
            stream.write(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
            generation=manifest["generation_id"]
            def send(table, rows):
                stream.write("\nCOPY raw_duck."+table+" FROM STDIN WITH (FORMAT CSV);\n")
                writer=csv.writer(stream,lineterminator="\n")
                count=0
                for identity,payload in rows:
                    writer.writerow([generation,identity,json.dumps(payload,ensure_ascii=False,separators=(",",":"))]);count+=1
                stream.write("\\.\n");stream.flush();emit("published_table_streamed",table=table,rows=count)
                return count
            # Generation and data commit atomically; readers cannot see a partially loaded generation.
            stream.write("\nCOPY raw_duck.reconcile_generations_20260920 (generation_id,status,manifest) FROM STDIN WITH (FORMAT CSV);\n")
            csv.writer(stream,lineterminator="\n").writerow([generation,manifest["status"],json.dumps(manifest)])
            stream.write("\\.\n")
            expected={}
            expected["reconcile_objects_20260920"]=send("reconcile_objects_20260920",((r["file_id"],r) for r in records(root/"object_versions.parquet")))
            expected["reconcile_occurrences_20260920"]=send("reconcile_occurrences_20260920",((r["occurrence_id"],r) for r in records(root/"occurrence_links.parquet")))
            expected["reconcile_work_items_20260920"]=send("reconcile_work_items_20260920",((r["item_id"],r) for r in records(root/"recovery_worklist.parquet")))
            expected["reconcile_r2_occurrences_20260920"]=send("reconcile_r2_occurrences_20260920",((r["occurrence_id"],r) for r in records(root/"r2_links.parquet")))
            expected["reconcile_native_exports_20260920"]=send("reconcile_native_exports_20260920",((stable_id(r["source"],r["source_id"]),r) for r in records(root/"native_export_reconciliation.parquet")))
            expected["reconcile_source_observations_20260920"]=send("reconcile_source_observations_20260920",((stable_id(r["source"],r["source_id"]),r) for r in records(root/"source_observations.parquet")))
            expected["reconcile_bas_candidates_20260920"]=send("reconcile_bas_candidates_20260920",((r["family_id"],r) for r in records(root/"bas_candidates.parquet")))
            def packages():
                for dataset in ("atomic_units","atomic_members","export_units","export_members","vault_units"):
                    for number,r in enumerate(records(root/(dataset+".parquet"))):
                        yield stable_id(dataset,number),{"dataset":dataset,"record":r}
            expected["reconcile_packages_20260920"]=send("reconcile_packages_20260920",packages())
            for table,count in expected.items():
                stream.write(f"DO $$ BEGIN IF (SELECT count(*) FROM raw_duck.{table} WHERE generation_id='{generation}') <> {count} THEN RAISE EXCEPTION 'row conservation failed'; END IF; END $$;\n")
            stream.write("COMMIT;\n");stream.close();proc.stdin.close()
            if proc.wait(timeout=600):raise RuntimeError("Publication failed; inspect dated stderr receipt")
        finally:
            if proc.poll() is None:proc.terminate()
    actual={}
    for table,count in expected.items():
        actual[table]=list(pg.rows(f"SELECT count(*) AS n FROM raw_duck.{table} WHERE generation_id='{generation}'"))[0]["n"]
        if actual[table]!=count:raise RuntimeError("Post-commit count differs")
    save_json(root/"published.json",{"generation_id":generation,"tables":actual,"status":"live_readback_verified"})
    emit("publication_verified",generation_id=generation,tables=actual)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation",required=True);parser.add_argument("--apply",action="store_true")
    args=parser.parse_args();publish(args.generation,args.apply)
