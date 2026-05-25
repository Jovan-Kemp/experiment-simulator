from __future__ import annotations


def render_srcdoc_iframe(html: str, *, title: str, height: int) -> str:
    """Embed standalone HTML in a marimo-safe iframe srcdoc attribute."""
    srcdoc = html.replace("&", "&amp;").replace('"', "&quot;")
    return (
        f'<iframe title="{title}" srcdoc="{srcdoc}" '
        f'width="100%" height="{int(height)}" '
        'style="border:1px solid #ddd;border-radius:6px;"></iframe>'
    )
