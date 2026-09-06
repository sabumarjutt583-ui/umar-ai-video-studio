/* ===========================================================
   Video Editing Bot v10 — frontend logic
   No innerHTML with user/server data anywhere (XSS-safe):
   every dynamic node is built with createElement + textContent.
   =========================================================== */

(() => {
"use strict";

const API = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
const T = window.I18N;

/* ---------------------------- tiny helpers ---------------------------- */
const $ = (id) => document.getElementById(id);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

function on(id, ev, fn) {
  const node = typeof id === "string" ? $(id) : id;
  if (node) node.addEventListener(ev, fn);
}

function el(tag, opts, children) {
  const node = document.createElement(tag);
  if (opts) {
    if (opts.cls) node.className = opts.cls;
    if (opts.text !== undefined) node.textContent = String(opts.text);
    if (opts.title) node.title = opts.title;
    if (opts.attrs) for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
    if (opts.on) for (const [ev, fn] of Object.entries(opts.on)) node.addEventListener(ev, fn);
    if (opts.style) Object.assign(node.style, opts.style);
  }
  (children || []).forEach((c) => c && node.appendChild(c));
  return node;
}

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

function toast(message, kind) {
  const box = $("toasts");
  const node = el("div", { cls: "toast " + (kind || ""), text: message });
  box.appendChild(node);
  setTimeout(() => { node.style.opacity = "0"; }, 4200);
  setTimeout(() => node.remove(), 4700);
}

let busyCount = 0;
function busy(on) {
  busyCount = Math.max(0, busyCount + (on ? 1 : -1));
  let bar = $("busyBar");
  if (busyCount > 0 && !bar) {
    bar = el("div", { cls: "busy-bar", attrs: { id: "busyBar" } });
    document.body.appendChild(bar);
  } else if (busyCount === 0 && bar) bar.remove();
}

function fmtSec(s) {
  s = Math.max(0, Math.round(Number(s) || 0));
  const m = Math.floor(s / 60);
  return (m > 0 ? m + "m " : "") + (s % 60) + "s";
}
function fmtClock(s) {
  s = Number(s) || 0;
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = (s % 60).toFixed(1).padStart(4, "0");
  return mm + ":" + ss;
}

/* ---------------------------- network ---------------------------- */
async function api(path, options) {
  busy(true);
  options = options || {};
  options.headers = options.headers || {};
  if (S.authToken) {
    if (options.headers instanceof Headers) {
      options.headers.set("Authorization", "Bearer " + S.authToken);
    } else {
      options.headers["Authorization"] = "Bearer " + S.authToken;
    }
  }
  try {
    const res = await fetch(API + path, options);
    let data = null;
    const text = await res.text();
    if (text) { try { data = JSON.parse(text); } catch { data = { detail: text }; } }
    if (!res.ok) {
      const detail = (data && (data.detail || data.message)) || res.status + " " + res.statusText;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  } catch (err) {
    if (err instanceof TypeError) throw new Error(T.t("msg_server_down"));
    throw err;
  } finally {
    busy(false);
  }
}

const jpost = (path, body) => api(path, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body || {}),
});
const jdel = (path) => api(path, { method: "DELETE" });
const jget = (path) => api(path, { method: "GET" });
const fpost = (path, formData) => api(path, { method: "POST", body: formData });

/* Kisi element ka text set karta hai (agar wo maujood ho) */
function setText(id, text) {
  const node = $(id);
  if (node) node.textContent = text;
}

/* ---------------------------- state ---------------------------- */
const S = {
  sid: null,
  options: {},
  segments: [],
  media: [],
  customImages: [],
  stickers: [],
  texts: [],
  sfx: [],
  validation: null,
  voiceDuration: 0,
  hasVoice: false,
  hasMusic: false,
  customFontName: null,
  poll: null,
  rendering: false,
  authToken: localStorage.getItem("veb_auth_token") || null,
  user: null,
  isOwner: false,
  activeView: "workflow",
  selectedClipIdx: null,
  audioPlayer: null,
};

const STEPS = ["voice", "timing", "media", "look", "captions", "audio", "overlays", "render"];
const POSITIONS = ["top_left", "top_center", "top_right", "center", "bottom_left", "bottom_center", "bottom_right"];

/* ---------------------------- select builders ---------------------------- */
function fillSelect(select, entries, selected) {
  if (!select) return;
  clear(select);
  entries.forEach(([value, label]) => {
    const opt = el("option", { text: label });
    opt.value = value;
    select.appendChild(opt);
  });
  if (selected !== undefined && selected !== null) select.value = selected;
}

const fromMap = (map) => Object.entries(map || {}).map(([k, v]) => [k, String(v)]);
const fromList = (list) => (list || []).map((v) => [v, prettify(v)]);

function prettify(key) {
  return String(key).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ---------------------------- rail / tabs ---------------------------- */
function buildRail() {
  const rail = $("rail");
  clear(rail);
  STEPS.forEach((step, i) => {
    const card = $("step-" + step);
    const label = card ? card.querySelector(".card-head h2 span:last-child") : null;
    const btn = el("button", {
      attrs: { type: "button", "data-rail": step },
      text: (i + 1) + ". " + (label ? label.textContent : step),
      on: { click: () => card && card.scrollIntoView({ behavior: "smooth", block: "start" }) },
    });
    rail.appendChild(btn);
  });
}

function markRail(step, done) {
  const btn = document.querySelector('[data-rail="' + step + '"]');
  if (btn) btn.classList.toggle("is-done", !!done);
}

function initTabs() {
  $$(".tabs").forEach((group) => {
    const section = group.closest("section");
    group.addEventListener("click", (ev) => {
      const tab = ev.target.closest(".tab");
      if (!tab) return;
      $$(".tab", group).forEach((t2) => t2.classList.toggle("is-active", t2 === tab));
      $$("[data-tabbody]", section).forEach((body) => {
        body.classList.toggle("is-active", body.dataset.tabbody === tab.dataset.tab);
      });
    });
  });
}

/* ---------------------------- boot ---------------------------- */
async function boot() {
  T.setLang(T.detectLang(), onLangChange);
  T.buildLangSelect($("langSelect"), onLangChange);
  applyTheme(localStorage.getItem("veb_theme") || "dark");
  buildRail();
  initTabs();
  wireEvents();

  try {
    const health = await api("/health");
    const ok = health && health.tools && health.tools.ffmpeg && health.tools.ffprobe;
    const badge = $("healthBadge");
    if (badge) {
      badge.textContent = ok ? "FFmpeg ✓" : "FFmpeg ✕";
      badge.className = "badge " + (ok ? "badge-ok" : "badge-err");
    }
    if (!ok) toast(T.t("msg_ffmpeg_missing"), "err");
  } catch (err) {
    const badge = $("healthBadge");
    if (badge) {
      badge.textContent = "offline";
      badge.className = "badge badge-err";
    }
    console.warn("Backend /health check:", err);
  }

  try {
    S.options = await api("/options");
    buildOptionSelects();
  } catch (err) {
    console.warn("Options fetch:", err);
  }

  await checkAuth();

  const saved = localStorage.getItem("veb_session");
  if (saved) {
    try {
      const state = await api("/session/" + saved + "/state");
      S.sid = saved;
      adoptState(state);
    } catch {
      try { await newSession(); } catch {}
    }
  } else {
    try { await newSession(); } catch {}
  }

  if ($("sessionBadge")) $("sessionBadge").textContent = S.sid ? "ID " + S.sid : "Studio Ready";
  restoreSettings();
  updateCaptionPreview();
  addManualRow(); addManualRow();
  try { pollStatus(); } catch {}
}

async function newSession() {
  const res = await jpost("/session/new");
  S.sid = res.session_id;
  localStorage.setItem("veb_session", S.sid);
}

function onLangChange() {
  buildRail();
  renderSegments();
  renderValidation();
  renderStickerChips();
  renderTextChips();
  renderSfxChips();
  buildOptionSelects();
  restoreSettings();
}

function applyTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode === "light" ? "light" : "dark");
  localStorage.setItem("veb_theme", mode);
}

function buildOptionSelects() {
  const o = S.options;
  const keep = (sel) => (sel && sel.value) || undefined;

  fillSelect($("optEffect"), fromList(o.effects), keep($("optEffect")) || "zoom_in_slow");
  fillSelect($("optTransition"), [["cut", "Cut"]].concat(fromMap(o.transitions)), keep($("optTransition")) || "fade");
  fillSelect($("optSpeed"), fromList(o.transition_speeds), keep($("optSpeed")) || "medium");
  fillSelect($("optFilter"), fromMap(o.color_filters), keep($("optFilter")) || "none");
  fillSelect($("optAspect"), fromList(o.aspect_ratios), keep($("optAspect")) || "9:16");
  fillSelect($("optRes"), fromList(o.resolutions), keep($("optRes")) || "1080p");
  fillSelect($("expAspect"), fromList(o.aspect_ratios), keep($("expAspect")) || "1:1");
  fillSelect($("expRes"), fromList(o.resolutions), keep($("expRes")) || "1080p");

  const presets = [["", "— " + T.t("preset") + " —"]].concat(
    Object.entries(o.caption_presets || {}).map(([k, v]) => [k, v.label || prettify(k)])
  );
  fillSelect($("capPreset"), presets, keep($("capPreset")) || "");
  fillSelect($("capMode"), fromList(o.caption_modes), keep($("capMode")) || "line");
  fillSelect($("capFont"), fromMap(o.caption_fonts), keep($("capFont")) || "clean");
  fillSelect($("capAnim"), fromList(o.caption_animations), keep($("capAnim")) || "none");
  fillSelect($("capLang"), [["default", T.t("fmt_auto")]].concat(fromList(o.caption_languages)),
    keep($("capLang")) || "default");

  fillSelect($("sfxKey"), fromMap(o.sound_effects), keep($("sfxKey")));
  fillSelect($("stkKey"), fromMap(o.stickers), keep($("stkKey")));
  fillSelect($("txtFont"), fromMap(o.caption_fonts), keep($("txtFont")) || "bold");

  const posEntries = POSITIONS.map((p) => [p, prettify(p)]);
  fillSelect($("stkPos"), posEntries, keep($("stkPos")) || "top_right");
  fillSelect($("txtPos"), posEntries, keep($("txtPos")) || "top_center");
}

/* ---------------------------- settings persistence ---------------------------- */
const SETTING_IDS = ["optEffect", "optTransition", "optSpeed", "optFilter", "optAspect", "optRes",
  "capEnabled", "capMode", "capFont", "capSize", "capColor", "capHighlight", "capPosition",
  "capAnim", "capMargin", "capMaxChars", "capOutline", "capBox", "capBold", "capCaps", "capLang",
  "musicVol", "vidAudioMode", "vidAudioVol", "vidTrimMode", "ducking", "musicFade", "smartTriggers",
  "expAspect", "expRes", "expFit", "manualMode"];

function collectSettings() {
  const out = {};
  SETTING_IDS.forEach((id) => {
    const node = $(id);
    if (!node) return;
    out[id] = node.type === "checkbox" ? node.checked : node.value;
  });
  return out;
}

function applySettings(values) {
  Object.entries(values || {}).forEach(([id, value]) => {
    const node = $(id);
    if (!node) return;
    if (node.type === "checkbox") node.checked = !!value;
    else node.value = value;
  });
  syncRangeLabels();
  updateManualColumns();
  updateCaptionPreview();
}

function saveSettings() {
  localStorage.setItem("veb_settings", JSON.stringify(collectSettings()));
}

