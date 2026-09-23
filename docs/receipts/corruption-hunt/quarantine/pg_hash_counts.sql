select 'legacy_hashes.raw_hashes', count(*), count(distinct md5) from legacy_hashes.raw_hashes;
select 'legacy_hashes.raw_sizehash', count(*) from legacy_hashes.raw_sizehash;
select 'evidence.evidence_hash', count(*) from evidence.evidence_hash;
select 'raw_hashes columns', string_agg(column_name, ', ' order by ordinal_position) from information_schema.columns where table_schema = 'legacy_hashes' and table_name = 'raw_hashes';
