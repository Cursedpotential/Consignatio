/**
 * Byline: Claude Code · Sonnet 5 · 2026-09-14
 *
 * Receives the live selection manifest broadcast by the Xplorer engine iframe
 * (see xplorer-copilot-buildkit/xplorer-copilot apps/client/src/hooks/use-intake-embed-bridge.ts)
 * over window.postMessage. Metadata only -- names, paths, sizes and type; no file
 * bytes cross this bridge. This app never reads the selected files itself.
 */
import { useEffect, useState } from "react";

const BRIDGE_SOURCE = "xplorer-intake-bridge";

export interface BridgeSelectionEntry {
  name: string;
  path: string;
  file_type: string;
  size?: number;
  metadataOnly?: boolean;
}

export interface BridgeSelectionState {
  /** True once any message has been received from an embedded Xplorer engine. */
  connected: boolean;
  currentPath: string;
  count: number;
  selection: BridgeSelectionEntry[];
}

const initialState: BridgeSelectionState = {
  connected: false,
  currentPath: "",
  count: 0,
  selection: [],
};

const isSelectionMessage = (
  data: unknown,
): data is {
  source: string;
  type: "selection";
  currentPath: string;
  count: number;
  selection: BridgeSelectionEntry[];
} =>
  typeof data === "object" &&
  data !== null &&
  (data as { source?: unknown }).source === BRIDGE_SOURCE &&
  (data as { type?: unknown }).type === "selection";

const isReadyMessage = (
  data: unknown,
): data is { source: string; type: "ready" } =>
  typeof data === "object" &&
  data !== null &&
  (data as { source?: unknown }).source === BRIDGE_SOURCE &&
  (data as { type?: unknown }).type === "ready";

/** Untrusted transport: only structurally-valid messages from the known source are applied. */
export function useIntakeSelectionBridge(): BridgeSelectionState {
  const [state, setState] = useState<BridgeSelectionState>(initialState);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      const { data } = event;
      if (isReadyMessage(data)) {
        setState((prev) => ({ ...prev, connected: true }));
        return;
      }
      if (isSelectionMessage(data)) {
        setState({
          connected: true,
          currentPath:
            typeof data.currentPath === "string" ? data.currentPath : "",
          count: Number.isFinite(data.count)
            ? data.count
            : data.selection.length,
          selection: Array.isArray(data.selection) ? data.selection : [],
        });
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  return state;
}
