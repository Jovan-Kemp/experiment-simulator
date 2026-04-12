from __future__ import annotations

import urllib.parse

# Canvas motion previews: jsPsych-style RDK logic in the browser (iframe), no PsychoPy.


def _label_seed(label: str) -> int:
    return sum(ord(ch) for ch in label) & 0x7FFFFFFF


def motion_coherence_preview_iframe_src(
    coherence: float,
    *,
    instance_label: str,
    n_dots: int = 20,
    width: int = 220,
    height: int = 140,
    duration_s: float = 5.0,
    seed: int = 42,
) -> str:
    """Return a ``data:`` URL for an iframe ``src`` with embedded Canvas + JS."""
    c = max(0.0, min(1.0, float(coherence)))
    # Escape for embedding in single-quoted or minimal contexts; data URL uses quote().
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>body{{margin:0;background:#ffffff;overflow:hidden}}canvas{{display:block}}</style></head>
<body>
<canvas id="cv" width="{width}" height="{height}"></canvas>
<script>
(function() {{
  const W = {width}, H = {height}, N = {int(n_dots)}, coherence = {c};
  const durationMs = {int(round(float(duration_s) * 1000))};
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
  const xmin = inset + r;
  const xmax = W - inset - r;
  const ymin = inset + r;
  const ymax = H - inset - r;
  const xrng = Math.max(0.0001, xmax - xmin);
  const yrng = Math.max(0.0001, ymax - ymin);
  const nSignal = Math.round(N * coherence);
  const dots = [];
  for (let i = 0; i < N; i++) {{
    dots.push({{ x: xmin + rnd() * xrng, y: ymin + rnd() * yrng, vx: 0, vy: 0, signal: i < nSignal }});
  }}
  for (let i = 0; i < N; i++) {{
    if (dots[i].signal) {{
      dots[i].vx = 1; dots[i].vy = 0;
    }} else {{
      const ang = rnd() * Math.PI * 2;
      dots[i].vx = Math.cos(ang);
      dots[i].vy = Math.sin(ang);
    }}
  }}
  const initial = dots.map(function(d) {{ return {{ x: d.x, y: d.y }}; }});
  const speed = 2.2;
  const canvas = document.getElementById('cv');
  const ctx = canvas.getContext('2d');
  let t0 = performance.now();
  function wrapToroidal(v, lo, span) {{
    return lo + ((v - lo) % span + span) % span;
  }}
  function step(now) {{
    if (now - t0 >= durationMs) {{
      t0 = now;
      for (let i = 0; i < N; i++) {{
        dots[i].x = initial[i].x;
        dots[i].y = initial[i].y;
      }}
    }}
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.beginPath();
    ctx.rect(inset, inset, W - 2 * inset, H - 2 * inset);
    ctx.clip();
    ctx.fillStyle = '#000000';
    for (const d of dots) {{
      d.x = wrapToroidal(d.x + d.vx * speed, xmin, xrng);
      d.y = wrapToroidal(d.y + d.vy * speed, ymin, yrng);
      ctx.beginPath();
      ctx.arc(d.x, d.y, r, 0, Math.PI * 2);
      ctx.fill();
    }}
    ctx.restore();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.strokeRect(inset + 0.5, inset + 0.5, W - 2 * inset - 1, H - 2 * inset - 1);
    requestAnimationFrame(step);
  }}
  requestAnimationFrame(step);
}})();
</script>
</body></html>"""
    return "data:text/html;charset=utf-8," + urllib.parse.quote(html, safe="")


def motion_coherence_preview_iframe_html(
    coherence: float,
    *,
    instance_label: str,
    n_dots: int = 20,
    width: int = 220,
    height: int = 140,
    duration_s: float = 5.0,
    seed: int = 42,
) -> str:
    """HTML fragment: iframe pointing at Canvas preview (for ``mo.Html``)."""
    src = motion_coherence_preview_iframe_src(
        coherence,
        instance_label=instance_label,
        n_dots=n_dots,
        width=width,
        height=height,
        duration_s=duration_s,
        seed=seed,
    )
    w = width + 12
    h = height + 12
    return (
        f'<iframe title="motion coherence {instance_label}" '
        f'src="{src}" width="{w}" height="{h}" '
        f'style="border:none;border-radius:4px" '
        f'sandbox="allow-scripts"></iframe>'
    )