function restoreSettings() {
  try {
    const raw = localStorage.getItem("veb_settings");
    if (raw) applySettings(JSON.parse(raw));
    else { syncRangeLabels(); updateManualColumns(); }
  } catch { syncRangeLabels(); }
}

/* ---------------------------- range labels + caption preview ---------------------------- */
const RANGE_LABELS = [
  ["capSize", "capSizeVal", (v) => v],
  ["capMargin", "capMarginVal", (v) => v],
  ["musicVol", "musicVolVal", (v) => v + "%"],
  ["vidAudioVol", "vidAudioVolVal", (v) => v + "%"],
  ["sfxVol", "sfxVolVal", (v) => v + "%"],
  ["stkScale", "stkScaleVal", (v) => v + "%"],
  ["stkOp", "stkOpVal", (v) => v + "%"],
];

function syncRangeLabels() {
  RANGE_LABELS.forEach(([inputId, labelId, fmt]) => {
    const input = $(inputId), label = $(labelId);
    if (input && label) label.textContent = fmt(input.value);
  });
}

const PREVIEW_FONT_STACK = {
  bold: '"Arial Black", Impact, sans-serif',
  clean: "Arial, Helvetica, sans-serif",
  elegant: "Georgia, serif",
  handwritten: '"Comic Sans MS", cursive',
  impact: "Impact, Haettenschweiler, sans-serif",
  modern: '"Segoe UI", system-ui, sans-serif',
  rounded: "Verdana, Geneva, sans-serif",
  serif: '"Times New Roman", serif',
  urdu: '"Noto Nastaliq Urdu", "Segoe UI", serif',
  arabic: '"Traditional Arabic", "Segoe UI", serif',
  devanagari: '"Nirmala UI", "Segoe UI", sans-serif',
  chinese: '"Microsoft YaHei", SimHei, sans-serif',
};

function updateCaptionPreview() {
  const box = $("capPreview");
  if (!box) return;
  const span = box.querySelector("span") || box.appendChild(el("span"));
  const enabled = $("capEnabled") ? $("capEnabled").checked : true;
  let sample = T.t("preview_sample");
  if ($("capCaps") && $("capCaps").checked) sample = sample.toUpperCase();
  span.textContent = enabled ? sample : T.t("captions_off");

  const size = Number(($("capSize") || {}).value || 64);
  const scaled = Math.max(11, Math.round(size * 0.28));
  const font = ($("capFont") || {}).value || "clean";
  const color = ($("capColor") || {}).value || "#FFFFFF";
  const pos = ($("capPosition") || {}).value || "bottom";
  const outline = $("capOutline") && $("capOutline").checked;
  const boxed = $("capBox") && $("capBox").checked;
  const bold = $("capBold") && $("capBold").checked;

  Object.assign(span.style, {
    fontSize: scaled + "px",
    fontFamily: S.customFontName ? '"' + S.customFontName + '", ' + (PREVIEW_FONT_STACK[font] || "sans-serif")
                                 : (PREVIEW_FONT_STACK[font] || "sans-serif"),
    color: enabled ? color : "var(--text-dim)",
    fontWeight: bold ? "800" : "400",
    textShadow: outline ? "0 0 4px #000, 1px 1px 0 #000, -1px -1px 0 #000" : "none",
    background: boxed ? "rgba(0,0,0,0.55)" : "transparent",
    padding: boxed ? "0.15em 0.4em" : "0",
    borderRadius: boxed ? "6px" : "0",
    direction: T.isRTL() ? "rtl" : "ltr",
  });
  box.style.alignItems = pos === "top" ? "flex-start" : (pos === "middle" ? "center" : "flex-end");
}

/* ---------------------------- session state adoption ---------------------------- */
function adoptState(state) {
  S.segments = state.segments || [];
  S.media = state.manual_media || [];
  S.customImages = state.custom_sticker_images || [];
  S.voiceDuration = state.voice_duration || 0;
  S.hasVoice = !!state.has_voice;
  S.hasMusic = !!state.has_music;
  S.sceneAvailable = !!state.scene_mapping_available;

  setPill("voicePill", S.hasVoice ? T.t("ready") : T.t("not_set"), S.hasVoice ? "ok" : "");
  setPill("musicPill", S.hasMusic ? T.t("ready") : T.t("no_music"), S.hasMusic ? "ok" : "");
  setPill("timingPill", S.segments.length ? S.segments.length + " " + T.t("segments_count") : T.t("not_set"),
    S.segments.length ? "ok" : "");
  renderVoiceParts(state.voice_parts || []);
  renderSegments();
  renderCustomImages();
  markRail("voice", S.hasVoice);
  markRail("timing", S.segments.length > 0);
  S.customFontName = state.custom_font_name || null;
  showCustomFont(S.customFontName);
  if (state.settings && Object.keys(state.settings).length) applySettings(state.settings);
}

function setPill(id, text, kind) {
  const node = $(id);
  if (!node) return;
  node.textContent = text;
  node.className = "pill" + (kind ? " " + kind : "");
  node.removeAttribute("data-i18n");
}

/* ---------------------------- voice ---------------------------- */
function renderVoiceParts(parts) {
  const box = $("voicePartsList");
  if (!box) return;
  clear(box);
  (parts || []).forEach((p, i) => {
    const name = p.filename || p.name || ("part " + (i + 1));
    const meta = fmtClock(p.start || 0) + " → " + fmtClock((p.start || 0) + (p.duration || 0));
    box.appendChild(el("div", { cls: "mini-row" }, [
      el("span", { text: (i + 1) + ". " + name }),
      el("span", { cls: "pill", text: meta }),
    ]));
  });
  if (S.voiceDuration) {
    box.appendChild(el("div", { cls: "mini-row" }, [
      el("span", { text: T.t("timeline") }),
      el("span", { cls: "pill ok", text: fmtSec(S.voiceDuration) }),
    ]));
  }
}

async function uploadVoice(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/upload/voice/" + S.sid, fd);
    S.hasVoice = true;
    S.voiceDuration = res.duration || 0;
    setPill("voicePill", T.t("voice_ready") + " · " + fmtSec(S.voiceDuration), "ok");
    markRail("voice", true);
    renderVoiceParts([]);
    toast(T.t("msg_uploaded"), "ok");
    refreshState();
  } catch (err) { toast(err.message, "err"); }
}

async function uploadVoiceParts(files) {
  if (!files || !files.length) return;
  const fd = new FormData();
  Array.from(files).forEach((f) => fd.append("files", f));
  const gap = encodeURIComponent(($("voiceGap") || {}).value || 0);
  const order = encodeURIComponent(($("voiceOrder") || {}).value || "natural");
  try {
    const res = await fpost("/upload/voice-parts/" + S.sid + "?gap_seconds=" + gap + "&order=" + order, fd);
    S.hasVoice = true;
    S.voiceDuration = res.total_duration || 0;
    setPill("voicePill", T.t("voice_ready") + " · " + fmtSec(S.voiceDuration), "ok");
    markRail("voice", true);
    renderVoiceParts(res.parts || []);
    toast(T.t("msg_uploaded"), "ok");
  } catch (err) { toast(err.message, "err"); }
}

async function refreshState() {
  try {
    const state = await api("/session/" + S.sid + "/state");
    adoptState(state);
  } catch { /* ignore */ }
}

/* ---------------------------- manual timing table ---------------------------- */
function manualMode() { return (($("manualMode") || {}).value) || "duration"; }

function updateManualColumns() {
  const table = $("manualTable");
  if (!table) return;
  const dur = manualMode() === "duration";
  $$(".col-start, .col-end", table).forEach((n) => n.classList.toggle("hide-col", dur));
  $$(".col-dur", table).forEach((n) => n.classList.toggle("hide-col", !dur));
  $$("td.col-start, td.col-end", table).forEach((n) => n.classList.toggle("hide-col", dur));
  $$("td.col-dur", table).forEach((n) => n.classList.toggle("hide-col", !dur));
  updateManualHint();
}

function addManualRow(values) {
  const body = $("manualTable") && $("manualTable").querySelector("tbody");
  if (!body) return;
  const v = values || {};
  const num = el("td", { cls: "rownum" });
  const numInput = (cls, value, step) => el("td", { cls: cls }, [
    el("input", {
      attrs: { type: "number", min: "0", step: step || "0.1", value: value === undefined ? "" : String(value) },
      on: { input: updateManualHint },
    }),
  ]);
  const textCell = el("td", {}, [
    el("input", { attrs: { type: "text", value: v.text || "", placeholder: T.t("text") } }),
  ]);
  const delCell = el("td", {}, [
    el("button", {
      cls: "icon-btn", text: "✕", attrs: { type: "button" },
      on: { click: (ev) => { ev.target.closest("tr").remove(); renumberManual(); } },
    }),
  ]);
  const row = el("tr", {}, [
    num,
    numInput("col-start", v.start),
    numInput("col-end", v.end),
    numInput("col-dur", v.duration),
    textCell,
    delCell,
  ]);
  body.appendChild(row);
  renumberManual();
  updateManualColumns();
}

function renumberManual() {
  const body = $("manualTable") && $("manualTable").querySelector("tbody");
  if (!body) return;
  Array.from(body.rows).forEach((row, i) => { row.cells[0].textContent = String(i + 1); });
  updateManualHint();
}

function readManualRows() {
  const body = $("manualTable") && $("manualTable").querySelector("tbody");
  if (!body) return [];
  const dur = manualMode() === "duration";
  const rows = [];
  Array.from(body.rows).forEach((row) => {
    const start = parseFloat(row.querySelector(".col-start input").value);
    const end = parseFloat(row.querySelector(".col-end input").value);
    const d = parseFloat(row.querySelector(".col-dur input").value);
    const text = row.cells[4].querySelector("input").value;
    if (dur) { if (d > 0) rows.push({ duration: d, text: text }); }
    else if (!isNaN(start) && !isNaN(end) && end > start) rows.push({ start: start, end: end, text: text });
  });
  return rows;
}

function updateManualHint() {
  const hint = $("manualHint");
  if (!hint) return;
  const rows = readManualRows();
  let total = 0;
  if (manualMode() === "duration") rows.forEach((r) => { total += r.duration; });
  else if (rows.length) total = Math.max.apply(null, rows.map((r) => r.end));
  const bits = [rows.length + " " + T.t("segments_count"), T.t("timeline") + " " + fmtSec(total)];
  if (S.voiceDuration) {
    bits.push(T.t("voice_ready") + " " + fmtSec(S.voiceDuration));
    if (Math.abs(total - S.voiceDuration) > 1.0) bits.push("⚠ " + T.t("msg_voice_mismatch"));
  }
  hint.textContent = bits.join(" · ");
}

function loadManualFromSegments() {
  const body = $("manualTable") && $("manualTable").querySelector("tbody");
  if (!body) return;
  if (!S.segments.length) { toast(T.t("no_segments"), "warn"); return; }
  clear(body);
  S.segments.forEach((seg) => addManualRow({
    start: seg.start, end: seg.end,
    duration: Math.round((seg.end - seg.start) * 100) / 100,
    text: seg.text || "",
  }));
}

