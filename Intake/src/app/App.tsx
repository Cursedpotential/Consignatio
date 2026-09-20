/** Case Bible Workbench · Byline: Codex · GPT-5 · 2026-08-30 */

import { useState } from "react";
import { ImportPanel } from "../features/import/ImportPanel";
import { ReviewWorkbench } from "../features/review/ReviewWorkbench";
import {
  datasetToReviewItems,
  type ImportedDataset,
} from "../features/import/dataset";
import { LiveSelectionPanel } from "../features/live-selection/LiveSelectionPanel";

export default function App() {
  const [importOpen, setImportOpen] = useState(false);
  const [dataset, setDataset] = useState<ImportedDataset>();

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "16px 16px 0 16px", flexShrink: 0 }}>
        <LiveSelectionPanel />
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <ReviewWorkbench
          key={dataset?.id ?? "sample"}
          initialItems={dataset ? datasetToReviewItems(dataset) : undefined}
          reviewSetId={dataset?.id}
          reviewSetTitle={dataset?.filename}
          sourceLabel={
            dataset ? `${dataset.format.toUpperCase()} import` : undefined
          }
          visibleFieldKeys={dataset?.visibleFields}
          onImportRequest={() => setImportOpen(true)}
        />
      </div>
      <ImportPanel
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onLoad={setDataset}
      />
    </div>
  );
}
