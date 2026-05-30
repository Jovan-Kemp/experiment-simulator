# jsPsych 7 CDN URLs and default plugin registry for the browser runner.
# Maps plugin type strings (e.g. ``html-keyboard-response``) to script URLs and global constructors.
# Imported by ``jspsych_runner`` when assembling participant-facing experiment pages.

from __future__ import annotations

# jsPsych 7 plugin CDN scripts and browser global constructor names.
JSPSYCH_CORE_CSS = "https://cdn.jsdelivr.net/npm/jspsych@7.3.4/css/jspsych.css"
JSPSYCH_CORE_JS = "https://cdn.jsdelivr.net/npm/jspsych@7.3.4/dist/index.browser.js"

JSPSYCH_PLUGIN_CDN: dict[str, str] = {
    "html-keyboard-response": (
        "https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-keyboard-response@1.1.3/dist/index.browser.js"
    ),
    "html-button-response": (
        "https://cdn.jsdelivr.net/npm/@jspsych/plugin-html-button-response@1.1.3/dist/index.browser.js"
    ),
}

JSPSYCH_PLUGIN_GLOBALS: dict[str, str] = {
    "html-keyboard-response": "jsPsychHtmlKeyboardResponse",
    "html-button-response": "jsPsychHtmlButtonResponse",
}

DEFAULT_PLUGINS: tuple[str, ...] = ("html-keyboard-response", "html-button-response")