async function applyManualTable() {
  const rows = readManualRows();
  if (!rows.length) { toast(T.t("no_segments"), "warn"); return; }
  try {
    const res = await jpost("/timestamps/manual/" + S.sid, { rows: rows, mode: manualMode() });
    S.segments = res.segments || [];
    afterTimingChange(res);
    const body = $("manualTable").querySelector("tbody");
    const overlaps = res.overlapping_rows || [];
    Array.from(body.rows).forEach((row, i) => row.classList.toggle("is-overlap", overlaps.indexOf(i + 1) !== -1));
    if (overlaps.length) toast(T.t("msg_overlap") + " " + overlaps.join(", "), "warn");
    if (res.voice_mismatch) toast(T.t("msg_voice_mismatch"), "warn");
  } catch (err) { toast(err.message, "err"); }
}

/* ---------------------------- timing (file / paste / group / scene) ---------------------------- */
function afterTimingChange(res) {
  S.segments = res.segments || S.segments;
  if (res.scene_mapping_available !== undefined) S.sceneAvailable = !!res.scene_mapping_available;
  setPill("timingPill", S.segments.length + " " + T.t("segments_count"), S.segments.length ? "ok" : "");
  markRail("timing", S.segments.length > 0);
  renderSegments();
  updateManualHint();
  refreshSceneInfo();
  toast(T.t("msg_applied"), "ok");
}

async function uploadTimestamps(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try { afterTimingChange(await fpost("/upload/timestamps/" + S.sid, fd)); }
  catch (err) { toast(err.message, "err"); }
}

async function pasteTimestamps() {
  const content = ($("tsPaste") || {}).value || "";
  try {
    afterTimingChange(await jpost("/timestamps/paste/" + S.sid, {
      content: content, format_hint: ($("tsFormat") || {}).value || "auto",
    }));
  } catch (err) { toast(err.message, "err"); }
}

async function regroupSentences() {
  const n = Math.max(1, parseInt(($("groupN") || {}).value, 10) || 1);
  try {
    const res = await jpost("/timestamps/regroup/" + S.sid, { sentences_per_group: n });
    afterTimingChange(res);
    if (res.sentence_count) {
      setText("groupHint", res.sentence_count + " " + T.t("sentences_found") + " → " +
                            res.segment_count + " " + T.t("scenes_word"));
    }
  } catch (err) { toast(err.message, "err"); }
}

/* Live hint: is voice/script mein kitne sentences hain aur N par kitne scenes banenge */
async function refreshSceneInfo() {
  if (!S.sid) return;
  try {
    const res = await jget("/scenes/info/" + S.sid);
    if (!res.has_word_level || !res.sentence_count) return;
    const n = Math.max(1, parseInt(($("groupN") || {}).value, 10) || 1);
    const scenes = (res.preview && res.preview[String(n)]) || Math.ceil(res.sentence_count / n);
    setText("groupHint", res.sentence_count + " " + T.t("sentences_found") + " → " +
                          scenes + " " + T.t("scenes_word"));
  } catch (err) { /* hint hai — chup chaap chhod dein */ }
}

/* ---------- Rasta B: Scene TIME TABLE (paste ya file) — word-level JSON ki zarurat nahi ---------- */
function showSceneTableInfo(res) {
  const box = $("sceneTableInfo");
  if (!box) return;
  clear(box);
  const bits = [res.segment_count + " " + T.t("scenes_word"),
                T.t("timeline") + ": " + fmtSec(res.timeline_duration || 0)];
  if (res.voice_duration) bits.push(T.t("voice") + ": " + fmtSec(res.voice_duration));
  bits.forEach((txt) => box.appendChild(el("span", { text: txt })));
  if (res.skipped_count) {
    box.appendChild(el("span", { cls: "warn", text: T.t("rows_skipped") + ": " + res.skipped_count }));
    (res.skipped_rows || []).slice(0, 5).forEach((msg) => box.appendChild(el("small", { text: msg })));
  }
  (res.warnings || []).slice(0, 5).forEach((msg) => box.appendChild(el("small", { cls: "warn", text: msg })));
  if (res.voice_mismatch) toast(T.t("msg_voice_mismatch"), "warn");
}

async function applySceneTable() {
  const content = ($("sceneTablePaste") || {}).value || "";
  if (!content.trim()) { toast(T.t("paste_empty"), "warn"); return; }
  const btn = $("sceneTableBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await jpost("/scenes/table/paste/" + S.sid, { content: content });
    afterTimingChange(res);
    showSceneTableInfo(res);
  } catch (err) { toast(err.message, "err"); }
  finally { if (btn) btn.disabled = false; }
}

async function uploadSceneTable(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/upload/scenetable/" + S.sid, fd);
    afterTimingChange(res);
    showSceneTableInfo(res);
  } catch (err) { toast(err.message, "err"); }
}

async function uploadSceneMap(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/upload/scenemap/" + S.sid, fd);
    afterTimingChange(res);
    if (res.low_confidence_count) toast("⚠ " + res.low_confidence_count + " scenes: low match confidence", "warn");
  } catch (err) { toast(err.message, "err"); }
}

async function pasteSceneMap() {
  try {
    const res = await jpost("/scenemap/paste/" + S.sid, { content: ($("scenePaste") || {}).value || "" });
    afterTimingChange(res);
    if (res.low_confidence_count) toast("⚠ " + res.low_confidence_count + " scenes: low match confidence", "warn");
  } catch (err) { toast(err.message, "err"); }
}

/* ---------------------------- media ---------------------------- */
async function uploadMedia(files) {
  if (!files || !files.length) return;
  const fileList = Array.from(files);
  const total = fileList.length;
  
  toast(`Starting upload of ${total} file(s)...`, "ok");
  let autoAssignedTotal = 0;
  
  // Group files into small batches (< 25 MB per batch) to avoid Cloudflare 100MB tunnel limit & timeout
  let currentBatch = [];
  let currentBatchSize = 0;
  const batches = [];
  
  for (const f of fileList) {
    if (currentBatch.length > 0 && (currentBatchSize + f.size > 25 * 1024 * 1024 || currentBatch.length >= 5)) {
      batches.push(currentBatch);
      currentBatch = [];
      currentBatchSize = 0;
    }
    currentBatch.push(f);
    currentBatchSize += f.size;
  }
  if (currentBatch.length > 0) batches.push(currentBatch);

  let processedCount = 0;
  for (let b = 0; b < batches.length; b++) {
    const batch = batches[b];
    const fd = new FormData();
    batch.forEach((f) => fd.append("files", f));
    processedCount += batch.length;
    toast(`Uploading files (${processedCount}/${total})...`, "warn");
    try {
      const res = await fpost("/media/manual/" + S.sid, fd);
      S.media = res.all_manual_media || [];
      if (res.segments && res.segments.length) S.segments = res.segments;
      autoAssignedTotal += (res.auto_assigned_count || 0);
      renderSegments();
    } catch (err) {
      toast(`Upload error on batch ${b + 1}: ${err.message}`, "err");
    }
  }
  toast((T.t("msg_auto_assigned") || "Auto-assigned") + " " + autoAssignedTotal + " media file(s)", "ok");
}

async function importZip(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/media/manual/" + S.sid + "/import-zip", fd);
    S.media = res.all_manual_media || [];
    if (res.segments && res.segments.length) S.segments = res.segments;
    renderSegments();
    toast(T.t("msg_auto_assigned") + " " + (res.auto_assigned_count || 0), "ok");
  } catch (err) { toast(err.message, "err"); }
}

async function assignMedia(index, url) {
  const payload = {};
  payload[String(index)] = url || null;
  try {
    const res = await jpost("/media/manual/" + S.sid + "/assign", payload);
    S.segments = res.segments || S.segments;
    renderSegments();
  } catch (err) { toast(err.message, "err"); }
}

function segmentStatusFor(index) {
  if (!S.validation || !S.validation.segment_status) return null;
  return S.validation.segment_status.find((s) => s.segment_index === index) || null;
}

function issuesFor(index) {
  if (!S.validation || !S.validation.issues) return [];
  return S.validation.issues.filter((i) => i.segment_index === index);
}

function renderSegments() {
  const box = $("segmentList");
  if (!box) return;
  clear(box);

  const summary = $("segSummary");
  if (summary) {
    clear(summary);
    const withMedia = S.segments.filter((s) => s.media).length;
    const timeline = S.segments.length ? S.segments[S.segments.length - 1].end : 0;
    [
      S.segments.length + " " + T.t("segments_count"),
      withMedia + " " + T.t("with_media"),
      T.t("timeline") + ": " + fmtSec(timeline),
    ].forEach((txt) => summary.appendChild(el("span", { text: txt })));
  }

  if (!S.segments.length) {
    box.appendChild(el("p", { cls: "hint", text: T.t("no_segments") }));
    setPill("mediaPill", T.t("not_set"), "");
    return;
  }

  const options = [["", "— " + T.t("unassigned") + " —"]].concat(
    S.media.map((m) => [m.url, m.filename + (m.type === "video" ? " 🎬" : " 🖼")])
  );

  S.segments.forEach((seg, i) => {
    const status = segmentStatusFor(i);
    const level = status && status.level && status.level !== "ok" ? status.level : "";
    const thumb = el("div", { cls: "seg-thumb" });
    if (seg.media && seg.media.thumbnail) {
      if (seg.media.type === "video") {
        thumb.appendChild(el("video", { attrs: { src: seg.media.thumbnail, muted: "", playsinline: "" } }));
      } else {
        thumb.appendChild(el("img", { attrs: { src: seg.media.thumbnail, alt: "" } }));
      }
    } else {
      thumb.appendChild(el("span", { text: "—" }));
    }

    const timeCol = el("div", {}, [
      el("div", { cls: "seg-time", text: fmtClock(seg.start) + " → " + fmtClock(seg.end) }),
      el("div", { cls: "seg-time", text: fmtSec(seg.end - seg.start) }),
    ]);

    const textCol = el("div", {}, [
      el("div", { cls: "seg-text", text: (i + 1) + ". " + (seg.text || "—") }),
    ]);
    issuesFor(i).forEach((issue) => {
      textCol.appendChild(el("div", { cls: "seg-issue " + issue.level, text: issueText(issue) }));
    });

    const select = el("select");
    fillSelect(select, options, seg.media ? seg.media.full_url : "");
    select.addEventListener("change", () => assignMedia(i, select.value));
    const actions = el("div", { cls: "seg-actions" }, [select]);

    box.appendChild(el("div", { cls: "seg" + (level ? " level-" + level : ""), }, [thumb, timeCol, textCol, actions]));
  });

  const withMedia = S.segments.filter((s) => s.media).length;
  setPill("mediaPill", withMedia + "/" + S.segments.length + " " + T.t("with_media"),
    withMedia === S.segments.length ? "ok" : (withMedia ? "warn" : "err"));
  markRail("media", withMedia === S.segments.length && S.segments.length > 0);
}

function issueText(issue) {
  let text = T.t("v_" + issue.code, issue.code);
  const d = issue.data || {};
  const extras = Object.keys(d).map((k) => k + ": " + d[k]);
  if (extras.length) text += " (" + extras.join(", ") + ")";
  return "S" + (issue.segment_index >= 0 ? issue.segment_number : "—") + " · " + text;
}

/* ---------------------------- overlays: stickers / images / texts ---------------------------- */
function stickerLabel(key) {
  const map = S.options.stickers || {};
  return map[key] || prettify(key);
}

function addSticker() {
  const key = ($("stkKey") || {}).value;
  const whole = $("stkWhole") && $("stkWhole").checked;
  const start = parseFloat(($("stkStart") || {}).value) || 0;
  const dur = parseFloat(($("stkDur") || {}).value) || 3;
  const item = {
    sticker_key: key,
    position: ($("stkPos") || {}).value || "top_right",
    scale: (parseFloat(($("stkScale") || {}).value) || 22) / 100,
    opacity: (parseFloat(($("stkOp") || {}).value) || 100) / 100,
    whole_video: !!whole,
    times: whole ? [] : [{ start: start, duration: dur }],
  };
  S.stickers.push(item);
  renderStickerChips();
}

