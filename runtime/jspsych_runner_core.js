/** Generic jsPsych timeline runner (plugin-agnostic). */
window.JsPsychRunnerCore = (() => {
  const PLUGIN_CTORS = {
    "html-keyboard-response": () =>
      typeof jsPsychHtmlKeyboardResponse !== "undefined" ? jsPsychHtmlKeyboardResponse : null,
    "html-button-response": () =>
      typeof jsPsychHtmlButtonResponse !== "undefined" ? jsPsychHtmlButtonResponse : null,
  };

  const REVIVE_KEYS = ["on_finish", "on_start", "on_load", "stimulus"];

  function decodeB64Json(b64) {
    return JSON.parse(atob(b64));
  }

  function reviveCallback(obj, key) {
    if (typeof obj[key] === "string" && obj[key].trim().startsWith("function")) {
      obj[key] = eval("(" + obj[key] + ")");
    }
  }

  function buildTypeMap(pluginNames) {
    const typeMap = {};
    for (const name of pluginNames) {
      const ctorFactory = PLUGIN_CTORS[name];
      if (ctorFactory) {
        typeMap[name] = ctorFactory();
      }
    }
    return typeMap;
  }

  function prepareTimeline(rawTimeline, pluginNames) {
    const typeMap = buildTypeMap(pluginNames);
    return rawTimeline.map((trial) => {
      const t = { ...trial };
      if (typeof t.type === "string" && typeMap[t.type]) {
        t.type = typeMap[t.type];
      }
      for (const key of REVIVE_KEYS) {
        reviveCallback(t, key);
      }
      return t;
    });
  }

  function assertJsPsychLoaded() {
    if (typeof initJsPsych !== "function") {
      const err = document.createElement("div");
      err.style.color = "#b91c1c";
      err.style.fontWeight = "600";
      err.textContent = "Failed to load jsPsych runtime scripts.";
      document.body.appendChild(err);
      throw new Error("initJsPsych is unavailable; script CDN load failed.");
    }
  }

  function renderResultsCharts(rows, config) {
    if (!config.show_results_charts || !window.JsPsychDemoCharts) return;
    const task = config.results_task_filter;
    const filtered = task
      ? rows.filter((r) => r && r.task === task)
      : rows;
    window.JsPsychDemoCharts.mount(filtered);
  }

  function createJsPsych(config) {
    const jsPsych = initJsPsych({
      display_element: config.display_element || "jspsych-target",
      on_finish: () => {
        const rows = jsPsych.data.get().values();
        postResultsToParent(rows, config.results_message_type || "jspsych-results");
        renderResultsCharts(rows, config);
      },
    });
    // jsPsych v7: no global `jsPsych`; expose instance for eval'd trial callbacks.
    window.__jsPsychInstance = jsPsych;
    return jsPsych;
  }

  function postResultsToParent(rows, messageType) {
    try {
      window.parent.postMessage({ type: messageType, rows }, "*");
    } catch (e) {
      // Ignore postMessage failures in non-iframe contexts.
    }
  }

  function armDisplayFocus(root) {
    if (!root) return;
    root.setAttribute("tabindex", "0");
    let inputArmed = false;
    window.addEventListener("pointerdown", () => {
      inputArmed = true;
      root.focus();
    });
    return { root, getArmed: () => inputArmed, setArmed: (v) => { inputArmed = v; } };
  }

  function installArrowKeyPolicy(focusState) {
    const isArrow = (k) => k === "ArrowLeft" || k === "ArrowRight";
    const handler = (e) => {
      if (!focusState.getArmed()) return;
      if (isArrow(e.key)) {
        e.stopPropagation();
        e.preventDefault();
      }
    };
    window.addEventListener("keydown", handler, { passive: false });
    window.addEventListener("keyup", handler, { passive: false });
  }

  function runPrepared(jsPsych, timeline) {
    jsPsych.run(timeline);
  }

  function start(config, timelineB64) {
    assertJsPsychLoaded();
    const rawTimeline = decodeB64Json(timelineB64);
    const timeline = prepareTimeline(rawTimeline, config.plugins || []);
    const jsPsych = createJsPsych(config);
    const root = document.getElementById(config.display_element || "jspsych-target");
    const focusState = armDisplayFocus(root);
    if (config.input_arrow_keys) {
      installArrowKeyPolicy(focusState);
    }
    runPrepared(jsPsych, timeline);
  }

  return {
    decodeB64Json,
    prepareTimeline,
    assertJsPsychLoaded,
    createJsPsych,
    postResultsToParent,
    renderResultsCharts,
    armDisplayFocus,
    installArrowKeyPolicy,
    runPrepared,
    start,
  };
})();
