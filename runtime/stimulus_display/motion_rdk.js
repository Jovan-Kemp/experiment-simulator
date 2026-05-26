/** Motion RDK display: animates canvases emitted by renderers/motion_trial_stimulus_html. */
const motionHandles = new WeakMap();

const DEFAULT_SPEED_PX_S = 120;

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function startCanvasLoop(canvas, state) {
  const { ctx, W, H, inset, xmin, xmax, ymin, ymax, xrng, yrng, dots, speedPxS, r } =
    state;
  let rafId = 0;
  let lastTs = null;

  function wrap(v, lo, span) {
    return lo + (((v - lo) % span) + span) % span;
  }

  function draw(ts) {
    if (!canvas.isConnected) {
      cancelAnimationFrame(rafId);
      motionHandles.delete(canvas);
      return;
    }
    const now = typeof ts === "number" ? ts : performance.now();
    if (lastTs === null) {
      lastTs = now;
    }
    let dt = (now - lastTs) / 1000;
    lastTs = now;
    if (dt > 0.1) {
      dt = 0.1;
    }
    const step = speedPxS * dt;

    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.beginPath();
    ctx.rect(inset, inset, W - 2 * inset, H - 2 * inset);
    ctx.clip();
    ctx.fillStyle = "#000";
    for (const d of dots) {
      d.x = wrap(d.x + d.vx * step, xmin, xrng);
      d.y = wrap(d.y + d.vy * step, ymin, yrng);
      ctx.beginPath();
      ctx.arc(d.x, d.y, r, 0, 2 * Math.PI);
      ctx.fill();
    }
    ctx.restore();
    rafId = requestAnimationFrame(draw);
  }

  rafId = requestAnimationFrame(draw);
  motionHandles.set(canvas, rafId);
}

function startMotionCanvas(canvas) {
  if (motionHandles.has(canvas)) return;

  const W = canvas.width;
  const H = canvas.height;
  const N = Number(canvas.dataset.nDots || "80");
  const stimLevel = Number(canvas.dataset.stimLevel || "0");
  const dirSign = Number(canvas.dataset.dirSign || "1");
  const seed0 = Number(canvas.dataset.seed || "42");
  const speedPxS = Number(canvas.dataset.speedPxS || String(DEFAULT_SPEED_PX_S));
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const rnd = mulberry32(seed0);
  const r = 2;
  const inset = 8;
  const xmin = inset + r;
  const xmax = W - inset - r;
  const ymin = inset + r;
  const ymax = H - inset - r;
  const xrng = Math.max(0.001, xmax - xmin);
  const yrng = Math.max(0.001, ymax - ymin);
  const nSignal = Math.round(N * stimLevel);
  const dots = [];

  for (let i = 0; i < N; i++) {
    dots.push({
      x: xmin + rnd() * xrng,
      y: ymin + rnd() * yrng,
      vx: 0,
      vy: 0,
      signal: i < nSignal,
    });
  }

  for (let i = 0; i < N; i++) {
    if (dots[i].signal) {
      dots[i].vx = dirSign;
      dots[i].vy = 0;
    } else {
      const a = rnd() * Math.PI * 2;
      dots[i].vx = Math.cos(a);
      dots[i].vy = Math.sin(a);
    }
  }

  startCanvasLoop(canvas, {
    ctx,
    W,
    H,
    inset,
    xmin,
    xmax,
    ymin,
    ymax,
    xrng,
    yrng,
    dots,
    speedPxS,
    r,
  });
}

function startAllMotionCanvases(selector = "canvas[data-rdk='1']") {
  document.querySelectorAll(selector).forEach(startMotionCanvas);
}

window.__startAllMotionCanvases = startAllMotionCanvases;
