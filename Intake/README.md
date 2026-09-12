# Intake

Intake is the desktop work surface for **Consignatio**, the Vault project designated
at `E:\AI_Workspace\Projects\Propria\Consignatio\`. See the
[project naming and location decision](docs/UNIFIED-PROJECT.md) for the distinction
between the Vault location and the current application source directory.

Unified application: React/Tauri frontend here, CocoIndex corpus backend in `backend/`.
Start with [the project and planning index](docs/UNIFIED-PROJECT.md) for the merged
scope, commands, diagrams, priorities, and implementation boundaries.

Case Bible Workbench is a local-first desktop review surface for turning large,
machine-proposed datasets and curated media albums into human-approved structure.
It is not an evidence store and it does not create a second approval authority.

The first runnable slice demonstrates the enduring interaction model:

- a virtualized Glide Data Grid for dense review;
- a synchronized contact sheet for pictures;
- bulk selection, automatic group numbers, and tagging;
- a provenance rail that separates source facts, machine proposals, and human decisions;
- an explicit handoff boundary for governed Platform intake.

## Run locally

```powershell
cd E:\AI_Workspace\casebible\workbench
npm install
npm run dev
```

Storybook:

```powershell
npm run storybook
```

Desktop shell, after installing dependencies:

```powershell
npm run tauri dev
```

## Verify

```powershell
npm run test
npm run build
npm run build-storybook
```

## Read first

- [Product brief](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data contracts](docs/DATA-CONTRACTS.md)
- [Media connectors](docs/CONNECTORS.md)
- [Interaction design](docs/INTERACTION-DESIGN.md)
- [Implementation status](docs/STATUS.md)