function addCustomImageSticker(image) {
  const whole = $("stkWhole") && $("stkWhole").checked;
  const start = parseFloat(($("stkStart") || {}).value) || 0;
  const dur = parseFloat(($("stkDur") || {}).value) || 3;
  S.stickers.push({
    custom_url: image.url,
    label: image.filename,
    thumb: image.url,
    position: ($("stkPos") || {}).value || "top_right",
    scale: (parseFloat(($("stkScale") || {}).value) || 22) / 100,
    opacity: (parseFloat(($("stkOp") || {}).value) || 100) / 100,
    whole_video: !!whole,
    times: whole ? [] : [{ start: start, duration: dur }],
  });
  renderStickerChips();
}

function renderStickerChips() {
  const box = $("stkList");
  if (!box) return;
  clear(box);
  S.stickers.forEach((s, i) => {
    const when = s.whole_video ? T.t("whole_video")
      : (s.times || []).map((t) => fmtClock(t.start) + "+" + t.duration + "s").join(", ");
    const label = (s.custom_url ? (s.label || "image") : stickerLabel(s.sticker_key)) +
      " · " + prettify(s.position) + " · " + Math.round(s.scale * 100) + "% · " + when;
    const children = [];
    if (s.thumb) children.push(el("img", { attrs: { src: s.thumb, alt: "" } }));
    children.push(el("span", { text: label }));
    children.push(el("button", {
      text: "✕", attrs: { type: "button", title: T.t("remove") },
      on: { click: () => { S.stickers.splice(i, 1); renderStickerChips(); } },
    }));
    box.appendChild(el("span", { cls: "chip" }, children));
  });
}

function renderCustomImages() {
  const box = $("customImgList");
  if (!box) return;
  clear(box);
  S.customImages.forEach((img) => {
    box.appendChild(el("span", { cls: "chip" }, [
      el("img", { attrs: { src: img.url, alt: "" } }),
      el("span", { text: img.filename }),
      el("button", {
        text: "+", attrs: { type: "button", title: T.t("add") },
        on: { click: () => addCustomImageSticker(img) },
      }),
    ]));
  });
}

async function uploadOverlayImage(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/overlay/image/" + S.sid, fd);
    S.customImages = res.all_images || [];
    renderCustomImages();
    toast(T.t("msg_uploaded"), "ok");
  } catch (err) { toast(err.message, "err"); }
}

function addCustomText() {
  const value = (($("txtValue") || {}).value || "").trim();
  if (!value) return;
  S.texts.push({
    text: value,
    font: ($("txtFont") || {}).value || "bold",
    color: ($("txtColor") || {}).value || "#FFD166",
    opacity: 1.0,
    font_size: parseInt(($("txtSize") || {}).value, 10) || 48,
    position: ($("txtPos") || {}).value || "top_center",
    start: parseFloat(($("txtStart") || {}).value) || 0,
    duration: parseFloat(($("txtDur") || {}).value) || 3,
    background_box: $("txtBox") ? $("txtBox").checked : true,
  });
  $("txtValue").value = "";
  renderTextChips();
}

function renderTextChips() {
  const box = $("txtList");
  if (!box) return;
  clear(box);
  S.texts.forEach((t, i) => {
    const label = '"' + t.text + '" · ' + prettify(t.position) + " · " +
      fmtClock(t.start) + "+" + t.duration + "s";
    box.appendChild(el("span", { cls: "chip" }, [
      el("span", { text: label, style: { color: t.color } }),
      el("button", {
        text: "✕", attrs: { type: "button", title: T.t("remove") },
        on: { click: () => { S.texts.splice(i, 1); renderTextChips(); } },
      }),
    ]));
  });
}

function addSfx() {
  const key = ($("sfxKey") || {}).value;
  if (!key) return;
  S.sfx.push({
    sfx_key: key,
    start: parseFloat(($("sfxStart") || {}).value) || 0,
    volume: (parseFloat(($("sfxVol") || {}).value) || 50) / 100,
  });
  renderSfxChips();
}

function renderSfxChips() {
  const box = $("sfxList");
  if (!box) return;
  clear(box);
  const labels = S.options.sound_effects || {};
  S.sfx.forEach((s, i) => {
    const label = (labels[s.sfx_key] || prettify(s.sfx_key)) + " @ " + fmtClock(s.start) +
      " · " + Math.round(s.volume * 100) + "%";
    box.appendChild(el("span", { cls: "chip" }, [
      el("span", { text: label }),
      el("button", {
        text: "✕", attrs: { type: "button", title: T.t("remove") },
        on: { click: () => { S.sfx.splice(i, 1); renderSfxChips(); } },
      }),
    ]));
  });
}

/* ---------------------------- validation ---------------------------- */
async function runValidation(silent) {
  if (!S.segments.length) { if (!silent) toast(T.t("no_segments"), "warn"); return null; }
  try {
    const res = await jpost("/media/validate/" + S.sid, {
      aspect_ratio: ($("optAspect") || {}).value || "9:16",
      resolution: ($("optRes") || {}).value || "1080p",
    });
    S.validation = res;
    renderValidation();
    renderSegments();
    return res;
  } catch (err) {
    if (!silent) toast(err.message, "err");
    return null;
  }
}

async function matchTimelineToVoice() {
  try {
    let res = null;
    try {
      res = await jpost("/timeline/match-voice/" + S.sid);
    } catch (apiErr) {
      // Fallback: agar backend server reload na hua ho to /segments/update/ use karein
      const vDur = S.voiceDuration || (S.validation && S.validation.summary && S.validation.summary.voice_duration) || 0;
      if (S.segments && S.segments.length && vDur > 0) {
        const segs = JSON.parse(JSON.stringify(S.segments));
        if (parseFloat(segs[0].start) > 0) segs[0].start = 0;
        for (let i = 0; i < segs.length - 1; i++) {
          const nextStart = parseFloat(segs[i + 1].start || 0);
          const currEnd = parseFloat(segs[i].end || 0);
          if (nextStart > currEnd) {
            segs[i].end = Math.round(nextStart * 100) / 100;
          }
        }
        segs[segs.length - 1].end = Math.round(parseFloat(vDur) * 100) / 100;
        await jpost("/segments/update/" + S.sid, { segments: segs });
        res = { segments: segs };
      } else {
        throw apiErr;
      }
    }

    if (res && res.segments) {
      S.segments = res.segments;
    }

    // Har halat mein validation dobara chalao taake warning turant gayab ho jaye
    const valRes = await jpost("/media/validate/" + S.sid, {
      aspect_ratio: ($("optAspect") || {}).value || "9:16",
      resolution: ($("optRes") || {}).value || "1080p",
    });
    S.validation = valRes;
    S.voiceMatched = true;

    renderSegments();
    renderValidation();
    toast(T.t("msg_voice_matched") || "Timeline matched to voice duration! ✅", "ok");
  } catch (err) {
    toast(err.message, "err");
  }
}

function renderValidation() {
  const box = $("validationPanel");
  if (!box) return;
  clear(box);
  const v = S.validation;
  if (!v) return;
  const s = v.summary || {};

  const head = el("div", { cls: "v-summary" }, [
    el("span", { cls: "pill " + (s.ready ? "ok" : "err"), text: s.ready ? T.t("v_ready") : T.t("v_not_ready") }),
    el("span", { cls: "pill" + (s.errors ? " err" : ""), text: (s.errors || 0) + " " + T.t("v_errors") }),
    el("span", { cls: "pill" + (s.warnings ? " warn" : ""), text: (s.warnings || 0) + " " + T.t("v_warnings") }),
    el("span", { cls: "pill", text: (s.with_media || 0) + "/" + (s.total_segments || 0) + " " + T.t("with_media") }),
    el("span", { cls: "pill", text: T.t("timeline") + " " + fmtSec(s.timeline_duration || 0) }),
  ]);
  box.appendChild(head);

  const hasMismatch = (v.issues || []).some((issue) => issue.code === "timeline_voice_mismatch");

  (v.issues || []).forEach((issue) => {
    const children = [
      el("b", { text: issue.segment_index >= 0 ? "#" + issue.segment_number : "★" }),
      el("span", { text: issueText(issue).replace(/^S[^·]*· /, "") }),
    ];
    if (issue.code === "timeline_voice_mismatch" && issue.data && issue.data.voice > issue.data.timeline) {
      const diff = Math.round((issue.data.voice - issue.data.timeline) * 10) / 10;
      const fixBtn = el("button", {
        cls: "btn btn-primary btn-sm",
        style: { marginLeft: "auto", whiteSpace: "nowrap" },
        text: "⚡ " + (T.t("match_voice") || "Match to voice") + " (+" + diff + "s)",
        attrs: { type: "button" },
        on: { click: (e) => { e.stopPropagation(); matchTimelineToVoice(); } },
      });
      children.push(fixBtn);
    }
    box.appendChild(el("div", { cls: "v-item " + issue.level }, children));
  });

  // Agar timeline voice se match ho chuki hai to green confirmation dikhayein
  if (!hasMismatch && (S.voiceMatched || (s.timeline_duration && s.voice_duration && Math.abs(s.timeline_duration - s.voice_duration) <= 0.5))) {
    box.appendChild(el("div", { cls: "v-item ok" }, [
      el("b", { text: "✓" }),
      el("span", { text: (T.t("v_timeline_voice_matched") || "Timeline matched to voice duration") + " (" + fmtSec(s.timeline_duration || s.voice_duration) + ") ✅" }),
    ]));
  }

  markRail("render", !!s.ready);
}

/* ---------------------------- render ---------------------------- */
function captionPayload() {
  const num = (id, fallback) => {
    const v = parseFloat(($(id) || {}).value);
    return isNaN(v) ? fallback : v;
  };
  const maxChars = parseInt(($("capMaxChars") || {}).value, 10);
  return {
    enabled: $("capEnabled") ? $("capEnabled").checked : true,
    mode: ($("capMode") || {}).value || "line",
    font: ($("capFont") || {}).value || "clean",
    font_size: num("capSize", 64),
    color: ($("capColor") || {}).value || "#FFFFFF",
    highlight_color: ($("capHighlight") || {}).value || "#FFD166",
    position: ($("capPosition") || {}).value || "bottom",
    outline: $("capOutline") ? $("capOutline").checked : true,
    background_box: $("capBox") ? $("capBox").checked : false,
    bold: $("capBold") ? $("capBold").checked : true,
    all_caps: $("capCaps") ? $("capCaps").checked : false,
    animation: ($("capAnim") || {}).value || "none",
    margin_v: num("capMargin", 80),
    max_chars_per_line: isNaN(maxChars) || maxChars <= 0 ? null : maxChars,
    language_mode: ($("capLang") || {}).value || "default",
    custom_font_name: S.customFontName || null,
  };
}

