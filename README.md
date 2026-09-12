# casekit — Codex A/B, Phase 0

Minimal Go CLI skeleton. No extraction, file operations, indexing, workers, or
integration are implemented in this phase.

Source plan: `F:\Users\matts\Downloads\repair_tool_kit_buildkit_v2.zip`.
The earlier `repair_tool_kit_buildkit.zip` supplies the missing BUILD_GUIDE and
TOOL-CATALOG documents. Neither archive supplied the referenced scaffold.
Their contents remain unmodified. The owner approved Phase 0, not a drive-root installation. Casekit is a module
inside Consignatio. This A/B worktree is named repair-tool-kit-codex; all
controlled state stays inside its module directory under runtime-codex.

## Build and test

From PowerShell 7, with Go 1.26 installed:

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\repair-tool-kit-codex\repair-tool-kit" && pwsh -NoProfile -File .\scripts\build.ps1 -Target all -Version 0.0.0-phase0
```

The script prints a fresh output directory containing `casekit.exe`,
`casekitw.exe`, and `casekit-linux-amd64`. It runs vet, build, and tests first.
`-Target windows`, `linux`, or `verify` provide smaller tasks. Taskfile targets
wrap the same script if Task is installed; Task is not required or installed here.
PowerShell 7 on Windows is the tested build host; Linux is a cross-compile target.

All controlled caches, temporary files and outputs use
`E:\AI_Workspace\Projects\Propria\Consignatio\repair-tool-kit-codex\repair-tool-kit\runtime-codex`. No global environment settings are changed.
The build uses two compiler slots, GOMAXPROCS=2 and a 512 MiB Go runtime soft
memory target (not a hard aggregate process-memory ceiling).

Smoke-test a printed output directory:

```powershell
cd "E:\AI_Workspace\Projects\Propria\Consignatio\repair-tool-kit-codex\repair-tool-kit" && pwsh -NoProfile -File .\scripts\smoke-test.ps1 -BuildDirectory "<printed build directory>"
```

The smoke test checks both PE subsystems and exact version output, checks the
Linux ELF header, and launches a local shortcut with normal window settings.
The shortcut stays beside the build. It does not register shell verbs, install
a service, or modify the desktop. Physical no-flash observation remains a human
check; inspecting the subsystem is not a claim of observing the screen.

`--version` prints only the build version. `--config config.example.toml` checks
the small Phase 0 TOML configuration; it does not create installation directories.
The TOML parser is pinned to `github.com/BurntSushi/toml v1.6.0` in go.mod/go.sum.

See [Phase 0 receipt and checklist](docs/phase0.html) for verification and remaining work.

The [location correction receipt](docs/location-correction-codex.html) supersedes
earlier installation-location claims and identifies the fresh verified build.
