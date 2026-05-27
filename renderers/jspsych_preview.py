from __future__ import annotations

import urllib.parse


def _label_seed(label: str) -> int:
    return sum(ord(ch) for ch in label) & 0x7FFFFFFF


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
    c = max(0.0, min(1.0, float(stim_level)))
    lifetime = max(0.001, float(dot_lifetime_s))
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>body{{margin:0;background:#ffffff;overflow:hidden}}canvas{{display:block;width:{width}px;height:{height}px;max-width:{width}px;max-height:{height}px}}</style></head>
<body>
<canvas id="cv" width="{width}" height="{height}"></canvas>
<script>
(function() {{
  const W = {width}, H = {height}, N = {int(n_dots)}, stimLevel = {c};
  const seed = {int(seed)} + {_label_seed(instance_label)};
  function mulberry32(a) {{
    return function() {{
      let t = (a += 0x6d2b79f5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }};
  }}
  const rnd = mulberry32(seed);
  const r = 2.5;
  const inset = 4;
  const xmin = inset + r, xmax = W - inset - r;
  const ymin = inset + r, ymax = H - inset - r;
  const xrng = Math.max(0.0001, xmax - xmin);
  const yrng = Math.max(0.0001, ymax - ymin);
  const nSignal = Math.round(N * stimLevel);
  const dots = [];
  const dotLifetimeS = {lifetime};
  for (let i = 0; i < N; i++) {{
    dots.push({{
      x: xmin + rnd() * xrng, y: ymin + rnd() * yrng,
      vx: 0, vy: 0, signal: i < nSignal, age: rnd() * dotLifetimeS
    }});
  }}
  for (let i = 0; i < N; i++) {{
    if (dots[i].signal) {{ dots[i].vx = 1; dots[i].vy = 0; }}
    else {{
      const ang = rnd() * Math.PI * 2;
      dots[i].vx = Math.cos(ang); dots[i].vy = Math.sin(ang);
    }}
  }}
  const speedPxS = {float(speed_px_s)};
  const canvas = document.getElementById('cv');
  const ctx = canvas.getContext('2d');
  let lastTs = null;
  function respawn(d) {{
    d.x = xmin + rnd() * xrng;
    d.y = ymin + rnd() * yrng;
    d.age = 0;
  }}
  function outside(d) {{
    return d.x < xmin || d.x > xmax || d.y < ymin || d.y > ymax;
  }}
  function step(now) {{
    if (lastTs === null) {{ lastTs = now; }}
    let dt = (now - lastTs) / 1000;
    lastTs = now;
    if (dt > 0.1) {{ dt = 0.1; }}
    const stepDist = speedPxS * dt;
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.beginPath(); ctx.rect(inset, inset, W - 2 * inset, H - 2 * inset); ctx.clip();
    ctx.fillStyle = '#000000';
    for (const d of dots) {{
      d.x += d.vx * stepDist;
      d.y += d.vy * stepDist;
      d.age += dt;
      if (d.age >= dotLifetimeS || outside(d)) {{ respawn(d); }}
      ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, Math.PI * 2); ctx.fill();
    }}
    ctx.restore();
    ctx.strokeStyle = '#000000'; ctx.lineWidth = 1;
    ctx.strokeRect(inset + 0.5, inset + 0.5, W - 2 * inset - 1, H - 2 * inset - 1);
    requestAnimationFrame(step);
  }}
  requestAnimationFrame(step);
}})();
</script></body></html>"""
    return "data:text/html;charset=utf-8," + urllib.parse.quote(html, safe="")


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
    return (
        f'<iframe title="motion coherence {instance_label}" '
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
    """HTML stimulus for jsPsych html-keyboard-response.

    jsPsych handles timing and response collection; this snippet only renders
    the motion canvas animation.
    """
    c = max(0.0, min(1.0, float(stim_level)))
    direction_sign = -1 if motion_direction == "left" else 1
    tid = urllib.parse.quote(trial_id, safe="")
    return f"""
<div style="display:flex;justify-content:center;align-items:center;flex-direction:column;">
  <canvas
    id="rdk-{tid}"
    width="{width}"
    height="{height}"
    data-rdk="1"
    data-stim-level="{c}"
    data-dir-sign="{direction_sign}"
    data-seed="{int(seed) + (sum(ord(ch) for ch in trial_id) & 0x7FFFFFFF)}"
    data-n-dots="{int(n_dots)}"
    data-speed-px-s="{float(speed_px_s)}"
    data-dot-lifetime-s="{max(0.001, float(dot_lifetime_s))}"
    style="width:{int(width)}px;height:{int(height)}px;max-width:{int(width)}px;max-height:{int(height)}px;border:1px solid #000;background:#fff;flex-shrink:0;"
  ></canvas>
</div>
"""

