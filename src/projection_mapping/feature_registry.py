from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import importlib.util
import shutil
import sys
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    import tomli as tomllib

from .app_runtime import bundle_root, is_frozen


PARAM_GROUP_ORDER = (
    "System & Input",
    "Output & Resolution",
    "Design Customization",
    "Behavior & Reactivity",
    "Performance & Advanced",
)


def current_platform() -> str:
    """Return the stable platform names used by configs/features.toml."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    return "other"


def _module_install_hint(modules: tuple[str, ...]) -> str:
    """Return the most useful project extra for common optional runtime groups."""
    names = set(modules)
    hints: list[str] = []
    if names & {"moderngl", "glcontext", "glfw"}:
        hints.append("graphics")
    if names & {"rtmlib", "onnxruntime"}:
        hints.append("performer")
    if "mediapipe" in names:
        hints.append("mediapipe")
    if names & {"trimesh"}:
        hints.append("assets3d")
    if names & {"pythonosc", "python_osc"}:
        hints.append("interop")
    if names & {"soundcard"}:
        hints.append("audio")
    if not hints:
        return ""
    extras = ",".join(dict.fromkeys(hints))
    return f"; install with `python -m pip install -e '.[{extras}]'`"


def infer_param_group(key: str, flag: str = "") -> str:
    """Infer a stable UI box for old configs that do not yet declare a group.

    New feature TOML may set ``group = ...`` explicitly. The inference keeps the
    whole existing registry organized immediately instead of requiring every old
    experiment to be edited in lockstep.
    """
    name = f"{key} {flag}".lower().replace("-", "_")

    system_tokens = (
        "source",
        "device",
        "audio",
        "microphone",
        "camera",
        "capture_",
        "input_",
        "loopback",
        "backend",
        "model_path",
    )
    if any(token in name for token in system_tokens):
        return "System & Input"

    output_tokens = (
        "display",
        "render_width",
        "render_height",
        "projector_width",
        "projector_height",
        "output_width",
        "output_height",
        "fullscreen",
    )
    if any(token in name for token in output_tokens):
        return "Output & Resolution"

    behavior_tokens = (
        "reactivity",
        "madness",
        "threshold",
        "sensitivity",
        "smoothing",
        "blend",
        "trail",
        "feedback",
        "charge",
        "cooldown",
        "decay",
        "drive",
    )
    if any(token in name for token in behavior_tokens):
        return "Behavior & Reactivity"

    performance_tokens = (
        "capacity",
        "particles",
        "particle_count",
        "analysis_size",
        "analysis_window",
        "blocksize",
        "steps",
        "iterations",
        "point_count",
        "points",
        "fps",
        "reserve",
        "acceleration",
        "precision",
    )
    if any(token in name for token in performance_tokens):
        return "Performance & Advanced"

    return "Design Customization"


@dataclass(frozen=True)
class FeatureParam:
    key: str
    flag: str
    label: str
    type: str = "text"
    default: Any = ""
    choices: tuple[str, ...] = ()
    min: float | int | None = None
    max: float | int | None = None
    help: str = ""
    group: str = ""

    @property
    def ui_group(self) -> str:
        return self.group.strip() or infer_param_group(self.key, self.flag)

    def coerce(self, value: Any) -> Any:
        if self.type == "bool":
            return bool(value)
        if self.type == "int":
            value = int(value)
        elif self.type == "float":
            value = float(value)
        else:
            value = str(value)

        if self.type in {"int", "float"}:
            if self.min is not None and value < self.min:
                raise ValueError(f"{self.label} must be >= {self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{self.label} must be <= {self.max}")
        if self.type == "choice" and self.choices and value not in self.choices:
            raise ValueError(f"{self.label} must be one of {', '.join(self.choices)}")
        return value


@dataclass(frozen=True)
class Feature:
    id: str
    name: str
    category: str
    description: str
    command: tuple[str, ...]
    fullscreen: bool = False
    params: tuple[FeatureParam, ...] = field(default_factory=tuple)
    platforms: tuple[str, ...] = ()
    requires_commands: tuple[str, ...] = ()
    requires_modules: tuple[str, ...] = ()

    def defaults(self) -> dict[str, Any]:
        return {p.key: p.default for p in self.params}

    def grouped_params(self) -> tuple[tuple[str, tuple[FeatureParam, ...]], ...]:
        buckets: dict[str, list[FeatureParam]] = {}
        for param in self.params:
            buckets.setdefault(param.ui_group, []).append(param)
        order = {name: i for i, name in enumerate(PARAM_GROUP_ORDER)}
        names = sorted(buckets, key=lambda name: (order.get(name, 999), name))
        return tuple((name, tuple(buckets[name])) for name in names)

    def supported_on(self, platform: str | None = None) -> bool:
        platform = platform or current_platform()
        return not self.platforms or platform in self.platforms

    def platform_hint(self) -> str:
        return "all supported OSs" if not self.platforms else ", ".join(self.platforms)

    def missing_commands(self) -> tuple[str, ...]:
        return tuple(command for command in self.requires_commands if shutil.which(command) is None)

    def missing_modules(self) -> tuple[str, ...]:
        missing: list[str] = []
        for module in self.requires_modules:
            try:
                found = importlib.util.find_spec(module) is not None
            except (ImportError, AttributeError, ValueError):
                found = False
            if not found:
                missing.append(module)
        return tuple(missing)

    def available(self, platform: str | None = None) -> bool:
        return self.supported_on(platform) and not self.missing_commands() and not self.missing_modules()

    def availability_hint(self, platform: str | None = None) -> str:
        platform = platform or current_platform()
        if not self.supported_on(platform):
            return f"unsupported on {platform}; supported: {self.platform_hint()}"
        missing = self.missing_commands()
        if missing:
            return f"missing external command(s): {', '.join(missing)}"
        missing_modules = self.missing_modules()
        if missing_modules:
            return (
                f"missing Python module(s): {', '.join(missing_modules)}"
                f"{_module_install_hint(missing_modules)}"
            )
        return "available"

    def build_argv(self, values: dict[str, Any] | None = None) -> list[str]:
        if not self.supported_on():
            raise RuntimeError(
                f"{self.name} is not supported on {current_platform()}; supported: {self.platform_hint()}"
            )
        missing = self.missing_commands()
        if missing:
            raise RuntimeError(
                f"{self.name} requires external command(s) not found on PATH: {', '.join(missing)}"
            )
        missing_modules = self.missing_modules()
        if missing_modules:
            raise RuntimeError(
                f"{self.name} requires Python module(s) not installed in this environment: "
                f"{', '.join(missing_modules)}{_module_install_hint(missing_modules)}"
            )

        values = values or {}
        if self.command and self.command[0] == "python":
            if is_frozen():
                argv = [sys.executable, "--pm-child", *self.command[1:]]
            else:
                argv = [sys.executable, *self.command[1:]]
        else:
            argv = list(self.command)

        for param in self.params:
            value = param.coerce(values.get(param.key, param.default))
            if param.type == "bool":
                if value:
                    argv.append(param.flag)
                continue
            if value == "":
                continue
            argv.extend([param.flag, str(value)])
        return argv


@dataclass(frozen=True)
class FeatureRegistry:
    features: tuple[Feature, ...]

    def by_id(self, feature_id: str) -> Feature:
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        raise KeyError(feature_id)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(feature.category for feature in self.features))


def _default_registry_path() -> Path:
    candidates = [
        bundle_root() / "configs" / "features.toml",
        Path.cwd() / "configs" / "features.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _registry_files(registry_path: Path) -> list[Path]:
    """Return the main registry plus optional configs/features.d/*.toml fragments."""
    files = [registry_path]
    fragments = registry_path.parent / "features.d"
    if fragments.is_dir():
        files.extend(sorted(fragments.glob("*.toml")))
    return files


def load_registry(path: str | Path | None = None) -> FeatureRegistry:
    registry_path = Path(path) if path else _default_registry_path()
    if not registry_path.exists():
        raise FileNotFoundError(f"feature registry not found: {registry_path}")

    raw_features: list[dict[str, Any]] = []
    for file_path in _registry_files(registry_path):
        data = tomllib.loads(file_path.read_text(encoding="utf-8"))
        raw_features.extend(data.get("feature", []))

    features: list[Feature] = []
    seen: set[str] = set()
    for raw in raw_features:
        feature_id = raw["id"]
        if feature_id in seen:
            raise ValueError(f"duplicate feature id: {feature_id}")
        seen.add(feature_id)
        params = tuple(
            FeatureParam(
                key=p["key"],
                flag=p["flag"],
                label=p.get("label", p["key"]),
                type=p.get("type", "text"),
                default=p.get("default", False if p.get("type") == "bool" else ""),
                choices=tuple(p.get("choices", [])),
                min=p.get("min"),
                max=p.get("max"),
                help=p.get("help", ""),
                group=p.get("group", ""),
            )
            for p in raw.get("param", [])
        )
        features.append(
            Feature(
                id=feature_id,
                name=raw["name"],
                category=raw.get("category", "Other"),
                description=raw.get("description", ""),
                command=tuple(raw["command"]),
                fullscreen=bool(raw.get("fullscreen", False)),
                params=params,
                platforms=tuple(raw.get("platforms", [])),
                requires_commands=tuple(raw.get("requires_commands", [])),
                requires_modules=tuple(raw.get("requires_modules", [])),
            )
        )
    return FeatureRegistry(tuple(features))
