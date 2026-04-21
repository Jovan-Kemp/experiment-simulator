from __future__ import annotations

import base64
import json


def _encode_timeline(timeline: list[dict[str, object]]) -> str:
    timeline_json = json.dumps(timeline)
    return base64.b64encode(timeline_json.encode("utf-8")).decode("ascii")


def build_jspsych_runner_html(
    timeline: list[dict[str, object]],
    *,
    title: str = "jsPsych Runtime",
) -> str:
    """Build a standalone jsPsych HTML runner page."""
    # Base64 payload avoids escaping edge cases when embedding timeline in srcdoc.
    timeline_b64 = _encode_timeline(timeline)
    title_safe = title.replace("<", "&lt;").replace(">", "&gt;")
    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>__TITLE_SAFE__</title>
  <link href="https://cdn.jsdelivr.net/npm/jspsych@7.3.4/css/jspsych.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/jspsych@7.3.4/dist/index.browser.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-keyboard-response@1.1.3/dist/index.browser.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-button-response@1.1.3/dist/index.browser.js"></script>
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; font-family: system-ui, sans-serif; }
    #jspsych-target { width: 100%; }
  </style>
</head>
<body>
  <div id="jspsych-target"></div>
  <script>
    const motionHandles = new WeakMap();
    window.__startAllMotionCanvases = () => {
      const canvases = document.querySelectorAll("canvas[data-rdk='1']");
      canvases.forEach((canvas) => {
        if (motionHandles.has(canvas)) return;
        const W = canvas.width;
        const H = canvas.height;
        const N = Number(canvas.dataset.nDots || "80");
        const stimLevel = Number(canvas.dataset.stimLevel || "0");
        const dirSign = Number(canvas.dataset.dirSign || "1");
        const seed0 = Number(canvas.dataset.seed || "42");
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        function mulberry32(a) {
          return function() {
            let t = (a += 0x6d2b79f5);
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
          };
        }
        const rnd = mulberry32(seed0);
        const r = 2;
        const inset = 8;
        const xmin = inset + r, xmax = W - inset - r, ymin = inset + r, ymax = H - inset - r;
        const xrng = Math.max(0.001, xmax - xmin), yrng = Math.max(0.001, ymax - ymin);
        const nSignal = Math.round(N * stimLevel);
        const dots = [];
        for (let i = 0; i < N; i++) {
          dots.push({ x: xmin + rnd() * xrng, y: ymin + rnd() * yrng, vx: 0, vy: 0, signal: i < nSignal });
        }
        for (let i = 0; i < N; i++) {
          if (dots[i].signal) { dots[i].vx = dirSign; dots[i].vy = 0; }
          else {
            const a = rnd() * Math.PI * 2;
            dots[i].vx = Math.cos(a); dots[i].vy = Math.sin(a);
          }
        }
        function wrap(v, lo, span) { return lo + ((v - lo) % span + span) % span; }
        const speed = 2.0;
        let rafId = 0;
        function draw() {
          if (!canvas.isConnected) {
            cancelAnimationFrame(rafId);
            motionHandles.delete(canvas);
            return;
          }
          ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, W, H);
          ctx.save(); ctx.beginPath(); ctx.rect(inset, inset, W - 2 * inset, H - 2 * inset); ctx.clip();
          ctx.fillStyle = "#000";
          for (const d of dots) {
            d.x = wrap(d.x + d.vx * speed, xmin, xrng);
            d.y = wrap(d.y + d.vy * speed, ymin, yrng);
            ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, 2 * Math.PI); ctx.fill();
          }
          ctx.restore();
          rafId = requestAnimationFrame(draw);
        }
        rafId = requestAnimationFrame(draw);
        motionHandles.set(canvas, rafId);
      });
    };
    const typeMap = {
      "html-keyboard-response": (typeof jsPsychHtmlKeyboardResponse !== "undefined")
        ? jsPsychHtmlKeyboardResponse
        : null,
      "html-button-response": (typeof jsPsychHtmlButtonResponse !== "undefined")
        ? jsPsychHtmlButtonResponse
        : null,
    };
    const reviveFn = (obj, key) => {
      if (typeof obj[key] === "string" && obj[key].trim().startsWith("function")) {
        obj[key] = eval("(" + obj[key] + ")");
      }
    };
    const timeline = JSON.parse(atob("__TIMELINE_B64__")).map((t) => {
      if (typeof t.type === "string" && typeMap[t.type]) {
        t.type = typeMap[t.type];
      }
      reviveFn(t, "on_finish");
      reviveFn(t, "on_start");
      reviveFn(t, "on_load");
      reviveFn(t, "stimulus");
      return t;
    });
    if (typeof initJsPsych !== "function") {
      const err = document.createElement("div");
      err.style.color = "#b91c1c";
      err.style.fontWeight = "600";
      err.textContent = "Failed to load jsPsych runtime scripts.";
      document.body.appendChild(err);
      throw new Error("initJsPsych is unavailable; script CDN load failed.");
    }
    const isArrow = (k) => k === "ArrowLeft" || k === "ArrowRight";
    const jsPsych = initJsPsych({
      display_element: "jspsych-target",
      on_finish: () => {
        const rows = jsPsych.data.get().values();
        try {
          window.parent.postMessage({type: "jspsych-results", rows}, "*");
        } catch (e) {}
      }
    });
    const root = document.getElementById("jspsych-target");
    if (root) {
      root.setAttribute("tabindex", "0");
    }
    let inputArmed = false;
    window.addEventListener("pointerdown", () => {
      inputArmed = true;
      if (root) {
        root.focus();
      }
    });
    // Keep arrow-key responses from scrolling the iframe/page.
    window.addEventListener("keydown", (e) => {
      if (!inputArmed) {
        return;
      }
      if (isArrow(e.key)) {
        e.stopPropagation();
        e.preventDefault();
      }
    }, { passive: false });
    window.addEventListener("keyup", (e) => {
      if (!inputArmed) {
        return;
      }
      if (isArrow(e.key)) {
        e.stopPropagation();
        e.preventDefault();
      }
    }, { passive: false });
    window.__startAllMotionCanvases();
    jsPsych.run(timeline);
  </script>
</body>
</html>"""
    return html.replace("__TITLE_SAFE__", title_safe).replace("__TIMELINE_B64__", timeline_b64)