function renderPayload() {
  return {
    effect: ($("optEffect") || {}).value || "zoom_in_slow",
    transition: ($("optTransition") || {}).value || "cut",
    transition_speed: ($("optSpeed") || {}).value || "medium",
    color_filter: ($("optFilter") || {}).value || "none",
    aspect_ratio: ($("optAspect") || {}).value || "9:16",
    resolution: ($("optRes") || {}).value || "1080p",
    captions: captionPayload(),
    music_volume: (parseFloat(($("musicVol") || {}).value) || 0) / 100,
    audio_ducking: $("ducking") ? $("ducking").checked : false,
    music_fade_in_out: $("musicFade") ? $("musicFade").checked : true,
    video_audio_mode: ($("vidAudioMode") || {}).value || "mute",
    video_audio_volume: (parseFloat(($("vidAudioVol") || {}).value) || 0) / 100,
    video_trim_mode: ($("vidTrimMode") || {}).value || "end",
    stickers: S.stickers,
    custom_texts: S.texts,
    sound_effects: S.sfx,
    smart_trigger_enabled: $("smartTriggers") ? $("smartTriggers").checked : false,
    cleanup_temp: true,
    skip_validation: $("skipValidation") ? $("skipValidation").checked : false,
  };
}

async function startRender() {
  if (!S.hasVoice) { toast(T.t("msg_need_voice"), "err"); return; }
  if (!S.segments.length) { toast(T.t("msg_need_timing"), "err"); return; }
  saveSettings();
  try {
    const res = await jpost("/render/" + S.sid, renderPayload());
    if (res.status === "blocked") {
      S.validation = res.validation;
      renderValidation();
      renderSegments();
      toast(T.t("msg_blocked"), "err");
      $("step-render").scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    S.rendering = true;
    $("renderBtn").disabled = true;
    $("cancelBtn").disabled = false;
    clear($("renderLog"));
    if (res.validation) { S.validation = res.validation; renderValidation(); }
    pollStatus();
  } catch (err) { toast(err.message, "err"); }
}

async function cancelRender() {
  try {
    await jpost("/render/cancel/" + S.sid);
    toast(T.t("msg_cancelling"), "warn");
  } catch (err) { toast(err.message, "err"); }
}

const STAGE_KEYS = ["clips", "join", "filter", "captions", "overlays", "voice", "music", "sfx", "finalize"];

function renderStages(state) {
  const list = $("stageList");
  if (!list) return;
  clear(list);
  const planned = state.stages && state.stages.length ? state.stages : STAGE_KEYS;
  const done = state.completed_stages || [];
  planned.forEach((key) => {
    const isDone = done.indexOf(key) !== -1 || state.status === "done";
    const isActive = state.status === "processing" && state.stage === key && !isDone;
    list.appendChild(el("li", { cls: isDone ? "done" : (isActive ? "active" : "") }, [
      el("span", { cls: "dot" }),
      el("span", { text: T.t("stage_" + key, prettify(key)) }),
    ]));
  });
}

function renderLogLines(log) {
  const box = $("renderLog");
  if (!box) return;
  clear(box);
  (log || []).slice(-120).forEach((line) => {
    box.appendChild(el("div", {}, [
      el("span", { cls: "t", text: "[" + line.t + "s] " }),
      el("span", { text: line.message }),
    ]));
  });
  box.scrollTop = box.scrollHeight;
}

function statusPill(status) {
  const map = {
    processing: ["st_processing", "busy"], done: ["st_done", "ok"],
    error: ["st_error", "err"], cancelled: ["st_cancelled", "warn"], idle: ["idle", ""],
  };
  return map[status] || map.idle;
}

async function pollStatus() {
  if (S.poll) { clearTimeout(S.poll); S.poll = null; }
  let state;
  try { state = await api("/render/status/" + S.sid); }
  catch { S.poll = setTimeout(pollStatus, 3000); return; }

  const [key, kind] = statusPill(state.status);
  const pill = $("renderStatus");
  if (pill) { pill.textContent = T.t(key); pill.className = "pill " + kind; pill.removeAttribute("data-i18n"); }

  const pct = Math.max(0, Math.min(100, Number(state.percent) || 0));
  $("progressFill").style.width = pct.toFixed(1) + "%";
  $("progressPct").textContent = pct.toFixed(0) + "%";
  const parts = [];
  if (state.elapsed) parts.push(T.t("elapsed") + " " + fmtSec(state.elapsed));
  if (state.eta) parts.push(T.t("eta") + " " + fmtSec(state.eta));
  $("progressTime").textContent = parts.join(" · ") || "—";

  const msg = $("renderMessage");
  msg.textContent = state.message || T.t("not_started");
  msg.removeAttribute("data-i18n");
  renderStages(state);
  renderLogLines(state.log);

  if (state.validation && !S.validation) { S.validation = state.validation; renderValidation(); }

  if (state.status === "processing") {
    S.rendering = true;
    $("renderBtn").disabled = true;
    $("cancelBtn").disabled = false;
    S.poll = setTimeout(pollStatus, 1200);
    return;
  }

  $("renderBtn").disabled = false;
  $("cancelBtn").disabled = true;
  if (S.rendering && state.status === "done") toast(T.t("msg_render_done"), "ok");
  if (S.rendering && state.status === "error") toast(state.error || state.message, "err");
  S.rendering = false;

  if (state.status === "done" && state.download_url) {
    const card = $("resultCard");
    card.hidden = false;
    $("resultVideo").src = state.download_url;
    const dl = $("downloadBtn");
    dl.href = API + "/download/" + S.sid;
    let meta = [];
    if (state.duration) meta.push(fmtSec(state.duration));
    if (state.size_mb) meta.push(state.size_mb + " MB");
    dl.textContent = T.t("download") + (meta.length ? " (" + meta.join(", ") + ")" : "");
    markRail("render", true);
  }
}

async function quickExport() {
  const btn = $("exportBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await jpost("/render/quick-export/" + S.sid, {
      aspect_ratio: ($("expAspect") || {}).value,
      resolution: ($("expRes") || {}).value,
      fit_mode: ($("expFit") || {}).value,
    });
    const list = $("exportList");
    const link = el("a", {
      cls: "btn btn-ghost btn-sm", text: T.t("download"),
      attrs: { href: res.download_url, download: res.filename },
    });
    list.appendChild(el("div", { cls: "mini-row" }, [
      el("span", { text: res.filename + " · " + res.size_mb + " MB" }), link,
    ]));
    toast(T.t("msg_exported"), "ok");
  } catch (err) { toast(err.message, "err"); }
  finally { if (btn) btn.disabled = false; }
}

/* ---------------------------- custom caption font ---------------------------- */
function showCustomFont(name) {
  const pill = $("capFontPill");
  const clearBtn = $("capFontClear");
  if (pill) { pill.textContent = name || ""; pill.hidden = !name; }
  if (clearBtn) clearBtn.hidden = !name;
}

function clearCustomFont() {
  S.customFontName = null;
  const input = $("capFontFile");
  if (input) input.value = "";
  showCustomFont(null);
  updateCaptionPreview();
  saveSettings();
}

async function uploadCaptionFont(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/upload/font/" + S.sid, fd);
    S.customFontName = res.font_name || null;
    showCustomFont(S.customFontName);
    updateCaptionPreview();
    saveSettings();
    toast(T.t("msg_font_loaded") + " " + (res.font_name || ""), "ok");
  } catch (err) { toast(err.message, "err"); }
}

/* ---------------------------- projects ---------------------------- */
function openProjects(open) {
  const modal = $("projectModal");
  if (!modal) return;
  modal.hidden = !open;
  if (open) loadProjectList();
}

async function loadProjectList() {
  const box = $("projectList");
  if (!box) return;
  clear(box);
  try {
    const res = await api("/project/list");
    const projects = res.projects || [];
    if (!projects.length) {
      box.appendChild(el("p", { cls: "hint", text: T.t("msg_no_projects") }));
      return;
    }
    projects.forEach((p) => {
      const when = p.saved_at ? new Date(p.saved_at * 1000).toLocaleString() : "";
      box.appendChild(el("div", { cls: "mini-row" }, [
        el("span", { text: p.name + " · " + p.segment_count + " " + T.t("segments_count") + (when ? " · " + when : "") }),
        el("span", { cls: "row" }, [
          el("button", {
            cls: "btn btn-ghost btn-sm", text: T.t("load"), attrs: { type: "button" },
            on: { click: () => loadProject(p.name) },
          }),
          el("button", {
            cls: "btn btn-ghost btn-sm btn-danger-ghost", text: T.t("del"), attrs: { type: "button" },
            on: { click: () => deleteProject(p.name) },
          }),
        ]),
      ]));
    });
  } catch (err) { toast(err.message, "err"); }
}

async function saveProject() {
  const name = (($("projectName") || {}).value || "").trim();
  if (!name) return;
  try {
    await jpost("/project/save/" + S.sid, { name: name, settings: collectSettings() });
    toast(T.t("msg_saved"), "ok");
    loadProjectList();
  } catch (err) { toast(err.message, "err"); }
}

async function loadProject(name) {
  try {
    const res = await jpost("/project/load/" + S.sid, { name: name });
    S.segments = res.segments || [];
    S.media = res.manual_media || [];
    S.hasVoice = !!res.has_voice;
    S.hasMusic = !!res.has_music;
    S.voiceDuration = res.voice_duration || 0;
    if (res.settings && Object.keys(res.settings).length) applySettings(res.settings);
    setPill("voicePill", S.hasVoice ? T.t("ready") : T.t("not_set"), S.hasVoice ? "ok" : "");
    setPill("musicPill", S.hasMusic ? T.t("ready") : T.t("no_music"), S.hasMusic ? "ok" : "");
    setPill("timingPill", S.segments.length + " " + T.t("segments_count"), S.segments.length ? "ok" : "");
    markRail("voice", S.hasVoice);
    markRail("timing", S.segments.length > 0);
    renderSegments();
    toast(T.t("msg_loaded"), "ok");
    if (res.missing_files && res.missing_files.length) {
      toast(T.t("msg_missing_files") + " " + res.missing_files.length, "warn");
    }
    openProjects(false);
  } catch (err) { toast(err.message, "err"); }
}

async function deleteProject(name) {
  if (!window.confirm(T.t("msg_confirm_delete") + " " + name)) return;
  try {
    await jdel("/project/" + encodeURIComponent(name));
    toast(T.t("msg_deleted"), "ok");
    loadProjectList();
  } catch (err) { toast(err.message, "err"); }
}

/* ---------------------------- drag & drop ---------------------------- */
/* BUG FIX: pehle `if (!zone || !input) return;` tha — jo inputs kisi .drop zone ke
   andar nahi hain (mediaInput, zipInput, stkImgInput sirf <label class="btn"> me hain)
   unka change listener hi attach nahi hota tha, yani upload button dead tha.
   Ab change listener sirf input hone par lag jata hai; drag&drop handlers tab hi
   lagte hain jab koi zone mile. */
function wireDrop(dropSelectorNode, inputId, handler) {
  const input = $(inputId);
  if (!input) return;
  const zone = dropSelectorNode || null;
  const done = () => { if (zone) zone.classList.add("is-done"); };
  input.addEventListener("change", () => {
    if (input.files && input.files.length) {
      handler(input.multiple ? input.files : input.files[0]);
      done();
    }
    input.value = "";
  });
  if (!zone) return;
  ["dragenter", "dragover"].forEach((ev) => zone.addEventListener(ev, (e) => {
    e.preventDefault(); zone.classList.add("is-over");
  }));
  ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, () => zone.classList.remove("is-over")));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    const files = e.dataTransfer && e.dataTransfer.files;
    if (!files || !files.length) return;
    handler(input.multiple ? files : files[0]);
    zone.classList.add("is-done");
  });
}

/* Sabse qareeb drop zone dhoondte hain; agar input sirf label/section me hai to
   uske container ko drop target bana dete hain (data-drop) taake drag bhi chale. */
