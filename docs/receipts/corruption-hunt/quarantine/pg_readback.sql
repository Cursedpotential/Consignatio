select 'integrity_hold rows', count(*) from raw_duck.integrity_hold;
select 'audit by catalog/reason', catalog, reason, count(*), count(*) filter (where original_hash is not null) as original_hash_kept from raw_duck.integrity_hold group by 2, 3 order by 2, 3;
select 'r2_files flagged', count(*), 'still hashed', count(*) filter (where md5 is not null) from raw_duck.r2_files where integrity_status is not null;
select 'final_survivors excluded', count(*), 'still hashed', count(*) filter (where md5 is not null) from raw_duck.final_survivors where integrity_status is not null;
select 'survivors eligible (unflagged, hashed)', count(*), round(sum(size)/1e9, 1) from raw_duck.final_survivors where integrity_status is null and coalesce(md5,'') <> '';
