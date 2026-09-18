from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from .feature_registry import Feature, FeatureParam, current_platform, load_registry
from .launcher import FeatureLauncher


def _import_textual():
    try:
        from textual.app import App, ComposeResult
        from textual.binding import Binding
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.screen import Screen
        from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, ListItem, ListView, Select, Static
    except ImportError as exc:
        raise RuntimeError(
            'Console UI requires Textual. Install with: python -m pip install -e ".[ui,vision]"'
        ) from exc
    return {
        "App": App,
        "ComposeResult": ComposeResult,
        "Binding": Binding,
        "Horizontal": Horizontal,
        "Vertical": Vertical,
        "VerticalScroll": VerticalScroll,
        "Screen": Screen,
        "Button": Button,
        "Checkbox": Checkbox,
        "Footer": Footer,
        "Header": Header,
        "Input": Input,
        "Label": Label,
        "ListItem": ListItem,
        "ListView": ListView,
        "Select": Select,
        "Static": Static,
    }


T = _import_textual()
App = T["App"]
ComposeResult = T["ComposeResult"]
Binding = T["Binding"]
Horizontal = T["Horizontal"]
Vertical = T["Vertical"]
VerticalScroll = T["VerticalScroll"]
Screen = T["Screen"]
Button = T["Button"]
Checkbox = T["Checkbox"]
Footer = T["Footer"]
Header = T["Header"]
Input = T["Input"]
Label = T["Label"]
ListItem = T["ListItem"]
ListView = T["ListView"]
Select = T["Select"]
Static = T["Static"]


CSS = """
Screen { background: #090a0f; color: #e7e7ee; }
#body { height: 1fr; }
#sidebar { width: 38%; border: round #555577; padding: 1; }
#detail { width: 62%; border: round #555577; padding: 1 2; }
.category { color: #9da4ff; text-style: bold; margin-top: 1; }
.feature-title { text-style: bold; color: #ffffff; }
.feature-description { color: #b9bbcc; margin-bottom: 1; }
.status-running { color: #8cffbd; text-style: bold; }
.status-idle { color: #9a9aae; }
.status-error { color: #ff7777; text-style: bold; }
.param-group { height: auto; border: round #34364b; padding: 0 1 1 1; margin-bottom: 1; }
.param-group-title { color: #aeb3ff; text-style: bold; margin: 0 0 1 0; }
.param-row { height: auto; margin-bottom: 1; }
.param-label { width: 28; padding-top: 1; }
.param-control { width: 1fr; }
.param-help { color: #74778d; margin: 0 0 1 28; }
#launch { margin-top: 1; width: 1fr; }
#stop { margin-top: 1; width: 1fr; }
#log-actions { height: auto; margin-top: 1; }
#copy-log, #open-log { width: 1fr; }
#log-path { color: #8e91a7; margin-top: 1; }
#log { height: 18; border: round #333344; padding: 1; overflow-y: auto; }
.hint { color: #8e91a7; margin-top: 1; }
.unsupported { color: #777785; }
"""


def _control_id(param: FeatureParam) -> str:
    return f"param-{param.key.replace('_', '-')}"


class ConfigScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Stop / Back"),
        Binding("ctrl+r", "launch", "Launch"),
    ]

    def __init__(self, feature: Feature, values: dict[str, Any] | None = None):
        super().__init__()
        self.feature = feature
        self.values = feature.defaults()
        if values:
            self.values.update(values)

    def _param_control(self, param: FeatureParam):
        value = self.values.get(param.key, param.default)
        if param.type == "bool":
            return Checkbox(value=bool(value), id=_control_id(param), classes="param-control")
        if param.type == "choice":
            options = [(choice, choice) for choice in param.choices]
            return Select(options, value=str(value), id=_control_id(param), classes="param-control")
        return Input(value=str(value), id=_control_id(param), classes="param-control")

    def compose(self):
        yield Header(show_clock=True)
        with VerticalScroll(id="detail"):
            yield Static(self.feature.name, classes="feature-title")
            yield Static(self.feature.description, classes="feature-description")
            if not self.feature.available():
                yield Static(self.feature.availability_hint(), classes="unsupported")

            for group_name, params in self.feature.grouped_params():
                with Vertical(classes="param-group"):
                    yield Static(group_name.upper(), classes="param-group-title")
                    for param in params:
                        with Horizontal(classes="param-row"):
                            yield Label(param.label, classes="param-label")
                            yield self._param_control(param)
                        if param.help:
                            yield Static(param.help, classes="param-help")

            yield Button(
                "LAUNCH FULLSCREEN" if self.feature.available() else "UNAVAILABLE",
                id="launch",
                variant="success",
                disabled=not self.feature.available(),
            )
            yield Static(
                "Controls are grouped by intent: system/input, output resolution, design, behavior, "
                "and performance. Launching keeps this exact configuration screen alive. ESC in the "
                "projector exits the visual and returns here with every value preserved; terminal ESC "
                "stops the child tree and also keeps these settings.",
                classes="hint",
            )
        yield Footer()

    def _values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for param in self.feature.params:
            widget = self.query_one(f"#{_control_id(param)}")
            if param.type == "bool":
                values[param.key] = widget.value
            elif param.type == "choice":
                values[param.key] = widget.value
            else:
                values[param.key] = widget.value
        return values

    def action_back(self) -> None:
        # ESC while a visual runs stops the child but deliberately leaves this configuration
        # screen mounted. Projector-window ESC exits the child directly, revealing the same form.
        if self.app.launcher.poll().running:
            self.app.stop_active()
            return
        self.app.remember_feature_values(self.feature, self._values())
        self.app.pop_screen()

    def action_launch(self) -> None:
        self._launch()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch":
            self._launch()

    def _launch(self) -> None:
        try:
            values = self._values()
            self.feature.build_argv(values)
            self.app.remember_feature_values(self.feature, values)
            self.app.launch_feature(self.feature, values)
        except Exception as exc:
            self.notify(str(exc), title="Cannot launch", severity="error", timeout=8)


