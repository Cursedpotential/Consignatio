# Interaction design

## Approved Platform palette

Light workspace:

- Workspace/paper `#F5F3EE`; raised surface `#FFFEFB`.
- Primary ink `#1D2228`; muted text `#687078`.
- Soft fill `#EBE8E0`; border `#D5D1C9`; strong border `#B8B6B0`.

Graphite shell:

- Top navigation `#151E25`; darkest navigation `#121A21`.
- Sidebar `#202B33`; active sidebar `#314050`; sidebar border `#3D4952`.
- Shell text `#D9DFE2`; bright shell text `#F7F8F7`.

Interaction:

- Indigo `#4051B9`; dark indigo `#2F3D9C`.
- Soft indigo `#E9ECFB`; focus indigo `#8290ED`.

Status only:

- Success `#2F9D67`; strong success `#17794B`; background `#E2F3E9`.
- Warning `#C58214`; background `#FFF4DD`.
- Destructive `#B5433B`; background `#FBE9E7`.

Dark workspace:

- Workspace `#1D252C`; surface `#242E36`.
- Primary text `#F0F1EF`; muted text `#B1B8BD`.
- Soft fill `#2C373F`; border `#43505A`; strong border `#62707A`.
- Primary indigo `#8591F0`; soft indigo `#313A66`.

Typography uses **Instrument Sans** for navigation and actions, **Source Serif 4**
sparingly for review-set titles, and **IBM Plex Mono** for identifiers, hashes,
counts, and receipts. System fallbacks keep the initial build offline-capable.

The shell remains graphite while the working area feels like warm paper. Indigo is
the only interaction accent. Green, amber, and red communicate status and never
decoration. There are no gradients, glass effects, neon treatments, or nested card
stacks. Operational surfaces are square or lightly rounded with fine borders,
compact density, and restrained shadows.

## Layout

```text
┌ review-set header / mode / search / sync ────────────────────────────────┐
├ lenses ───────┬ grid or contact sheet ────────────┬ decision record ────┤
│ saved views   │ dense source records              │ SOURCE              │
│ groups        │                                   │ PROPOSAL            │
│ tags          │                                   │ HUMAN               │
├───────────────┴───────────────────────────────────┴─────────────────────┤
│ persistent selection ledger and bulk-action preview                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Signature interaction

The bottom selection ledger behaves like a physical evidence tray. It always states:

```text
7 selected · 5 visible · 2 hidden by filters
```

It previews the scope of a bulk action before application and remains present when
switching between Grid, Gallery, and Hierarchy modes.

## Provenance rail

The inspector is not a generic property drawer. It presents three fixed strata:

1. **Source** — what the source system actually supplied.
2. **Proposal** — what a model or rule suggested and why.
3. **Human decision** — what was accepted, rejected, corrected, or left unresolved.

## Self-critique

An earlier three-panel concept risked resembling a generic admin dashboard. The
revision makes provenance, selection scope, and review state structural. Decorative
cards, gradients, oversized metrics, and gratuitous motion were removed. The single
expressive device is the selection ledger; everything else stays dense and quiet.
