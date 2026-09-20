---
title: Codex — the catalog is its own foundation; audit the existing catalog model before Build 1 consumes it
platform: Codex
model: not stated by owner
created: 2026-09-18
tags: [catalog, source-of-truth, raw_duck, catalog-audit, cocoindex, build-1, identity, occurrence, dates, provenance, hashes, packages, codex-review]
summary: "Codex stops Build 1 before more wiring: key+size+sha1 is not the catalog contract. The catalog is independent of Spacedrive, the viewer, Intake and CocoIndex; they consume it. The catalog model must cover identity (object vs occurrence), current physical location, original/recorded location, names (queryable), many distinct dates (never merged or invented), hashes at the right level, type/signature, source/provenance, package/container relationships, and operational state. Prerequisite: inspect and document the existing catalog model — 11 questions (tables/views, what each represents, object identity, source occurrence, physical B2 inventory, temporal metadata, provenance metadata, hashes, package relationships, classification/disposition state, authority per fact) — then Build 1 consumes it. Do not 'fix' or re-invent the catalog before auditing it."
provenance:
  saved_by: "Claude Code · Opus 5"
  saved_at: 2026-09-18T22:55:00-04:00
  shared_by: owner, pasted into chat 2026-09-18 22:52 EDT
  content: verbatim paste; only this front matter was added. "Pasted text.txtTXT" strings are Codex citation chips.
  why_it_matters: pauses Build 1 and sets the catalog-model audit as the prerequisite; logged in docs/URGENT-TODO.md 2026-09-18 22:55
---

> _Byline: transcript from Codex, saved verbatim by Claude Code · Opus 5 · 2026-09-18_

Yes. This is exactly where Claude started drifting again. It began writing `catalog_source.py` before it had actually established what the catalog contract is. The transcript shows it first reduced the source to `key, size, sha1`, then only after you challenged it admitted the real catalog contains original paths/names, source accounts, modified times, other hashes, and metadata. Pasted text.txtTXT
And your instinct is right: `key + size + sha1` is nowhere near enough for the catalog you need.
The catalog is its own foundation
It should be independent of:

* Spacedrive
* the hosted viewer
* Intake
* CocoIndex
* whatever UI happens to exist this week

Those systems consume the catalog. They do not define it.
The architecture should be:

```
                    VAULT / B2 / SOURCES
                            ↓
                     MASTER CATALOG
                  source-of-truth inventory
                            ↓
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
      CocoIndex          Viewer/UI       Organization tools
      discovery
          ↓
   select for intake
          ↓
      Go platform
```

Claude actually recognized that after your correction—“the CocoIndex app will read the catalog database directly, independent of any viewer or explorer”—but it should have established that before writing the source module. Pasted text.txtTXT
What the catalog needs to know
Not every field has to exist in one physical table, but the catalog model needs enough information to answer questions about identity, location, time, provenance, duplicates, and source context.
At minimum, I would expect these groups.
Identity

```
catalog_object_id
source_id
source_occurrence_id
stable object/file identity
```

The catalog has to distinguish an underlying object from an occurrence of that object.
That's important because the same bytes can appear:

```
Google Drive/export/foo.jpg
Recovered Disk/foo.jpg
B2/archive/foo.jpg
old phone backup/foo.jpg
```

One content hash does not mean those occurrences are semantically interchangeable.
Current physical location

```
storage_backend
bucket/container
object key
current canonical locator
size
```

This tells the systems where the bytes currently live.
Original / recorded location
This is just as important:

```
original filename
original relative path
recorded source path
source folder/package
original B2 key if migrated
```

Claude's existing catalog view already contains some of this: `source`, `scope`, `path`, `source_id`, recorded B2 key, matched origin, metadata, and resolved current vault key. Pasted text.txtTXT
That information should not be collapsed into one current filename.
Names
Absolutely yes, filenames must be queryable.
Ideally:

```
filename
stem
extension
original filename
normalized filename
possibly historical filename(s)
```

That allows:
find everything whose name contains Katrina
without scanning file contents.
And also:
find all files whose original filename was X even though the vault organization renamed/moved them.
Dates
Also yes.
But not one ambiguous `date` field.
You can have several different dates with completely different meanings:

```
filesystem created time
filesystem modified time
source-recorded created time
source-recorded modified time
object-store upload time
catalog first-seen time
catalog last-seen time
ingest/discovery time
archive member timestamp
EXIF/media creation time
document metadata date
```

Not all of them will exist for every file.
And you must not invent one date from another.
That becomes extremely important when you later query:
show files from May 2024
because you need to know whether that means:

* content event date,
* EXIF creation date,
* filesystem mtime,
* backup export date,
* or B2 upload date.

Hashes / fingerprints
Not merely SHA-1.
Something like:

```
sha256
sha1
md5 if inherited from source
native source hash
native hash algorithm
size
```

And potentially later:

```
perceptual image hash
media fingerprint
normalized-document fingerprint
```

Those are derived discovery properties, though, so I would not force all of them into the base object row.
Type information

```
extension
reported MIME
sniffed MIME
media family
detected signature
signature confidence
```

Crucially:

```
foo.json
```

isn't enough.
Discovery may determine:

```
application/json
    ↓
Claude official conversation export
```

or:

```
application/xml
    ↓
SMS Backup & Restore
```

That richer signature belongs either in the catalog's discovery/enrichment layer or a linked classification table.
Source/provenance
This is especially important for your recovered and exported data:

```
source device/account
source system
collection/export
archive/package
recovery source
parent source
source path
collection timestamp
source metadata
```

That lets you distinguish:
This photo was recovered from Phone A
from:
the exact same bytes appeared inside a Google Photos Takeout.
Again, hash equality does not erase provenance.
Package/container relationships
The catalog should support:

```
ZIP
 ├─ member A
 ├─ member B
 └─ member C

Takeout
 └─ package members

SMS export
 ├─ XML
 └─ attachments

phone backup
 └─ contained objects
```

That can be modeled as relationships rather than stuffing everything into one row.
State
You also need operational state:

```
exists / missing
resolved / unresolved
duplicate candidate
canonical candidate
quarantined
ignored
classified
needs review
selected for intake
```

Not necessarily those exact names—I am not declaring a schema rule here—but the catalog needs to support those concepts.
What should NOT happen
Claude was heading toward:

```
vault_objects
    key
    size
    sha1
        ↓
CocoIndex
```

That would make the current B2 object listing masquerade as the catalog.
Wrong abstraction.
`vault_objects_20260916_r4` may be an excellent physical-storage inventory.
It is not necessarily the whole catalog.
In fact, the SQL Claude inspected already proves there's more:

```
source
scope
path
source_id
size
modtime
native_hash_kind
native_hash
md5
disposition
b2_key_recorded
matched_origin
metadata
recorded_at
sha1
vault_key
resolution
```

Those fields are visible in the existing catalog view it inspected. Pasted text.txtTXT
So the information wasn't absent.
Claude simply grabbed the thinnest convenient table.
CocoIndex should receive a rich descriptor
Build 1 should not be:

```
key
size
sha1
```

It should conceptually receive something much more like:

```
CatalogObjectDescriptor

identity
    catalog_object_id
    source_occurrence_id

location
    current object locator
    original/recorded locator

name
    filename
    original filename
    extension

source
    source
    scope
    source_id
    package/container membership

physical metadata
    size
    modified time(s)

fingerprints
    known hashes

catalog metadata
    disposition
    resolution
    source metadata

discovery metadata
    detected signature
    classification
    etc.
```

Then CocoIndex can enrich that descriptor with:

```
searchable content
chunks
semantic embeddings
classification/signatures
package relationships
duplicate evidence
relevance signals
```

without replacing the catalog.
And your dates question is particularly important
You said:
“Because we're going to be querying against dates…”
Yes.
You absolutely want to be able to issue discovery queries such as:

```
files modified during June 2025
photos whose EXIF creation was June 2025
exports collected after June 2025
AI chats created around a particular event
files first seen on a certain device
objects recorded in a backup from a certain period
```

Those queries become impossible or misleading if the catalog boils everything down to:

```
key / size / hash
```

And later, when you build timelines, you cannot afford for storage timestamps and event timestamps to get conflated.
So I would stop Claude's Build 1 right where that transcript ends
It had already created `catalog_source.py` with 93 lines. Pasted text.txtTXT
I would not let it continue wiring that implementation yet.
Not because Build 1 is wrong.
Because the prerequisite is:
Inspect and document the existing master catalog model first.
Specifically:

```
1. What catalog tables/views already exist?
2. What does each represent?
3. Which is object identity?
4. Which is source occurrence?
5. Which is current physical B2 inventory?
6. What temporal metadata is available?
7. What source/provenance metadata exists?
8. What hashes exist and at what level?
9. What package/container relationships already exist?
10. What classification/disposition state exists?
11. Which table/view is authoritative for which facts?
```

Then Build 1 consumes that model.
It should not invent another catalog schema just because a Python module needs a query.
So: did Claude fuck up another task?
Not necessarily the underlying catalog.
From this transcript, I cannot conclude the catalog itself is broken.
What I can conclude is that Claude nearly underused an apparently much richer existing catalog by selecting `key, size, sha1` as though that were the source contract. The moment you challenged it, it found richer occurrence/catalog fields already sitting there. Pasted text.txtTXT
So before anybody “fixes the catalog,” audit what already exists.
Given what we've seen tonight, there is a very real chance that task is another case of:
the architecture/data already exists, but the new implementation grabbed the easiest narrow subset of it.
That distinction matters, because I do not want another agent “correcting” a catalog that may already contain exactly the information you need.