function dropZoneOf(inputId) {
  const input = $(inputId);
  if (!input) return null;
  return input.closest(".drop") || input.closest("[data-drop]");
}

/* ---------------------------- events ---------------------------- */
/* ---------------------------- Authentication & Gateway ---------------------------- */
async function checkAuth() {
  try {
    const res = await jget("/auth/me");
    const isAuthenticated = !!(res && res.user);

    // Dynamic Tool Name & Browser Title
    const toolName = (res && res.tool_name) || "Umar AI Video Studio";
    document.title = toolName;
    setText("sidebarToolName", toolName);
    setText("welcomeToolName", toolName);
    setText("authToolName", toolName);
    if ($("adminToolNameInput")) $("adminToolNameInput").value = toolName;

    // Logo image rendering across sidebar, auth screen, and admin preview
    const logoUrl = res && res.logo_url;
    const sidebarImg = $("sidebarCustomLogo");
    const sidebarDefault = $("sidebarDefaultLogo");
    const authImg = $("authCustomLogo");
    const authDefault = $("authDefaultLogo");
    const adminPreview = $("adminLogoPreviewImg");
    const adminFallback = $("adminLogoFallback");

    if (logoUrl) {
      if (sidebarImg) { sidebarImg.src = logoUrl; sidebarImg.style.display = "block"; }
      if (sidebarDefault) sidebarDefault.style.display = "none";
      if (authImg) { authImg.src = logoUrl; authImg.style.display = "block"; }
      if (authDefault) authDefault.style.display = "none";
      if (adminPreview) { adminPreview.src = logoUrl; adminPreview.style.display = "block"; }
      if (adminFallback) adminFallback.style.display = "none";
    } else {
      if (sidebarImg) sidebarImg.style.display = "none";
      if (sidebarDefault) sidebarDefault.style.display = "grid";
      if (authImg) authImg.style.display = "none";
      if (authDefault) authDefault.style.display = "grid";
      if (adminPreview) adminPreview.style.display = "none";
      if (adminFallback) adminFallback.style.display = "grid";
    }

    if (isAuthenticated) {
      S.user = res.user;
      S.isOwner = !!res.is_owner;

      // Update User details
      setText("sidebarUserName", S.user.name);
      setText("welcomeUserName", S.user.name);
      const roleEl = $("sidebarUserRole");
      if (roleEl) {
        roleEl.textContent = S.isOwner ? "Owner" : "User";
        roleEl.className = S.isOwner ? "pill ok" : "pill";
      }

      // Hide Auth Screen, Show App Shell
      if ($("authScreen")) $("authScreen").hidden = true;
      if ($("appShell")) $("appShell").hidden = false;

      // Owner-only triggers
      const logoEditBtn = $("logoUploadTrigger");
      if (logoEditBtn) logoEditBtn.style.display = S.isOwner ? "flex" : "none";
      const ownerLogoCard = $("ownerLogoCard");
      if (ownerLogoCard) ownerLogoCard.style.display = S.isOwner ? "block" : "none";

      // If no active view, land on welcome dashboard
      if (!S.activeView || S.activeView === "welcome") {
        switchView("welcome");
      }
    } else {
      S.user = null;
      S.isOwner = false;
      // Show Auth Screen, Hide App Shell
      if ($("authScreen")) $("authScreen").hidden = false;
      if ($("appShell")) $("appShell").hidden = true;
    }
  } catch (err) {
    console.warn("Auth check error, allowing guest preview:", err);
    // If backend unavailable, allow guest view
    if ($("authScreen")) $("authScreen").hidden = true;
    if ($("appShell")) $("appShell").hidden = false;
    switchView("welcome");
  }
}

function handleGuestAccess() {
  S.user = { name: "Guest User", email: "guest@local", role: "guest" };
  S.isOwner = false;
  if ($("authScreen")) $("authScreen").hidden = true;
  if ($("appShell")) $("appShell").hidden = false;
  setText("sidebarUserName", "Guest User");
  setText("welcomeUserName", "Guest User");
  const roleEl = $("sidebarUserRole");
  if (roleEl) { roleEl.textContent = "Guest"; roleEl.className = "pill"; }
  switchView("welcome");
  toast("Guest preview active.", "ok");
}

async function handleGateSignIn(e) {
  if (e) e.preventDefault();
  const email = ($("gateLoginEmail") || {}).value;
  const password = ($("gateLoginPassword") || {}).value;
  try {
    const res = await jpost("/auth/login", { email, password });
    if (res && res.token) {
      S.authToken = res.token;
      localStorage.setItem("veb_auth_token", res.token);
      S.user = res.user;
      S.isOwner = res.user.role === "owner";
      toast("Welcome, " + res.user.name + "! ✅", "ok");
      await checkAuth();
      switchView("welcome");
    }
  } catch (err) {
    toast(err.message, "err");
  }
}

async function handleGateSignUp(e) {
  if (e) e.preventDefault();
  const name = ($("gateSignupName") || {}).value;
  const email = ($("gateSignupEmail") || {}).value;
  const password = ($("gateSignupPassword") || {}).value;
  try {
    const res = await jpost("/auth/signup", { name, email, password });
    if (res && res.token) {
      S.authToken = res.token;
      localStorage.setItem("veb_auth_token", res.token);
      S.user = res.user;
      S.isOwner = false;
      toast("Account created! Welcome, " + res.user.name + " ✅", "ok");
      await checkAuth();
      switchView("welcome");
    }
  } catch (err) {
    toast(err.message, "err");
  }
}

async function handleQuickCreator() {
  const name = ($("gateQuickName") || {}).value || "Creator";
  try {
    const res = await jpost("/auth/quick-creator", { name });
    if (res && res.token) {
      S.authToken = res.token;
      localStorage.setItem("veb_auth_token", res.token);
      S.user = res.user;
      S.isOwner = false;
      toast("Welcome, " + res.user.name + "! 🚀", "ok");
      await checkAuth();
      switchView("welcome");
    }
  } catch (err) {
    toast(err.message, "err");
  }
}

async function handleQuickOwner() {
  try {
    const res = await jpost("/auth/login", { email: "sabumarjutt583@gmail.com", password: "admin123" });
    if (res && res.token) {
      S.authToken = res.token;
      localStorage.setItem("veb_auth_token", res.token);
      S.user = res.user;
      S.isOwner = true;
      toast("Welcome back, Owner Hafiz Muhammad Umar! 👑", "ok");
      await checkAuth();
      switchView("welcome");
    }
  } catch (err) {
    toast(err.message, "err");
  }
}

function switchGateTab(mode) {
  const tabQuick = $("authGateTabQuick");
  const tabIn = $("authGateTabSignIn");
  const tabUp = $("authGateTabSignUp");
  const formQuick = $("authGateFormQuick");
  const formIn = $("authGateFormSignIn");
  const formUp = $("authGateFormSignUp");

  if (tabQuick) tabQuick.classList.toggle("is-active", mode === "quick");
  if (tabIn) tabIn.classList.toggle("is-active", mode === "signin");
  if (tabUp) tabUp.classList.toggle("is-active", mode === "signup");

  if (formQuick) formQuick.hidden = mode !== "quick";
  if (formIn) formIn.hidden = mode !== "signin";
  if (formUp) formUp.hidden = mode !== "signup";
}

async function handleLogout() {
  try {
    if (S.authToken) await jpost("/auth/logout", { token: S.authToken });
  } catch {}
  S.authToken = null;
  S.user = null;
  S.isOwner = false;
  localStorage.removeItem("veb_auth_token");
  toast("Logged out successfully.", "ok");
  checkAuth();
}

async function handleLogoUpload(file) {
  if (!file) return;
  if (!S.isOwner) {
    toast("Sirf tool ke owner (Hafiz Muhammad Umar) logo tabdeel kar sakte hain.", "err");
    return;
  }
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fpost("/branding/logo", fd);
    toast((res && res.message) || "Logo updated! ✅", "ok");
    checkAuth();
  } catch (err) {
    toast(err.message, "err");
  }
}

async function handleSaveToolName() {
  if (!S.isOwner) {
    toast("Sirf tool ke owner (Hafiz Muhammad Umar) tool ka name tabdeel kar sakte hain.", "err");
    return;
  }
  const name = (($("adminToolNameInput") || {}).value || "").trim();
  if (!name) {
    toast("Tool ka name darj karein.", "warn");
    return;
  }
  try {
    const res = await jpost("/branding/settings", { tool_name: name });
    toast((res && res.message) || "Tool name update ho gaya! ✅", "ok");
    checkAuth();
  } catch (err) {
    toast(err.message, "err");
  }
}

/* ---------------------------- View & Panel Switching ---------------------------- */
function switchView(view) {
  S.activeView = view;
  const panels = {
    welcome: $("panelWelcome"),
    workflow: $("panelWorkflow"),
    editor: $("panelEditor"),
    projects: $("panelProjects"),
  };
  const navs = {
    welcome: $("navItemWelcome"),
    workflow: $("navItemWorkflow"),
    editor: $("navItemEditor"),
    projects: $("navItemProjects"),
  };
  const titles = {
    welcome: "🏠 Dashboard & Studio Overview",
    workflow: "🎛️ Video Creation Studio (Step-by-Step)",
    editor: "🎬 Professional Interactive Timeline Studio",
    projects: "📁 Projects Library & Saved Drafts",
  };

  Object.entries(panels).forEach(([k, p]) => {
    if (p) p.hidden = (k !== view);
  });
  Object.entries(navs).forEach(([k, n]) => {
    if (n) n.classList.toggle("is-active", k === view);
  });

  const titleEl = $("currentViewTitle");
  if (titleEl && titles[view]) titleEl.textContent = titles[view];

  if (view === "editor") {
    renderEditingPanel();
  } else if (view === "projects") {
    loadProjectsFullList();
  }
}

/* ---------------------------- New Project Wizard Modal ---------------------------- */
let selectedProjectAspect = "9:16";

function openNewProjectModal() {
  const modal = $("newProjectModal");
  if (modal) modal.hidden = false;
}

function closeNewProjectModal() {
  const modal = $("newProjectModal");
  if (modal) modal.hidden = true;
}

function selectProjectFormat(aspect) {
  selectedProjectAspect = aspect;
  ["fmtVertical", "fmtLandscape", "fmtSquare"].forEach((id) => {
    const card = $(id);
    if (card) {
      card.classList.toggle("is-active", card.dataset.aspect === aspect);
    }
  });
}

async function launchNewProject() {
  const title = (($("createProjectTitle") || {}).value || "").trim() || "Untitled Project";
  const res = ($("createProjectRes") || {}).value || "1080p";

  // Apply project settings
  if ($("projectName")) $("projectName").value = title;
  if ($("projectInputName")) $("projectInputName").value = title;
  if ($("optAspect")) $("optAspect").value = selectedProjectAspect;
  if ($("optRes")) $("optRes").value = res;
  saveSettings();

  closeNewProjectModal();
  switchView("workflow");

  // Scroll to step 1
  const step1 = $("step-voice");
  if (step1) step1.scrollIntoView({ behavior: "smooth" });
  toast("Project '" + title + "' initialized! Step 1 me voice upload karein.", "ok");
}