class ProjectionMappingApp(App):
    TITLE = "ProjectionMapping // Visual Madness Console"
    CSS = CSS
    BINDINGS = [
        Binding("escape", "stop_or_back", "Stop visual"),
        Binding("r", "refresh_status", "Refresh"),
        Binding("l", "show_log", "Refresh log"),
        Binding("c", "copy_log", "Copy full log"),
        Binding("o", "open_log", "Open log"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, registry_path: str | None = None):
        super().__init__()
        self.registry = load_registry(registry_path)
        self.feature_by_item_id: dict[str, Feature] = {}
        self.launcher = FeatureLauncher()
        self._feature_values: dict[str, dict[str, Any]] = {
            feature.id: feature.defaults() for feature in self.registry.features
        }
        self._last_state_text = ""
        self._last_log_text = ""

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with VerticalScroll(id="sidebar"):
                yield Static(f"FEATURES // {current_platform().upper()}", classes="feature-title")
                for category in self.registry.categories:
                    yield Static(category, classes="category")
                    items = []
                    for feature in self.registry.features:
                        if feature.category != category:
                            continue
                        item_id = f"feature-{feature.id.replace('_', '-')}"
                        self.feature_by_item_id[item_id] = feature
                        if not feature.supported_on():
                            suffix = "  [unsupported]"
                        elif feature.missing_commands():
                            suffix = f"  [missing: {', '.join(feature.missing_commands())}]"
                        elif feature.missing_modules():
                            suffix = f"  [missing py: {', '.join(feature.missing_modules())}]"
                        else:
                            suffix = ""
                        items.append(ListItem(Label(feature.name + suffix), id=item_id))
                    yield ListView(*items)
            with Vertical(id="detail"):
                yield Static("VISUAL MADNESS CONTROL DECK", classes="feature-title")
                yield Static(
                    "Choose a feature on the left. Configure it, launch it fullscreen on the projector, "
                    "press ESC to return, mutate parameters, and launch again.",
                    classes="feature-description",
                )
                yield Static("Idle", id="status", classes="status-idle")
                yield Button("STOP ACTIVE VISUAL", id="stop", variant="error", disabled=True)
                with Horizontal(id="log-actions"):
                    yield Button("COPY FULL LOG", id="copy-log")
                    yield Button("OPEN LOG FILE", id="open-log")
                yield Static("No run log yet.", id="log-path")
                yield Static("No run log yet.", id="log")
                yield Static(
                    "Logs stream here live and the complete log is persisted to the path above. "
                    "Neural model download/load/warmup stages are mirrored in the RUNNING status line. "
                    "Keyboard: ESC stop tree · C copy full log · O open log · L refresh · R refresh · Q quit.",
                    classes="hint",
                )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.35, self._poll_child)
        self._refresh_status()
        self._refresh_log(force=True)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id is None:
            return
        feature = self.feature_by_item_id.get(event.item.id)
        if feature is not None:
            self.push_screen(ConfigScreen(feature, self._feature_values.get(feature.id)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stop":
            self.stop_active()
        elif event.button.id == "copy-log":
            self.action_copy_log()
        elif event.button.id == "open-log":
            self.action_open_log()

    def remember_feature_values(self, feature: Feature, values: dict[str, Any]) -> None:
        self._feature_values[feature.id] = dict(values)

    def launch_feature(self, feature: Feature, values: dict[str, Any]) -> None:
        self.remember_feature_values(feature, values)
        state = self.launcher.launch(feature, values)
        self.notify(
            f"Started {feature.name} (PID {state.pid}). Live output is shown in the log panel.",
            title="Launched",
            timeout=5,
        )
        self._last_log_text = ""
        self._refresh_status()
        self._refresh_log(force=True)

    def stop_active(self) -> None:
        state = self.launcher.poll()
        if state.running:
            self.launcher.stop()
            self.notify(f"Stopped {state.feature_name} and child process tree", title="Visual stopped", timeout=4)
        self._refresh_status()
        self._refresh_log(force=True)

    def _poll_child(self) -> None:
        previous_running = self.launcher.state.running
        self.launcher.poll()
        self._refresh_log()
        if previous_running and not self.launcher.state.running:
            state = self.launcher.state
            self._refresh_log(force=True)
            if state.returncode not in (0, None):
                self.notify(
                    f"{state.feature_name} failed with exit {state.returncode}. See live log below.",
                    title="Visual failed",
                    severity="error",
                    timeout=10,
                )
            else:
                self.notify(
                    f"{state.feature_name} returned to console (exit {state.returncode})",
                    title="Back from projector",
                    timeout=5,
                )
        self._refresh_status()

    @staticmethod
    def _latest_runtime_stage(log_text: str) -> str | None:
        for line in reversed(log_text.splitlines()):
            marker = "[neural] stage="
            if marker not in line:
                continue
            value = line.split(marker, 1)[1].strip().split()[0]
            return value.replace("-", " ").upper()
        return None

    def _refresh_status(self) -> None:
        status = self.query_one("#status", Static)
        stop = self.query_one("#stop", Button)
        state = self.launcher.poll()
        if state.running:
            stage = self._latest_runtime_stage(self.launcher.read_log_tail())
            stage_text = f"  |  NEURAL {stage}" if stage else ""
            text = f"RUNNING  {state.feature_name}  |  PID {state.pid}{stage_text}  |  started {state.started_at}"
            status.set_classes("status-running")
            stop.disabled = False
        elif state.feature_name:
            text = f"IDLE  |  last: {state.feature_name}  |  exit {state.returncode}"
            status.set_classes("status-error" if state.returncode not in (0, None) else "status-idle")
            stop.disabled = True
        else:
            text = "IDLE  |  choose a feature and unleash it"
            status.set_classes("status-idle")
            stop.disabled = True
        if text != self._last_state_text:
            status.update(text)
            self._last_state_text = text

    def _refresh_log(self, force: bool = False) -> None:
        state = self.launcher.state
        path_text = f"Full log: {state.log_path}" if state.log_path else "No run log yet."
        self.query_one("#log-path", Static).update(path_text)
        text = self.launcher.read_log_tail()
        if force or text != self._last_log_text:
            self.query_one("#log", Static).update(text)
            self._last_log_text = text

    def _copy_text_to_clipboard(self, text: str) -> bool:
        candidates: list[tuple[list[str], bool]] = []
        if os.name == "nt":
            candidates.append((["clip"], True))
        elif current_platform() == "macos":
            candidates.append((["pbcopy"], True))
        else:
            candidates.extend([
                (["wl-copy"], True),
                (["xclip", "-selection", "clipboard"], True),
                (["xsel", "--clipboard", "--input"], True),
            ])
        for argv, use_stdin in candidates:
            if shutil.which(argv[0]) is None:
                continue
            try:
                subprocess.run(
                    argv,
                    input=text if use_stdin else None,
                    text=True,
                    timeout=3.0,
                    check=True,
                )
                return True
            except Exception:
                continue
        return False

    def action_copy_log(self) -> None:
        if self.launcher.state.log_path is None:
            self.notify("No run log yet.", title="Nothing to copy", severity="warning", timeout=4)
            return
        text = self.launcher.read_log()
        if self._copy_text_to_clipboard(text):
            self.notify("Full log copied to clipboard.", title="Copied", timeout=4)
        else:
            self.notify(
                "No clipboard helper found. Install wl-clipboard (Wayland) or xclip/xsel (X11), "
                "or use OPEN LOG FILE.",
                title="Clipboard unavailable",
                severity="warning",
                timeout=8,
            )

    def action_open_log(self) -> None:
        path = self.launcher.state.log_path
        if path is None or not path.exists():
            self.notify("No run log yet.", title="Nothing to open", severity="warning", timeout=4)
            return
        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif current_platform() == "macos":
                subprocess.Popen(["open", str(path)])
            else:
                opener = shutil.which("xdg-open")
                if opener is None:
                    raise RuntimeError("xdg-open not found")
                subprocess.Popen([opener, str(path)])
            self.notify(str(path), title="Opened log", timeout=4)
        except Exception as exc:
            self.notify(f"Could not open log: {exc}\n{path}", title="Open log failed", severity="error", timeout=8)

    def action_stop_or_back(self) -> None:
        if self.launcher.poll().running:
            self.stop_active()

    def action_refresh_status(self) -> None:
        self._refresh_status()
        self._refresh_log(force=True)

    def action_show_log(self) -> None:
        self._refresh_log(force=True)

    def on_unmount(self) -> None:
        self.launcher.close()


def main() -> None:
    ProjectionMappingApp().run()


if __name__ == "__main__":
    main()
