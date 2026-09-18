from __future__ import annotations

from collections.abc import Iterable

# Four hand-tuned stops per ramp: shadow, body, highlight, hot core.  These are
# intentionally asymmetric and projector-friendly rather than generic HSV rainbows.
PALETTE_STOPS: dict[str, tuple[str, str, str, str]] = {
    "aurora_ice": ("#050818", "#3432a8", "#16d9e3", "#e8fff9"),
    "ember_gold": ("#100307", "#9e1735", "#ff7518", "#fff0a6"),
    "violet_plasma": ("#090316", "#5b20a9", "#e62da6", "#8ed8ff"),
    "toxic_bloom": ("#020c0a", "#087b61", "#86e21d", "#f4ffb0"),
    "ocean_signal": ("#02091c", "#064b9b", "#00b8b5", "#d9f7ff"),
    "rose_quartz": ("#100612", "#7d234f", "#ec6d91", "#ffe0d2"),
    # Existing names remain useful to old configs and saved command lines.
    "spectral": ("#09051d", "#3a46bc", "#12c8c8", "#f0d75d"),
    "electric": ("#030918", "#1545d1", "#11ddff", "#f2fbff"),
    "solar": ("#130405", "#a52513", "#ff9a17", "#fff0a0"),
    "bio": ("#020c08", "#08734d", "#59d72d", "#e8ffad"),
    "ultraviolet": ("#0b0318", "#6520b2", "#e234c3", "#9eb8ff"),
    "icefire": ("#07122a", "#198ec2", "#f4e6d0", "#db3a21"),
    "cyber": ("#070616", "#7225bd", "#00dbe7", "#f5ff8a"),
}

CURATED_PALETTES = (
    "aurora_ice",
    "ember_gold",
    "violet_plasma",
    "toxic_bloom",
    "ocean_signal",
    "rose_quartz",
)


def palette_css(name: str) -> str | None:
    stops = PALETTE_STOPS.get(name)
    if stops is None:
        return None
    return f"linear-gradient(90deg, {', '.join(stops)})"


def palette_swatches(names: Iterable[str]) -> dict[str, str]:
    return {name: css for name in names if (css := palette_css(name)) is not None}


def _rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.removeprefix("#")
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def sample_palette(name: str, position: float) -> tuple[float, float, float]:
    """Sample a curated ramp. Useful for previews and non-GL renderers."""
    stops = PALETTE_STOPS[name]
    position = max(0.0, min(float(position), 1.0))
    scaled = position * (len(stops) - 1)
    index = min(int(scaled), len(stops) - 2)
    blend = scaled - index
    left, right = _rgb(stops[index]), _rgb(stops[index + 1])
    return tuple(a + (b - a) * blend for a, b in zip(left, right))  # type: ignore[return-value]


def glsl_palette_function(names: tuple[str, ...], uniform: str = "u_palette") -> str:
    """Build a GLSL 3.30 piecewise ramp function for an ordered palette list."""

    def vec(hex_color: str) -> str:
        return "vec3(" + ",".join(f"{channel:.6f}" for channel in _rgb(hex_color)) + ")"

    branches: list[str] = []
    for palette_index, name in enumerate(names):
        colors = PALETTE_STOPS[name]
        body = (
            "float x=clamp(t,0.0,1.0)*3.0;"
            f"if(x<1.0) return mix({vec(colors[0])},{vec(colors[1])},x);"
            f"if(x<2.0) return mix({vec(colors[1])},{vec(colors[2])},x-1.0);"
            f"return mix({vec(colors[2])},{vec(colors[3])},x-2.0);"
        )
        prefix = "if" if palette_index == 0 else "else if"
        branches.append(f"{prefix}({uniform}=={palette_index}){{{body}}}")
    return "vec3 pal(float t){" + "".join(branches) + "return vec3(1.0);}"


__all__ = [
    "CURATED_PALETTES",
    "PALETTE_STOPS",
    "glsl_palette_function",
    "palette_css",
    "palette_swatches",
    "sample_palette",
]
