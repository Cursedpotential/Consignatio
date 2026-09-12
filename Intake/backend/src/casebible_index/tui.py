from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static

from .config import Settings
from .fingerprints import newest_atomic_run, newest_fingerprints
from .inventory import newest_inventory
from .snapshots import newest_snapshot


class CaseBibleTui(App[None]):
    """Operator console for the isolated Case Bible corpus pipeline."""

    TITLE = "Case Bible Corpus"
    SUB_TITLE = "CocoIndex + NVIDIA NIM + Parquet"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("ctrl+c", "cancel_operation", "Cancel run"),
    ]
    CSS = """
    Screen { background: #0c111b; color: #d7e0ea; }
    #identity { height: 3; padding: 0 1; color: #8fbad9; }
    #form { height: auto; padding: 0 1; }
    .field-label { width: 12; padding-top: 1; color: #8fa3b8; }
    Input { margin: 0 0 1 0; }
    #actions { height: auto; padding: 0 1 1 1; }
    Button { margin-right: 1; min-width: 15; }
    #summary { height: 8; margin: 0 1 1 1; padding: 1; border: round #31516d; }
    #search-row { height: auto; padding: 0 1; }
    #query { width: 1fr; }
    #run-search { width: 15; margin-left: 1; }
    #log { height: 1fr; margin: 0 1 1 1; border: round #31516d; }
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.active_process: subprocess.Popen[str] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Isolated command: casebible-corpus  |  State: output/.casebible-corpus  |  "
            "No ccc commands or ~/.cocoindex_code state are used",
            id="identity",
        )
        with Vertical(id="form"):
            with Horizontal():
                yield Label("Source", classes="field-label")
                yield Input(str(self.settings.source_dir), id="source")
            with Horizontal():
                yield Label("Output", classes="field-label")
                yield Input(str(self.settings.output_dir), id="output")
            with Horizontal():
                yield Label("Source ID", classes="field-label")
                yield Input(self.settings.source_id, id="source-id")
        with Horizontal(id="actions"):
            yield Button("Inventory", id="inventory", variant="primary")
            yield Select(
                [("Hash all files", "all"), ("Hash duplicate-size candidates", "dedup-candidates")],
                value="all",
                allow_blank=False,
                id="hash-scope",
            )
            yield Button("Fingerprint", id="fingerprint", variant="primary")
            yield Button("Detect units", id="detect-units")
            yield Button("Index + summarize", id="index", variant="success")
            yield Button("Refresh", id="refresh")
        yield Static(id="summary")
        with Horizontal(id="search-row"):
            yield Input(placeholder="Semantic search query", id="query")
            yield Button("Search", id="run-search", variant="primary")
        yield RichLog(id="log", wrap=True, highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.action_refresh()
        self.query_one("#log", RichLog).write(
            "[bold cyan]Ready.[/] Run Inventory before Fingerprint or Detect units. "
            "Every operation is read-only against the source tree."
        )

    def _values(self) -> tuple[Path, Path, str]:
        source = Path(self.query_one("#source", Input).value).expanduser().resolve()
        output = Path(self.query_one("#output", Input).value).expanduser().resolve()
        source_id = self.query_one("#source-id", Input).value.strip() or "casebible"
        return source, output, source_id

    def _base_args(self) -> list[str]:
        source, output, source_id = self._values()
        return ["--source", str(source), "--output", str(output), "--source-id", source_id]

    def _set_busy(self, busy: bool) -> None:
        for button in self.query(Button):
            if button.id not in {"refresh"}:
                button.disabled = busy

    def _append_log(self, value: str) -> None:
        self.query_one("#log", RichLog).write(value)

    @work(thread=True, exclusive=True, group="casebible-corpus-operation")
    def run_operation(self, arguments: list[str]) -> None:
        self.call_from_thread(self._set_busy, True)
        display_command = f"[cyan]Running:[/] casebible-corpus {' '.join(arguments)}"
        self.call_from_thread(self._append_log, display_command)
        environment = os.environ.copy()
        command = [sys.executable, "-m", "casebible_index.cli", *arguments]
        try:
            self.active_process = subprocess.Popen(
                command,
                cwd=Path(__file__).resolve().parents[2],
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert self.active_process.stdout is not None
            for line in self.active_process.stdout:
                self.call_from_thread(self._append_log, line.rstrip())
            return_code = self.active_process.wait()
            if return_code:
                self.call_from_thread(
                    self._append_log, f"[bold red]Run failed with exit code {return_code}.[/]"
                )
            else:
                self.call_from_thread(self._append_log, "[bold green]Run completed.[/]")
                self.call_from_thread(self.action_refresh)
        except Exception as exc:
            self.call_from_thread(self._append_log, f"[bold red]{type(exc).__name__}: {exc}[/]")
        finally:
            self.active_process = None
            self.call_from_thread(self._set_busy, False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "refresh":
            self.action_refresh()
            return
        if button_id == "run-search":
            query = self.query_one("#query", Input).value.strip()
            if not query:
                self.notify("Enter a search query", severity="warning")
                return
            _, output, _ = self._values()
            self.run_operation(["search", query, "--output", str(output)])
            return
        arguments = [str(button_id), *self._base_args()]
        if button_id == "fingerprint":
            scope = str(self.query_one("#hash-scope", Select).value)
            arguments.extend(["--scope", scope])
        self.run_operation(arguments)

    def action_refresh(self) -> None:
        try:
            _, output, _ = self._values()
            atomic = newest_atomic_run(output)
            summary = {
                "active_snapshot": str(newest_snapshot(output) or "not created"),
                "inventory": str(newest_inventory(output) or "not created"),
                "fingerprints": str(newest_fingerprints(output) or "not created"),
                "atomic_units": str(atomic or "not created"),
                "source_mutation": "disabled",
            }
            self.query_one("#summary", Static).update(json.dumps(summary, indent=2))
        except Exception as exc:
            self.query_one("#summary", Static).update(f"Status unavailable: {exc}")

    def action_cancel_operation(self) -> None:
        process = self.active_process
        if process is None or process.poll() is not None:
            self.notify("No active operation")
            return
        process.terminate()
        self._append_log(
            "[yellow]Cancellation requested; partial derived output remains visible.[/]"
        )


def run_tui(settings: Settings) -> None:
    CaseBibleTui(settings).run()