async function loadProjectsFullList() {
  const box = $("fullProjectList");
  if (!box) return;
  clear(box);
  try {
    const res = await api("/project/list");
    const projects = res.projects || [];
    if (!projects.length) {
      box.appendChild(el("p", { cls: "hint", text: "Koi project save nahi hai abhi." }));
      return;
    }
    projects.forEach((p) => {
      const when = p.saved_at ? new Date(p.saved_at * 1000).toLocaleString() : "";
      box.appendChild(el("div", { cls: "mini-row", style: { padding: "0.8rem", background: "rgba(0,0,0,0.25)", borderRadius: "8px", border: "1px solid var(--line)" } }, [
        el("div", { style: { display: "flex", flexDirection: "column" } }, [
          el("strong", { text: p.name }),
          el("small", { cls: "hint", text: p.segment_count + " segments · " + when })
        ]),
        el("span", { cls: "row" }, [
          el("button", {
            cls: "btn btn-primary btn-sm", text: "Open & Edit", attrs: { type: "button" },
            on: { click: async () => { await loadProject(p.name); switchView("workflow"); } },
          }),
          el("button", {
            cls: "btn btn-ghost btn-sm btn-danger-ghost", text: "Delete", attrs: { type: "button" },
            on: { click: () => deleteProject(p.name) },
          }),
        ]),
      ]));
    });
  } catch (err) { toast(err.message, "err"); }
}


/* ---------------------------- Dedicated Interactive Editing Panel ---------------------------- */
function renderEditingPanel() {
  const edPill = $("editorTimelinePill");
  const stripMedia = $("stripMedia");
  const stripCaptions = $("stripCaptions");
  const stripVoice = $("stripVoice");
  const stripMusic = $("stripMusic");
  const ruler = $("timelineRuler");

  const totalDur = S.voiceDuration || (S.segments.length ? S.segments[S.segments.length - 1].end : 0);
  if (edPill) {
    edPill.textContent = S.segments.length + " clips · " + fmtSec(totalDur);
  }

  // Ruler markers
  if (ruler) {
    clear(ruler);
    const step = totalDur > 120 ? 30 : (totalDur > 30 ? 10 : 5);
    for (let t = 0; t <= Math.ceil(totalDur || 1); t += step) {
      ruler.appendChild(el("span", {
        style: { flex: "0 0 auto", minWidth: Math.max(step * 14, 40) + "px", borderLeft: "1px solid var(--line)", paddingLeft: "3px" },
        text: fmtClock(t)
      }));
    }
  }

  // Populate Track 1: Media Clips
  if (stripMedia) {
    clear(stripMedia);
    if (!S.segments.length) {
      stripMedia.appendChild(el("span", { cls: "hint", text: "No segments yet." }));
    } else {
      S.segments.forEach((seg, i) => {
        const dur = Math.max(seg.end - seg.start, 0.1);
        const widthPx = Math.max(Math.round(dur * 18), 70);
        const isSelected = S.selectedClipIdx === i;

        const thumb = seg.media && seg.media.thumbnail ?
          el("img", { attrs: { src: seg.media.thumbnail }, style: { width: "100%", height: "28px", objectFit: "cover", borderRadius: "3px" } }) :
          el("span", { cls: "tc-num", text: "#" + (i + 1) });

        const clip = el("div", {
          cls: "t-clip" + (isSelected ? " selected" : ""),
          style: { width: widthPx + "px" },
          on: { click: () => openClipInspector(i) },
        }, [
          thumb,
          el("span", { cls: "tc-dur", text: dur.toFixed(1) + "s" })
        ]);
        stripMedia.appendChild(clip);
      });
    }
  }

  // Populate Track 2: Captions
  if (stripCaptions) {
    clear(stripCaptions);
    if (!S.segments.length) {
      stripCaptions.appendChild(el("span", { cls: "hint", text: "No captions." }));
    } else {
      S.segments.forEach((seg, i) => {
        const dur = Math.max(seg.end - seg.start, 0.1);
        const widthPx = Math.max(Math.round(dur * 18), 70);
        const clip = el("div", {
          cls: "t-clip caption-clip",
          style: { width: widthPx + "px" },
          title: seg.text || "—",
          on: { click: () => openClipInspector(i) },
        }, [
          el("span", { cls: "tc-dur", style: { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }, text: seg.text || ("Clip " + (i + 1)) })
        ]);
        stripCaptions.appendChild(clip);
      });
    }
  }

  // Populate Track 3: Voice Audio Bar
  if (stripVoice) {
    clear(stripVoice);
    if (S.hasVoice && S.voiceDuration > 0) {
      stripVoice.appendChild(el("div", {
        cls: "t-clip voice-bar",
        text: "🎙️ Voice Audio Track (" + fmtSec(S.voiceDuration) + ")"
      }));
    } else {
      stripVoice.appendChild(el("span", { cls: "hint", text: "No voice file uploaded." }));
    }
  }

  // Populate Track 4: Music Track
  if (stripMusic) {
    clear(stripMusic);
    if (S.hasMusic) {
      stripMusic.appendChild(el("div", {
        cls: "t-clip music-bar",
        text: "🎵 Background Music Track"
      }));
    } else {
      stripMusic.appendChild(el("span", { cls: "hint", text: "No background music added." }));
    }
  }
}

function openClipInspector(idx) {
  S.selectedClipIdx = idx;
  const seg = S.segments[idx];
  if (!seg) return;
  const box = $("clipInspector");
  if (!box) return;
  box.hidden = false;

  setText("inspTitle", "Clip #" + (idx + 1) + " Inspector");
  if ($("inspStart")) $("inspStart").value = seg.start;
  if ($("inspEnd")) $("inspEnd").value = seg.end;
  if ($("inspText")) $("inspText").value = seg.text || "";

  // Fill effect select
  const effSel = $("inspEffect");
  if (effSel) {
    fillSelect(effSel, (S.options.effects || []).map((e) => [e, prettify(e)]), seg.effect || "auto");
  }

  // Preview thumbnail
  const preview = $("inspPreview");
  if (preview) {
    clear(preview);
    if (seg.media && seg.media.thumbnail) {
      if (seg.media.type === "video") {
        preview.appendChild(el("video", { attrs: { src: seg.media.thumbnail, muted: "", playsinline: "", autoplay: "", loop: "" } }));
      } else {
        preview.appendChild(el("img", { attrs: { src: seg.media.thumbnail } }));
      }
    } else {
      preview.appendChild(el("p", { cls: "hint", text: "No media assigned to this clip." }));
    }
  }

  renderEditingPanel();
}

function closeClipInspector() {
  S.selectedClipIdx = null;
  const box = $("clipInspector");
  if (box) box.hidden = true;
  renderEditingPanel();
}

async function saveClipChanges() {
  if (S.selectedClipIdx === null || !S.segments[S.selectedClipIdx]) return;
  const seg = S.segments[S.selectedClipIdx];
  const start = parseFloat(($("inspStart") || {}).value) || 0;
  const end = parseFloat(($("inspEnd") || {}).value) || 0;
  const text = (($("inspText") || {}).value || "").trim();
  const effect = ($("inspEffect") || {}).value || "auto";

  if (end <= start) {
    toast("End time must be greater than start time.", "err");
    return;
  }

  seg.start = Math.round(start * 100) / 100;
  seg.end = Math.round(end * 100) / 100;
  seg.text = text;
  seg.effect = effect;

  try {
    await jpost("/segments/update/" + S.sid, { segments: S.segments });
    toast("Clip #" + (S.selectedClipIdx + 1) + " saved! ✅", "ok");
    renderSegments();
    renderEditingPanel();
  } catch (err) {
    toast(err.message, "err");
  }
}

function togglePreviewAudio() {
  if (!S.audioPlayer) {
    S.audioPlayer = new Audio();
  }
  const btn = $("editorPlayAudioBtn");
  if (!S.audioPlayer.paused) {
    S.audioPlayer.pause();
    if (btn) btn.innerHTML = "▶ <span>" + (T.t("play_preview") || "Play Audio") + "</span>";
  } else {
    if (!S.sid || !S.hasVoice) {
      toast("Upload a voice file first.", "warn");
      return;
    }
    S.audioPlayer.src = API + "/files/" + S.sid + "/voice.mp3?t=" + Date.now();
    S.audioPlayer.play().then(() => {
      if (btn) btn.innerHTML = "⏸ <span>Pause</span>";
    }).catch(() => {
      toast("Cannot play audio directly. Check voice file.", "warn");
    });
    S.audioPlayer.onended = () => {
      if (btn) btn.innerHTML = "▶ <span>" + (T.t("play_preview") || "Play Audio") + "</span>";
    };
  }
}

/* ---------------------------- Modular Admin & Diagnostics Drawer ---------------------------- */
function openAdminSidebar() {
  const drawer = $("adminSidebar");
  if (!drawer) return;
  drawer.hidden = false;
  refreshDiagnostics();
}

function closeAdminSidebar() {
  const drawer = $("adminSidebar");
  if (drawer) drawer.hidden = true;
}

function switchDrawerTab(tab) {
  const isAdd = tab === "additions";
  const tabAdd = $("tabAdditions");
  const tabDiag = $("tabDiagnostics");
  const paneAdd = $("paneAdditions");
  const paneDiag = $("paneDiagnostics");

  if (tabAdd) tabAdd.classList.toggle("is-active", isAdd);
  if (tabDiag) tabDiag.classList.toggle("is-active", !isAdd);
  if (paneAdd) paneAdd.hidden = !isAdd;
  if (paneDiag) paneDiag.hidden = isAdd;
}

async function refreshDiagnostics() {
  try {
    const res = await jget("/system/diagnostics");
    if (!res) return;
    const tools = res.tools || {};
    const disk = res.disk || {};

    const ffmpegEl = $("diagMetricFfmpeg");
    if (ffmpegEl) {
      ffmpegEl.textContent = tools.ffmpeg ? "Installed & Ready ✅" : "Missing ❌";
      ffmpegEl.className = tools.ffmpeg ? "ok" : "err";
    }

    const nvencEl = $("diagMetricNvenc");
    if (nvencEl) {
      nvencEl.textContent = tools.nvenc_gpu ? "Supported ⚡" : "CPU Fallback";
      nvencEl.className = tools.nvenc_gpu ? "ok" : "";
    }

    const diskEl = $("diagMetricDisk");
    if (diskEl) {
      diskEl.textContent = (disk.free_gb || 0) + " GB free";
    }

    const cacheEl = $("diagMetricCache");
    if (cacheEl) {
      cacheEl.textContent = (disk.uploads_mb || 0) + " MB";
    }

    const consoleEl = $("diagConsoleLog");
    if (consoleEl) {
      consoleEl.textContent = "[DIAGNOSTICS - " + new Date().toLocaleTimeString() + "]\n" +
        "• Creator / Owner: " + (res.owner_name || "Hafiz Muhammad Umar") + "\n" +
        "• FFmpeg: " + (tools.ffmpeg ? "OK" : "NOT FOUND") + " (ffprobe: " + (tools.ffprobe ? "OK" : "NOT FOUND") + ")\n" +
        "• Hardware NVENC: " + (tools.nvenc_gpu ? "ACTIVE" : "OFF") + "\n" +
        "• Disk Space: " + disk.free_gb + " GB Free / " + disk.total_gb + " GB Total\n" +
        "• Uploads/Cache: " + disk.uploads_mb + " MB in use\n" +
        "• Active Sessions: " + res.active_sessions_count + "\n" +
        "• Registered Accounts: " + res.registered_users_count + "\n" +
        "All diagnostic systems operational.";
    }
  } catch (err) {
    const consoleEl = $("diagConsoleLog");
    if (consoleEl) consoleEl.textContent = "Diagnostics error: " + err.message;
  }
}

