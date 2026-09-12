# Product brief

## Subject, audience, and job

**Subject:** high-volume human review of file inventory, photographs, albums, and
machine-generated classification proposals.

**Primary operator:** the Case Bible owner conducting long, high-attention review
sessions on a Windows workstation.

**Single job:** convert a source review set into human-approved groups, tags, and
intake decisions without changing the source or obscuring provenance.

## Product boundary

The Workbench may browse source systems, cache thumbnails and metadata, organize a
review set, run explicitly registered local tools, and submit opaque references to
the Platform's governed acquisition workflow.

The Workbench does not:

- treat an album name or folder name as truth;
- mutate original imported values;
- write directly into canonical evidence tables;
- establish custody merely because a thumbnail was viewed;
- propagate deletions to Immich, PhotoPrism, or the filesystem;
- execute arbitrary shell strings supplied by UI state or imported data.

## First complete workflow

1. Open a sample or imported JSON/CSV review set.
2. Inspect records in Grid or Gallery mode.
3. Select visible or non-contiguous records.
4. apply tags and create an automatically numbered group.
5. Inspect Source, Proposal, and Human layers separately.
6. Undo the human operation.
7. prepare an intake handoff containing opaque source references.
8. export immutable source values plus the annotation overlay.

## Album workflow

An Immich or PhotoPrism album is imported as a versioned review-set snapshot. A
later sync creates a new snapshot and a membership delta; it never rewrites a prior
review. Selected items can be copied into governed Platform storage only through
the existing acquisition, preview, confirmation, and evidence-promotion process.

## Success criteria

- Selection remains intelligible when filters hide selected records.
- Source, proposal, and human fields cannot be mistaken for each other.
- A bulk action previews its exact scope before application.
- Every mutation is undoable and receipt-producing.
- Grid and Gallery share identity and selection.
- Large media files are loaded lazily; thumbnails are not treated as originals.

