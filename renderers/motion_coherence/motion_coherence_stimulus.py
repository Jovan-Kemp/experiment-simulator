# Motion-coherence stimulus HTML for marimo previews and jsPsych trial presentation.
# Python builds canvas markup; animation and layout live in ``motion_coherence.js`` / ``.css``.
# Paired with ``experiments/coherence_demo/motion_stimulus_plugin.py`` for jsPsych trials.

from __future__ import annotations

import html
import urllib.parse
from functools import lru_cache
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _motion_coherence_js() -> str:
    return (_PACKAGE_DIR / "motion_coherence.js").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _motion_coherence_css() -> str:
    return (_PACKAGE_DIR / "motion_coherence.css").read_text(encoding="utf-8")


def _label_seed(label: str) -> int:
    return sum(ord(ch) for ch in label) & 0x7FFFFFFF


def _trial_seed(seed: int, trial_id: str) -> int:
    return int(seed) + (sum(ord(ch) for ch in trial_id) & 0x7FFFFFFF)


def motion_coherence_preview_iframe_src(
    stim_level: float,
    *,
    instance_label: str,
    n_dots: int = 20,
    width: int = 220,
    height: int = 140,
    seed: int = 42,
    speed_px_s: float = 120.0,
    dot_lifetime_s: float = 0.1,
) -> str:
    """Self-contained preview document using the shared motion_coherence assets."""
    c = max(0.0, min(1.0, float(stim_level)))
    lifetime = max(0.001, float(dot_lifetime_s))
    preview_seed = int(seed) + _label_seed(instance_label)
    css = _motion_coherence_css()
    js = _motion_coherence_js()
    doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body class="motion-coherence-preview">
<div class="motion-coherence-stimulus">
  <canvas
    id="cv"
    class="motion-coherence-canvas"
    width="{int(width)}"
    height="{int(height)}"
    data-rdk="1"
    data-stim-level="{c}"
    data-dir-sign="1"
    data-seed="{preview_seed}"
    data-n-dots="{int(n_dots)}"
    data-speed-px-s="{float(speed_px_s)}"
    data-dot-lifetime-s="{lifetime}"
    style="width:{int(width)}px;height:{int(height)}px;max-width:{int(width)}px;max-height:{int(height)}px;"
  ></canvas>
</div>
<script>{js}</script>
<script>
(function() {{
  const canvas = document.getElementById("cv");
  if (window.MotionCoherence) {{
    window.MotionCoherence.startMotionCanvas(canvas);
  }}
}})();
</script></body></html>"""
    return "data:text/html;charset=utf-8," + urllib.parse.quote(doc, safe="")


def motion_coherence_preview_iframe_html(
    stim_level: float,
    *,
    instance_label: str,
    n_dots: int = 20,
    width: int = 220,
    height: int = 140,
    seed: int = 42,
    speed_px_s: float = 120.0,
    dot_lifetime_s: float = 0.1,
) -> str:
    src = motion_coherence_preview_iframe_src(
        stim_level,
        instance_label=instance_label,
        n_dots=n_dots,
        width=width,
        height=height,
        seed=seed,
        speed_px_s=speed_px_s,
        dot_lifetime_s=dot_lifetime_s,
    )
    w = width + 12
    h = height + 12
    label_safe = html.escape(instance_label, quote=True)
    return (
        f'<iframe title="motion coherence {label_safe}" '
        f'src="{src}" width="{w}" height="{h}" '
        f'style="border:none;border-radius:4px" '
        f'sandbox="allow-scripts"></iframe>'
    )


def motion_trial_stimulus_html(
    *,
    stim_level: float,
    motion_direction: str,
    trial_id: str,
    width: int = 500,
    height: int = 260,
    n_dots: int = 80,
    seed: int = 42,
    speed_px_s: float = 120.0,
    dot_lifetime_s: float = 0.1,
) -> str:
    """HTML stimulus for jsPsych html-keyboard-response (animated by motion_coherence.js)."""
    c = max(0.0, min(1.0, float(stim_level)))
    direction_sign = -1 if motion_direction == "left" else 1
    tid = urllib.parse.quote(trial_id, safe="")
    trial_seed = _trial_seed(seed, trial_id)
    return f"""
<div class="motion-coherence-stimulus">
  <canvas
    id="rdk-{tid}"
    class="motion-coherence-canvas"
    width="{int(width)}"
    height="{int(height)}"
    data-rdk="1"
    data-stim-level="{c}"
    data-dir-sign="{direction_sign}"
    data-seed="{trial_seed}"
    data-n-dots="{int(n_dots)}"
    data-speed-px-s="{float(speed_px_s)}"
    data-dot-lifetime-s="{max(0.001, float(dot_lifetime_s))}"
    style="width:{int(width)}px;height:{int(height)}px;max-width:{int(width)}px;max-height:{int(height)}px;"
  ></canvas>
</div>
"""
