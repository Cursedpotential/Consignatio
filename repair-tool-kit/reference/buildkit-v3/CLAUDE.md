# CLAUDE.md — casekit operating rules

## Before anything

Read `RULES.md` in the buildkit. It outranks this file and every other. In
particular: **guidance is not rules.** Do not add rules to any file. Do not
promote a "should" into a "must". If you think something ought to be binding,
say so and ask.

## Verification loop

```bash
go vet ./... && go build ./... && go test ./...
casekit doctor                      # every engine resolves and reports a version
casekit profile docs/reference/*    # must match PHASES.md Phase 2 values
```

Never declare a phase done without running its stated exit criterion command.
Incomplete validation before claiming completion is a specific known failure
mode here.

## Absolute rules for this codebase

1. **Never open a source file for write.** Hash before and after any operation;
   the hashes must match. All output is a derivative elsewhere.
2. **Never delete.** Superseded material goes to quarantine.
3. **mutool is not permitted in the glyph-accurate text path.** It maps
   ZapfDingbats `0x6E` to `I`, which corresponds to nothing and is
   unrecoverable. Raster and structure use only.
4. **Never parse XML with regex.** Base64 payloads contain `=` and silently
   corrupt attribute scanning. lxml or DuckDB only.
5. **Set sparse attributes on every element in the slim pass.** DuckDB's
   sample-based inference drops fields present on only some elements — this
   silently deleted every image during planning.
6. **Never point DuckDB at a raw XML file with base64 in it.**
   `xml_extract_attributes` consumed 3.1 GiB on a 3.8 MB file.
7. **`recovered` and `reconstructed` never share a status field.** Recovered
   means it existed and was retrieved. Reconstructed means it was inferred.
8. **Never infer, assume, or fabricate a value.** Unknown is unknown. Mark
   uncertainty as `estimated`.
9. **Every derived value carries a `derivation` block** — level, why,
   `derived_from` element IDs with byte offsets, method, assumptions, and
   `not_established`. A bare confidence label with no reasoning is not
   acceptable output (RULES R11). Same for every flag: whatever raised it
   states why.

## Where code goes

| Concern | Path |
|---|---|
| entry points | `cmd/casekit`, `cmd/casekitw` |
| file classification | `internal/profile` |
| engine selection + checks | `internal/route` |
| subprocess contract, registry, pools | `internal/engine` |
| format-specific extraction | `internal/extract` |
| content-addressed payloads | `internal/blob` |
| sealing + manifest | `internal/pkg` |
| append-only JSONL | `internal/ledger` |
| engine implementations | `engines/<id>/` |

Routes live in `internal/route/routes.toml` and are **hand-edited**. Never
compile a route into the binary.

## Conventions

- `gofmt` on save; `go vet` clean before any commit.
- Two binaries: `casekit.exe` (console) and `casekitw.exe`
  (`-ldflags "-H windowsgui"`, no console flash from shell verbs).
- Python engines run from a frozen `uv` venv under `engines/python/.venv`.
  Never depend on an ambient interpreter.
- Every engine reports its own id, version, and the exact commands it ran;
  those go into the sidecar verbatim.
- Windows paths are opaque strings across the contract. Test with a path
  containing a space and a non-ASCII character.

## Working style

- Ask before creating files. No silent decisions.
- Complete scripts, not fragments.
- Don't volunteer risk warnings or opposing arguments during build work.
- Don't gold-plate. The bar is "done and mostly accurate" — see RULES R2.