function applyStylePreset(presetName) {
  if (presetName === "hormozi") {
    if ($("capFont")) $("capFont").value = "bold";
    if ($("capColor")) $("capColor").value = "#FFFFFF";
    if ($("capHighlight")) $("capHighlight").value = "#FFD166";
    if ($("capAnim")) $("capAnim").value = "pop";
    if ($("optEffect")) $("optEffect").value = "auto";
    toast("Alex Hormozi Style Preset Applied! 🔥", "ok");
  } else if (presetName === "documentary") {
    if ($("capFont")) $("capFont").value = "clean";
    if ($("capColor")) $("capColor").value = "#F4F4F4";
    if ($("capAnim")) $("capAnim").value = "fade";
    if ($("optFilter")) $("optFilter").value = "cinematic";
    toast("Vox Documentary Style Preset Applied! 📜", "ok");
  } else if (presetName === "cashcow") {
    if ($("capFont")) $("capFont").value = "impact";
    if ($("capHighlight")) $("capHighlight").value = "#34D399";
    if ($("optTransition")) $("optTransition").value = "zoom_in";
    toast("Cashcow Faceless Preset Applied! 💰", "ok");
  }
  updateCaptionPreview();
  saveSettings();
}

function wireEvents() {
  on("themeBtn", "click", () => {
    const now = document.documentElement.getAttribute("data-theme");
    applyTheme(now === "light" ? "dark" : "light");
  });
  on("projectBtn", "click", () => openProjects(true));
  on("projectClose", "click", () => openProjects(false));
  on("projectSave", "click", saveProject);
  const modal = $("projectModal");
  if (modal) modal.addEventListener("click", (e) => { if (e.target === modal) openProjects(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") openProjects(false); });

  /* Topbar & Sidebar Navigation */
  on("navItemWelcome", "click", () => switchView("welcome"));
  on("navItemNewProject", "click", openNewProjectModal);
  on("navItemWorkflow", "click", () => switchView("workflow"));
  on("navItemEditor", "click", () => switchView("editor"));
  on("navItemProjects", "click", () => switchView("projects"));
  on("navItemAdmin", "click", openAdminSidebar);
  on("sidebarBtnLogout", "click", handleLogout);

  /* Welcome Dashboard Action Card buttons */
  on("welcomeBtnNewProject", "click", openNewProjectModal);
  on("welcomeBtnTimeline", "click", () => switchView("editor"));
  on("welcomeBtnPresets", "click", () => { openAdminSidebar(); switchDrawerTab("additions"); });
  on("welcomeBtnProjects", "click", () => switchView("projects"));
  on("welcomeBtnDiagnostics", "click", () => { openAdminSidebar(); switchDrawerTab("diagnostics"); });
  on("btnBackToDashboard", "click", () => switchView("welcome"));
  on("editorBackToDashBtn", "click", () => switchView("welcome"));
  on("btnWorkflowToEditor", "click", () => switchView("editor"));
  on("editorBackBtn", "click", () => switchView("workflow"));
  on("btnProjectsNewProject", "click", openNewProjectModal);
  on("btnDirectSaveProject", "click", async () => {
    const inputName = ($("projectInputName") || {}).value;
    if ($("projectName")) $("projectName").value = inputName;
    await saveProject();
    loadProjectsFullList();
  });

  /* Auth Gateway Screen (Login & Signup) */
  on("authGateTabQuick", "click", () => switchGateTab("quick"));
  on("authGateTabSignIn", "click", () => switchGateTab("signin"));
  on("authGateTabSignUp", "click", () => switchGateTab("signup"));
  on("btnQuickCreator", "click", handleQuickCreator);
  on("btnQuickOwner", "click", handleQuickOwner);
  on("authGateFormSignIn", "submit", handleGateSignIn);
  on("authGateFormSignUp", "submit", handleGateSignUp);
  on("btnGuestAccess", "click", handleGuestAccess);

  /* New Project Wizard Modal */
  on("newProjectClose", "click", closeNewProjectModal);
  ["fmtVertical", "fmtLandscape", "fmtSquare"].forEach((id) => {
    const card = $(id);
    if (card) {
      card.addEventListener("click", () => selectProjectFormat(card.dataset.aspect));
    }
  });
  on("btnLaunchStudio", "click", launchNewProject);

  /* Owner Branding Controls */
  on("btnAdminSaveToolName", "click", handleSaveToolName);
  on("btnAdminSaveLogo", "click", () => {
    const input = $("adminLogoFileInput");
    if (input && input.files && input.files[0]) handleLogoUpload(input.files[0]);
    else toast("Select a logo file first.", "warn");
  });
  const adminLogoInput = $("adminLogoFileInput");
  if (adminLogoInput) {
    adminLogoInput.addEventListener("change", () => {
      if (adminLogoInput.files && adminLogoInput.files[0]) handleLogoUpload(adminLogoInput.files[0]);
    });
  }
  on("logoUploadTrigger", "click", () => {
    const input = $("logoFileInput");
    if (input) input.click();
  });
  const logoInput = $("logoFileInput");
  if (logoInput) {
    logoInput.addEventListener("change", () => {
      if (logoInput.files && logoInput.files[0]) handleLogoUpload(logoInput.files[0]);
    });
  }

  /* Interactive Editing Panel controls */
  on("editorPlayAudioBtn", "click", togglePreviewAudio);
  on("editorMatchVoiceBtn", "click", matchTimelineToVoice);
  on("inspClose", "click", closeClipInspector);
  on("inspSaveBtn", "click", saveClipChanges);

  /* Admin & Diagnostics Drawer */
  on("adminSidebarClose", "click", closeAdminSidebar);
  on("adminSidebarOverlay", "click", closeAdminSidebar);
  on("tabAdditions", "click", () => switchDrawerTab("additions"));
  on("tabDiagnostics", "click", () => switchDrawerTab("diagnostics"));
  on("btnRefreshDiagnostics", "click", refreshDiagnostics);
  on("btnQuickFixSync", "click", matchTimelineToVoice);
  on("btnQuickFixCache", "click", () => {
    jpost("/system/repair/clean-cache")
      .then((res) => toast((res && res.message) || "Cache cleaned! ✅", "ok"))
      .then(refreshDiagnostics)
      .catch((err) => toast(err.message, "err"));
  });
  on("btnQuickFixMedia", "click", () => runValidation(false));

  document.querySelectorAll(".preset-pill").forEach((btn) => {
    btn.addEventListener("click", () => applyStylePreset(btn.dataset.preset));
  });


  /* step 1 — voice */
  wireDrop(dropZoneOf("voiceInput"), "voiceInput", uploadVoice);
  wireDrop(dropZoneOf("voicePartsInput"), "voicePartsInput", uploadVoiceParts);

  /* step 2 — timing */
  wireDrop(dropZoneOf("tsInput"), "tsInput", uploadTimestamps);
  on("tsPasteBtn", "click", pasteTimestamps);
  on("manualMode", "change", () => { updateManualColumns(); saveSettings(); });
  on("manualAddRow", "click", () => addManualRow());
  on("manualFromSegs", "click", loadManualFromSegments);
  on("manualApply", "click", applyManualTable);
  on("groupBtn", "click", regroupSentences);
  on("groupN", "input", refreshSceneInfo);
  wireDrop(dropZoneOf("sceneInput"), "sceneInput", uploadSceneMap);
  on("scenePasteBtn", "click", pasteSceneMap);
  on("sceneTableBtn", "click", applySceneTable);
  wireDrop(dropZoneOf("sceneTableInput"), "sceneTableInput", uploadSceneTable);

  /* step 3 — media */
  wireDrop(dropZoneOf("mediaInput"), "mediaInput", uploadMedia);
  wireDrop(dropZoneOf("zipInput"), "zipInput", importZip);

  /* step 4/5 — look + captions */
  ["optEffect", "optTransition", "optSpeed", "optFilter", "optAspect", "optRes"].forEach((id) => {
    on(id, "change", saveSettings);
  });
  on("capPreset", "change", () => {
    const preset = (S.options.caption_presets || {})[$("capPreset").value];
    if (!preset) return;
    if ($("capFont")) $("capFont").value = preset.font;
    if ($("capSize")) $("capSize").value = preset.font_size;
    if ($("capColor")) $("capColor").value = preset.color;
    if ($("capPosition")) $("capPosition").value = preset.position;
    if ($("capOutline")) $("capOutline").checked = !!preset.outline;
    if ($("capBox")) $("capBox").checked = !!preset.background_box;
    syncRangeLabels();
    updateCaptionPreview();
    saveSettings();
  });
  ["capEnabled", "capMode", "capFont", "capSize", "capColor", "capHighlight", "capPosition",
   "capAnim", "capMargin", "capMaxChars", "capOutline", "capBox", "capBold", "capCaps", "capLang"]
    .forEach((id) => {
      const node = $(id);
      if (!node) return;
      const ev = node.type === "range" ? "input" : "change";
      node.addEventListener(ev, () => { syncRangeLabels(); updateCaptionPreview(); saveSettings(); });
    });
  const fontFile = $("capFontFile");
  if (fontFile) fontFile.addEventListener("change", () => {
    if (fontFile.files && fontFile.files[0]) uploadCaptionFont(fontFile.files[0]);
  });
  on("capFontClear", "click", clearCustomFont);

  /* step 6 — audio */
  wireDrop(dropZoneOf("musicInput"), "musicInput", async (file) => {
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fpost("/upload/music/" + S.sid, fd);
      S.hasMusic = true;
      setPill("musicPill", T.t("ready") + " · " + fmtSec(res.duration || 0), "ok");
      markRail("audio", true);
      toast(T.t("msg_uploaded"), "ok");
    } catch (err) { toast(err.message, "err"); }
  });
  on("musicRemove", "click", async () => {
    try {
      await jdel("/upload/music/" + S.sid);
      S.hasMusic = false;
      setPill("musicPill", T.t("no_music"), "");
      markRail("audio", false);
    } catch (err) { toast(err.message, "err"); }
  });
  ["musicVol", "vidAudioVol", "sfxVol", "stkScale", "stkOp"].forEach((id) => {
    on(id, "input", () => { syncRangeLabels(); saveSettings(); });
  });
  ["vidAudioMode", "vidTrimMode", "ducking", "musicFade", "smartTriggers", "expAspect", "expRes", "expFit"]
    .forEach((id) => on(id, "change", saveSettings));
  on("sfxAdd", "click", addSfx);

  /* step 7 — overlays */
  on("stkAdd", "click", addSticker);
  on("txtAdd", "click", addCustomText);
  on("txtValue", "keydown", (e) => { if (e.key === "Enter") addCustomText(); });
  const stkImg = $("stkImgInput");
  if (stkImg) {
    wireDrop(dropZoneOf("stkImgInput"), "stkImgInput", uploadOverlayImage);
  }
  on("stkWhole", "change", () => {
    const whole = $("stkWhole").checked;
    ["stkStart", "stkDur"].forEach((id) => { if ($(id)) $(id).disabled = whole; });
  });

  /* step 8 — render */
  on("validateBtn", "click", () => runValidation(false));
  on("renderBtn", "click", startRender);
  on("cancelBtn", "click", cancelRender);
  on("exportBtn", "click", quickExport);
  on("skipValidation", "change", saveSettings);

  window.addEventListener("beforeunload", saveSettings);
}

/* ---------------------------- go ---------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  boot().catch((err) => {
    console.error(err);
    toast((err && err.message) || String(err), "err");
  });
});
})();











