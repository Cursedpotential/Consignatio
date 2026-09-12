---
title: Case Bible — Enrichment Lakehouse
---

Live view of the Case Bible enrichment corpus, served from the **R2 Data Catalog (Iceberg)** → DuckDB. Rebuild the data (refresh script) to pull current rows from the lakehouse.

```sql totals
select
  count(*) as files,
  count(*) filter (where needs_review) as needs_review,
  round(avg(confidence), 3) as avg_conf
from casebible.enrichment
```

<BigValue data={totals} value=files title="Enriched files" fmt='#,##0'/>
<BigValue data={totals} value=needs_review title="Need review" fmt='#,##0'/>
<BigValue data={totals} value=avg_conf title="Avg confidence" fmt="0.00"/>

## Files per domain

```sql by_domain
select domain, count(*) as files, round(avg(confidence),2) as avg_conf
from casebible.enrichment
where domain is not null
group by 1 order by files desc
```

<BarChart data={by_domain} x=domain y=files swapXY=true title="Files per domain"/>

## Files per document type

```sql by_doctype
select doc_type, count(*) as files
from casebible.enrichment
where doc_type is not null
group by 1 order by files desc limit 15
```

<BarChart data={by_doctype} x=doc_type y=files swapXY=true title="Files per doc type"/>

## Disposition

```sql by_disp
select coalesce(disposition,'(none)') as disposition, count(*) as files
from casebible.enrichment group by 1 order by files desc
```

<DataTable data={by_disp}/>

## Browse the corpus

```sql files
select file, doc_type, domain, relevance, disposition, confidence, needs_review, summary
from casebible.enrichment
order by confidence desc
```

<DataTable data={files} search=true rows=12>
  <Column id=file/>
  <Column id=doc_type/>
  <Column id=domain/>
  <Column id=relevance/>
  <Column id=confidence fmt="0.00"/>
  <Column id=needs_review/>
</DataTable>
