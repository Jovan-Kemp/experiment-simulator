/** Motion RDK display: animates canvases emitted by renderers/motion_trial_stimulus_html. */
const motionHandles = new WeakMap();

const DEFAULT_SPEED_PX_S = 120;
const DEFAULT_DOT_LIFETIME_S = 0.1;

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function respawnDot(d, rnd, xmin, ymin, xrng, yrng) {
  d.x = xmin + rnd() * xrng;
  d.y = ymin + rnd() * yrng;
  d.age = 0;
}

function dotOutside(d, xmin, xmax, ymin, ymax) {
  return d.x < xmin || d.x > xmax || d.y < ymin || d.y > ymax;
}

function startCanvasLoop(canvas, state) {
  const {
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
    dotLifetimeS,
    r,
    rnd,
  } = state;
  let rafId = 0;
  let lastTs = null;

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
      d.x += d.vx * step;
      d.y += d.vy * step;
      d.age += dt;
      if (d.age >= dotLifetimeS || dotOutside(d, xmin, xmax, ymin, ymax)) {
        respawnDot(d, rnd, xmin, ymin, xrng, yrng);
      }
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
  let dotLifetimeS = Number(
    canvas.dataset.dotLifetimeS || String(DEFAULT_DOT_LIFETIME_S)
  );
  if (!Number.isFinite(dotLifetimeS) || dotLifetimeS <= 0) {
    dotLifetimeS = DEFAULT_DOT_LIFETIME_S;
  }
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
      age: rnd() * dotLifetimeS,
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
    dotLifetimeS,
    r,
    rnd,
  });
}

function startAllMotionCanvases(selector = "canvas[data-rdk='1']") {
  document.querySelectorAll(selector).forEach(startMotionCanvas);
}

window.__startAllMotionCanvases = startAllMotionCanvases;
