/* project-os-cockpit cockpit JS — vanilla, no build step.
 *
 * Drives the left + right panes. The centre pane is server-rendered HTML
 * by the existing markdown renderer; we swap its contents on in-pane
 * navigation so the left pane keeps its scroll position.
 *
 * Endpoints (TASK-0012, schema v2):
 *   GET /api/cockpit/nav                              -> features by phase
 *   GET /api/cockpit/context?this=<id-or-rel-path>    -> linked + backlinks
 */
(function () {
  "use strict";

  var EXPECTED_SCHEMA = 2;
  var FILTER_KEY = "project-os-cockpit.cockpit.hide-completed";
  var COLLAPSED_KEY = "project-os-cockpit.cockpit.collapsed-groups";
  var MODE_KEY = "project-os-cockpit.cockpit.left-mode";
  var PLATFORM_KEY = "project-os-cockpit.cockpit.platform";
  var PINNED_KEY = "project-os-cockpit.cockpit.pinned-paths";
  var META_STRIP_KEY = "project-os-cockpit.cockpit.meta-strip-collapsed";
  var RIGHT_PANE_KEY = "project-os-cockpit.cockpit.right-pane-collapsed";
  var LEFT_PANE_KEY  = "project-os-cockpit.cockpit.left-pane-collapsed";
  var BOTTOM_COLLAPSED_KEY = "project-os-cockpit.cockpit.bottom-collapsed";
  var BOTTOM_HEIGHT_KEY    = "project-os-cockpit.cockpit.bottom-height";
  var FOLLOW_AGENT_KEY     = "project-os-cockpit.cockpit.follow-agent";
  var TAB_ID_KEY           = "project-os-cockpit.cockpit.tab-id";
  var TAB_HEARTBEAT_MS     = 15000;  // see _TAB_STALE_SECONDS (45s) on the server

  // "Project" is first — the orienting mode (directory trees + pinned +
  // rare lifecycle/supporting types). The mode id stays "library" for storage compatibility,
  // but the user-facing label is "Project".
  var NAV_MODES = [
    { id: "library",  label: "Project" },
    { id: "features", label: "Features" },
    { id: "tasks",    label: "Tasks" },
    { id: "issues",   label: "Issues" },
    { id: "recent",   label: "Recent" },
  ];
  var DEFAULT_MODE = "features";

  // Statuses that "Hide completed" filters out. Mirrors the Done-positive
  // and Done-negative palette buckets — anything terminal disappears.
  var COMPLETED_STATUSES = {
    // Done — positive (delivered / accepted / verified)
    done: 1, merged: 1, fixed: 1, fulfilled: 1, met: 1, complete: 1,
    verified: 1, passing: 1, published: 1, closed: 1,
    // Done — negative (terminal without success)
    obsolete: 1, retired: 1, cancelled: 1, superseded: 1,
    "wont-fix": 1, reverted: 1,
  };

  // ------------------------------------------------------------------ state

  var configEl = document.getElementById("cockpit-config");
  if (!configEl) return;
  var active = {};
  try { active = JSON.parse(configEl.textContent || "{}"); } catch (e) {}

  var leftEl = document.getElementById("cockpit-left");
  var rightEl = document.getElementById("cockpit-right");
  var centreEl = document.getElementById("cockpit-centre");
  if (!leftEl || !rightEl || !centreEl) return;

  var navCache = null;       // last-rendered nav payload (for current mode)
  var ctxCache = null;
  var navMode = loadMode();
  var platform = loadPlatform();
  var availablePlatforms = [];   // populated from the latest nav payload

  function loadHideCompleted() {
    try { return localStorage.getItem(FILTER_KEY) === "1"; } catch (e) { return false; }
  }
  function saveHideCompleted(v) {
    try { localStorage.setItem(FILTER_KEY, v ? "1" : "0"); } catch (e) {}
  }
  var hideCompleted = loadHideCompleted();

  function loadMetaStripCollapsed() {
    try { return localStorage.getItem(META_STRIP_KEY) === "1"; } catch (e) { return false; }
  }
  function saveMetaStripCollapsed(v) {
    try { localStorage.setItem(META_STRIP_KEY, v ? "1" : "0"); } catch (e) {}
  }

  function loadRightPaneCollapsed() {
    try { return localStorage.getItem(RIGHT_PANE_KEY) === "1"; } catch (e) { return false; }
  }
  function saveRightPaneCollapsed(v) {
    try { localStorage.setItem(RIGHT_PANE_KEY, v ? "1" : "0"); } catch (e) {}
  }
  var rightPaneCollapsed = loadRightPaneCollapsed();

  function loadLeftPaneCollapsed() {
    try { return localStorage.getItem(LEFT_PANE_KEY) === "1"; } catch (e) { return false; }
  }
  function saveLeftPaneCollapsed(v) {
    try { localStorage.setItem(LEFT_PANE_KEY, v ? "1" : "0"); } catch (e) {}
  }
  var leftPaneCollapsed = loadLeftPaneCollapsed();

  function loadFollowAgent() {
    try {
      var raw = localStorage.getItem(FOLLOW_AGENT_KEY);
      return raw === null ? true : raw === "1";  // default ON
    } catch (e) { return true; }
  }
  function saveFollowAgent(v) {
    try { localStorage.setItem(FOLLOW_AGENT_KEY, v ? "1" : "0"); } catch (e) {}
  }
  var followAgent = loadFollowAgent();

  // Per-tab identifier reported to /api/cockpit/tab-state so the server
  // can surface "what is the user looking at" via /api/cockpit/state
  // (TASK-0055). Persists in localStorage so a refresh keeps the same
  // tab identity; new tabs naturally get a fresh ID because the new tab
  // executes the script before localStorage is touched (we only fall
  // back to a fresh one when nothing is stored).
  function loadOrCreateTabId() {
    try {
      var existing = sessionStorage.getItem(TAB_ID_KEY);
      if (existing) return existing;
    } catch (e) {}
    var fresh = (typeof crypto !== "undefined" && crypto.randomUUID)
      ? crypto.randomUUID()
      : ("t-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10));
    try { sessionStorage.setItem(TAB_ID_KEY, fresh); } catch (e) {}
    return fresh;
  }
  var tabId = loadOrCreateTabId();

  function postTabState() {
    var payload = {
      tab_id: tabId,
      url: window.location.pathname + window.location.search,
      following: followAgent,
    };
    try {
      fetch("/api/cockpit/tab-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(function () {});
    } catch (e) {}
  }

  function loadBottomCollapsed() {
    try {
      var raw = localStorage.getItem(BOTTOM_COLLAPSED_KEY);
      return raw === null ? true : raw === "1";  // collapsed by default
    } catch (e) { return true; }
  }
  function saveBottomCollapsed(v) {
    try { localStorage.setItem(BOTTOM_COLLAPSED_KEY, v ? "1" : "0"); } catch (e) {}
  }
  function loadBottomHeight() {
    try {
      var raw = localStorage.getItem(BOTTOM_HEIGHT_KEY);
      var n = parseInt(raw || "", 10);
      return (n > 80 && n < 1200) ? n : 280;
    } catch (e) { return 280; }
  }
  function saveBottomHeight(px) {
    try { localStorage.setItem(BOTTOM_HEIGHT_KEY, String(px)); } catch (e) {}
  }

  function loadMode() {
    try {
      var raw = localStorage.getItem(MODE_KEY);
      for (var i = 0; i < NAV_MODES.length; i++) {
        if (NAV_MODES[i].id === raw) return raw;
      }
    } catch (e) {}
    return DEFAULT_MODE;
  }
  function saveMode(m) {
    try { localStorage.setItem(MODE_KEY, m); } catch (e) {}
  }

  function loadPlatform() {
    try { return localStorage.getItem(PLATFORM_KEY) || "all"; }
    catch (e) { return "all"; }
  }
  function savePlatform(p) {
    try { localStorage.setItem(PLATFORM_KEY, p); } catch (e) {}
  }

  function loadPinned() {
    try {
      var raw = localStorage.getItem(PINNED_KEY);
      if (!raw) return [];
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr.filter(function (s) { return typeof s === "string"; }) : [];
    } catch (e) { return []; }
  }
  function savePinned(arr) {
    try { localStorage.setItem(PINNED_KEY, JSON.stringify(arr)); } catch (e) {}
  }
  function isPinned(path) {
    if (!path) return false;
    var pins = loadPinned();
    return pins.indexOf(path) !== -1;
  }
  function togglePinned(path) {
    if (!path) return false;
    var pins = loadPinned();
    var idx = pins.indexOf(path);
    if (idx === -1) pins.push(path);
    else pins.splice(idx, 1);
    savePinned(pins);
    return idx === -1;  // true if newly pinned
  }

  function loadCollapsed() {
    try {
      var raw = localStorage.getItem(COLLAPSED_KEY);
      if (!raw) return {};
      var arr = JSON.parse(raw);
      var set = {};
      if (Array.isArray(arr)) arr.forEach(function (k) { set[k] = 1; });
      return set;
    } catch (e) { return {}; }
  }
  function saveCollapsed() {
    try {
      var keys = Object.keys(collapsed);
      localStorage.setItem(COLLAPSED_KEY, JSON.stringify(keys));
    } catch (e) {}
  }
  var collapsed = loadCollapsed();
  function isCollapsed(key) { return !!collapsed[key]; }
  function toggleCollapsed(key) {
    if (collapsed[key]) delete collapsed[key];
    else collapsed[key] = 1;
    saveCollapsed();
  }

  function isHidden(status) {
    if (!hideCompleted) return false;
    if (!status) return false;
    return !!COMPLETED_STATUSES[String(status).toLowerCase()];
  }

  // ------------------------------------------------------------------ utils

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (k === "class") node.className = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else if (k === "html") node.innerHTML = attrs[k];
        else if (attrs[k] != null) node.setAttribute(k, attrs[k]);
      }
    }
    if (children) {
      for (var i = 0; i < children.length; i++) {
        if (children[i] != null) node.appendChild(children[i]);
      }
    }
    return node;
  }

  function statusChip(status) {
    if (!status) return null;
    return el("span", {
      class: "status-chip",
      "data-status": String(status).toLowerCase(),
      text: status,
    });
  }

  // ------------------------------------------------------------------ type ordering
  // Mirror of cockpit.py TYPE_ORDER (REQ-0013) — controls right-pane
  // group ordering after the merge of linked + inbound-only.
  var TYPE_ORDER = [
    "task", "feature", "issue", "requirement", "change", "phase",
    "release", "adr", "risk", "test", "workflow", "plan", "reference",
  ];
  var TYPE_RANK = {};
  TYPE_ORDER.forEach(function (t, i) { TYPE_RANK[t] = i; });

  // ------------------------------------------------------------------ type icons
  // Inline Lucide-style monochrome SVGs keyed by note type. Stroke uses
  // currentColor so the per-type color tokens (CSS) drive the hue.
  var SVG_NS = "http://www.w3.org/2000/svg";
  var TYPE_ICONS = {
    feature:     '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22V15"/>',
    task:        '<path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    issue:       '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    requirement: '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    phase:       '<path d="M3 9h18"/><path d="M3 15h18"/><path d="M5 4v16"/><path d="M19 4v16"/><path d="M9 9v6"/><path d="M15 9v6"/>',
    change:      '<line x1="3" x2="9" y1="12" y2="12"/><line x1="15" x2="21" y1="12" y2="12"/><circle cx="12" cy="12" r="3"/>',
    adr:         '<path d="m16 16 3-8 3 8c-2 1-4 1-6 0z"/><path d="m2 16 3-8 3 8c-2 1-4 1-6 0z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    decision:    '<path d="m16 16 3-8 3 8c-2 1-4 1-6 0z"/><path d="m2 16 3-8 3 8c-2 1-4 1-6 0z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    risk:        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    test:        '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
    workflow:    '<rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/>',
    release:     '<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="m7.5 4.27 9 5.15"/>',
    reference:   '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    plan:        '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
    _default:    '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  };
  function typeIcon(type, size) {
    if (!type) return null;
    var key = String(type).toLowerCase();
    var paths = TYPE_ICONS[key] || TYPE_ICONS._default;
    var px = size ? String(size) : "14";
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "type-icon");
    svg.setAttribute("data-type", key);
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", px);
    svg.setAttribute("height", px);
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = paths;
    return svg;
  }

  // ------------------------------------------------------------------ group icons
  // Used in left-pane group headers to give each group a fast visual hook.
  // Library mode reuses the type-icon for rare:<type> groups; everything
  // else uses one of these section-flavoured Lucide-style icons.
  var GROUP_ICONS = {
    star:          '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    folder_tree:   '<path d="M20 10a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2.5a1 1 0 0 1-.8-.4l-.9-1.2A1 1 0 0 0 15 3h-2a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1Z"/><path d="M20 21a1 1 0 0 0 1-1v-3a1 1 0 0 0-1-1h-2.9a1 1 0 0 1-.88-.55l-.42-.85a1 1 0 0 0-.92-.6H13a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1Z"/><path d="M3 5a2 2 0 0 0 2 2h3"/><path d="M3 3v13a2 2 0 0 0 2 2h3"/>',
    layers:        '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 12.18-9.43 4.27a2 2 0 0 1-1.66 0L2 12.18"/><path d="m22 17.18-9.43 4.27a2 2 0 0 1-1.66 0L2 17.18"/>',
    list_checks:   '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    alert_octagon: '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    sun:           '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    moon:          '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    calendar_days: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>',
    calendar:      '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    history:       '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
  };
  var RECENT_BUCKET_ICONS = {
    today:     GROUP_ICONS.sun,
    yesterday: GROUP_ICONS.moon,
    week:      GROUP_ICONS.calendar_days,
    month:     GROUP_ICONS.calendar,
    earlier:   GROUP_ICONS.history,
  };
  function makeGroupIconSvg(paths, size) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "group-icon");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", String(size || 13));
    svg.setAttribute("height", String(size || 13));
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = paths;
    return svg;
  }
  function groupIcon(mode, group) {
    if (!group) return null;
    var key = String(group.key || "");
    if (key === "pinned")    return makeGroupIconSvg(GROUP_ICONS.star);
    if (key === "docs-tree") return makeGroupIconSvg(GROUP_ICONS.folder_tree);
    if (key.indexOf("rare:") === 0) {
      return typeIcon(key.slice(5), 13);
    }
    if (mode === "features") return makeGroupIconSvg(GROUP_ICONS.layers);
    if (mode === "tasks") {
      var t = makeGroupIconSvg(GROUP_ICONS.list_checks);
      t.setAttribute("data-status", key);
      return t;
    }
    if (mode === "issues") {
      var i = makeGroupIconSvg(GROUP_ICONS.alert_octagon);
      i.setAttribute("data-severity", key);
      return i;
    }
    if (mode === "recent") {
      return makeGroupIconSvg(RECENT_BUCKET_ICONS[key] || GROUP_ICONS.history);
    }
    return null;
  }

  function thisParam() {
    return active.id || active.path || "";
  }

  // Generic collapsible group via <details>/<summary>. Native browser toggling;
  // persists open/closed state under `collapsed[key]` in localStorage.
  //
  // opts.defaultOpen flips the storage semantics: when true (the default),
  // storage-bit-set means the user collapsed the group; when false, the
  // bit means the user opened a default-closed group (used for the
  // month buckets under Changes — TASK-0039). Single storage map, two
  // semantics — bit set ≡ user diverged from default.
  function collapsibleGroup(opts) {
    var defaultOpen = opts.defaultOpen !== false;
    var diverged = isCollapsed(opts.key);
    var startOpen = defaultOpen ? !diverged : diverged;
    var details = el("details", {
      class: opts.sectionClass || "",
      open: startOpen ? "" : null,
    });
    var chevron = el("span", { class: "group-chevron", "aria-hidden": "true" });
    var headerInner = el("span", { class: "group-header-inner" }, opts.headerChildren || []);
    var summary = el("summary", {
      class: opts.headerClass,
      style: opts.headerStyle || null,
    }, [chevron, headerInner]);
    details.appendChild(summary);
    var body = el("div", {
      class: "group-body",
      style: opts.bodyStyle || null,
    }, opts.bodyChildren || []);
    details.appendChild(body);
    details.addEventListener("toggle", function () {
      var isNowOpen = details.open;
      var nowDiverged = defaultOpen ? !isNowOpen : isNowOpen;
      var stored = isCollapsed(opts.key);
      if (nowDiverged !== stored) toggleCollapsed(opts.key);
    });
    return details;
  }

  // ------------------------------------------------------------------ filter UI

  function mountPlatformBar() {
    var slot = document.getElementById("cockpit-platform-slot");
    if (!slot) return;
    if (!availablePlatforms.length) {
      slot.replaceChildren();
      return;
    }
    var pills = ["all"].concat(availablePlatforms);
    // If the user's saved selection is no longer present in the corpus,
    // fall back silently to "all" (don't strand them on a stale platform).
    if (platform !== "all" && availablePlatforms.indexOf(platform) === -1) {
      platform = "all";
      savePlatform(platform);
    }
    var bar = el("div", {
      class: "platform-bar",
      role: "tablist",
      "aria-label": "Platform filter",
    });
    pills.forEach(function (p) {
      var btn = el("button", {
        class: "platform-pill" + (p === platform ? " is-active" : ""),
        type: "button",
        role: "tab",
        "aria-selected": p === platform ? "true" : "false",
        "data-platform": p,
        text: platformLabel(p),
      });
      btn.addEventListener("click", function () {
        if (p === platform) return;
        platform = p;
        savePlatform(platform);
        navCache = null;
        loadLeftPane().then(highlightActiveInLeftPane);
        loadRightPane();
      });
      bar.appendChild(btn);
    });
    slot.replaceChildren(bar);
  }

  function platformLabel(p) {
    if (p === "all") return "All";
    if (p === "ios") return "iOS";
    if (p === "android") return "Android";
    // Title-case for unknown values (web → Web, desktop → Desktop, ...).
    return p.charAt(0).toUpperCase() + p.slice(1);
  }

  function activePath() {
    return active.path || "";
  }

  function mountPinButton() {
    var slot = document.getElementById("cockpit-pin-slot");
    if (!slot) return;
    var path = activePath();
    if (!path || !/^\/docs\//.test(active.url || "")) {
      // Synthetic landing or project-support pages → no pin button.
      slot.replaceChildren();
      return;
    }
    var pinned = isPinned(path);
    var btn = el("button", {
      class: "pin-toggle" + (pinned ? " is-pinned" : ""),
      type: "button",
      "aria-pressed": pinned ? "true" : "false",
      title: pinned ? "Unpin from Library" : "Pin to Library",
      "aria-label": pinned ? "Unpin from Library" : "Pin to Library",
      text: pinned ? "★" : "☆",
    });
    btn.addEventListener("click", function () {
      var nowPinned = togglePinned(path);
      btn.classList.toggle("is-pinned", nowPinned);
      btn.setAttribute("aria-pressed", nowPinned ? "true" : "false");
      btn.textContent = nowPinned ? "★" : "☆";
      btn.title = nowPinned ? "Unpin from Library" : "Pin to Library";
      // If we're looking at the Library, the pinned section needs to refresh.
      if (navMode === "library") {
        navCache = null;
        loadLeftPane().then(highlightActiveInLeftPane);
      }
    });
    slot.replaceChildren(btn);
  }

  function applyMetaStripState() {
    // Server renders <details class="metadata-strip" open>; we strip the
    // open attribute when the user previously collapsed it. Wire up the
    // toggle listener once per element so navigations don't accumulate
    // duplicate handlers.
    var collapsed = loadMetaStripCollapsed();
    document.querySelectorAll(".metadata-strip").forEach(function (el) {
      if (el._metaWired) {
        // already wired; just re-sync open state.
        if (collapsed) el.removeAttribute("open");
        else el.setAttribute("open", "");
        return;
      }
      el._metaWired = true;
      if (collapsed) el.removeAttribute("open");
      el.addEventListener("toggle", function () {
        saveMetaStripCollapsed(!el.open);
      });
    });
  }

  function applyRightPaneState() {
    var cockpitEl = document.querySelector(".cockpit");
    if (!cockpitEl) return;
    cockpitEl.classList.toggle("right-collapsed", rightPaneCollapsed);
  }

  function applyLeftPaneState() {
    var cockpitEl = document.querySelector(".cockpit");
    if (!cockpitEl) return;
    cockpitEl.classList.toggle("left-collapsed", leftPaneCollapsed);
  }

  // ------------------------------------------------------------------ bottom panel

  var bottomTerminalMounted = false;

  function mountBottomPanel() {
    var panel = document.getElementById("cockpit-bottom-panel");
    if (!panel) return;
    var toggle = panel.querySelector(".cockpit-bottom-toggle");
    var body = document.getElementById("cockpit-bottom-body");
    var resizer = document.getElementById("cockpit-bottom-resizer");

    // Apply persisted height (when expanded) and collapsed state.
    var savedHeight = loadBottomHeight();
    panel.style.height = savedHeight + "px";
    setBottomCollapsed(loadBottomCollapsed());

    toggle.addEventListener("click", function () {
      var isCollapsed = panel.classList.contains("is-collapsed");
      setBottomCollapsed(!isCollapsed);
    });

    // Drag-to-resize on the top splitter.
    if (resizer) {
      resizer.addEventListener("mousedown", function (downEvt) {
        if (panel.classList.contains("is-collapsed")) return;
        downEvt.preventDefault();
        resizer.classList.add("is-dragging");
        var startY = downEvt.clientY;
        var startH = panel.getBoundingClientRect().height;
        function onMove(moveEvt) {
          var delta = startY - moveEvt.clientY;
          var next = Math.max(80, Math.min(window.innerHeight - 120, startH + delta));
          panel.style.height = next + "px";
        }
        function onUp() {
          resizer.classList.remove("is-dragging");
          document.removeEventListener("mousemove", onMove);
          document.removeEventListener("mouseup", onUp);
          saveBottomHeight(panel.getBoundingClientRect().height);
        }
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
      });
    }
  }

  function setBottomCollapsed(collapsed) {
    var panel = document.getElementById("cockpit-bottom-panel");
    var toggle = panel && panel.querySelector(".cockpit-bottom-toggle");
    if (!panel) return;
    panel.classList.toggle("is-collapsed", collapsed);
    if (collapsed) {
      panel.style.height = "26px";
    } else {
      panel.style.height = loadBottomHeight() + "px";
      // Lazy-mount the terminal iframe the first time the user opens
      // the panel — avoids spawning ttyd on every page load.
      if (!bottomTerminalMounted) {
        bottomTerminalMounted = true;
        mountTerminalIframe();
      }
    }
    if (toggle) {
      toggle.textContent = collapsed ? "▴" : "▾";
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      toggle.setAttribute(
        "aria-label", collapsed ? "Expand panel" : "Collapse panel"
      );
    }
    saveBottomCollapsed(collapsed);
  }

  function mountTerminalIframe() {
    var body = document.getElementById("cockpit-bottom-body");
    if (!body) return;
    fetch("/api/terminal", { headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (info) {
        if (!info || !info.enabled) {
          var hint = el("div", { class: "cockpit-bottom-placeholder" });
          hint.innerHTML = (info && info.reason)
            ? String(info.reason).replace(/`([^`]+)`/g,
                function (_, c) { return '<code>' + c + '</code>'; })
            : "Terminal not available.";
          body.replaceChildren(hint);
          return;
        }
        // Cache-bust the iframe URL — Chrome aggressively memoises
        // iframe responses even with Cache-Control: no-store, so a
        // changed URL each mount is the reliable way to force a fresh
        // fetch (which picks up CSS injection / proxy changes).
        var bustedUrl = info.url
          + (info.url.indexOf("?") === -1 ? "?" : "&")
          + "_t=" + Date.now();
        var iframe = el("iframe", {
          src: bustedUrl,
          title: "Terminal",
          allow: "clipboard-read; clipboard-write",
        });
        body.replaceChildren(iframe);
      })
      .catch(function (err) {
        body.replaceChildren(el("div", {
          class: "cockpit-bottom-placeholder",
          text: "Terminal endpoint failed: " + err.message,
        }));
      });
  }

  // Lucide panel-right / panel-left icons — the shapes Obsidian uses for
  // its sidebar toggles. Chevron points inward when the pane is open
  // ("click to close") and outward when collapsed ("click to open").
  var PANEL_RIGHT_CLOSE_PATHS =
    '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>' +
    '<line x1="15" x2="15" y1="3" y2="21"/>' +
    '<path d="m8 9 3 3-3 3"/>';
  var PANEL_RIGHT_OPEN_PATHS =
    '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>' +
    '<line x1="15" x2="15" y1="3" y2="21"/>' +
    '<path d="m11 9-3 3 3 3"/>';
  var PANEL_LEFT_CLOSE_PATHS =
    '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>' +
    '<line x1="9" x2="9" y1="3" y2="21"/>' +
    '<path d="m16 15-3-3 3-3"/>';
  var PANEL_LEFT_OPEN_PATHS =
    '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>' +
    '<line x1="9" x2="9" y1="3" y2="21"/>' +
    '<path d="m13 15 3-3-3-3"/>';

  function panelIconSvg(klass, paths) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", klass);
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "20");
    svg.setAttribute("height", "20");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.75");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = paths;
    return svg;
  }
  function panelRightIconSvg(collapsed) {
    return panelIconSvg(
      "panel-right-icon",
      collapsed ? PANEL_RIGHT_OPEN_PATHS : PANEL_RIGHT_CLOSE_PATHS
    );
  }
  function panelLeftIconSvg(collapsed) {
    return panelIconSvg(
      "panel-left-icon",
      collapsed ? PANEL_LEFT_OPEN_PATHS : PANEL_LEFT_CLOSE_PATHS
    );
  }

  function mountLeftPaneToggle() {
    var slot = document.getElementById("cockpit-left-toggle-slot");
    if (!slot) return;
    var btn = el("button", {
      class: "left-pane-toggle" + (leftPaneCollapsed ? " is-collapsed" : ""),
      type: "button",
      "aria-pressed": leftPaneCollapsed ? "true" : "false",
      title: leftPaneCollapsed ? "Show navigator pane" : "Hide navigator pane",
      "aria-label": leftPaneCollapsed ? "Show navigator pane" : "Hide navigator pane",
    });
    btn.appendChild(panelLeftIconSvg(leftPaneCollapsed));
    btn.addEventListener("click", function () {
      leftPaneCollapsed = !leftPaneCollapsed;
      saveLeftPaneCollapsed(leftPaneCollapsed);
      applyLeftPaneState();
      btn.classList.toggle("is-collapsed", leftPaneCollapsed);
      btn.setAttribute("aria-pressed", leftPaneCollapsed ? "true" : "false");
      var label = leftPaneCollapsed ? "Show navigator pane" : "Hide navigator pane";
      btn.title = label;
      btn.setAttribute("aria-label", label);
      btn.replaceChildren(panelLeftIconSvg(leftPaneCollapsed));
    });
    slot.replaceChildren(btn);
  }

  function mountRightPaneToggle() {
    var slot = document.getElementById("cockpit-right-toggle-slot");
    if (!slot) return;
    var btn = el("button", {
      class: "right-pane-toggle" + (rightPaneCollapsed ? " is-collapsed" : ""),
      type: "button",
      "aria-pressed": rightPaneCollapsed ? "true" : "false",
      title: rightPaneCollapsed ? "Show relationships pane" : "Hide relationships pane",
      "aria-label": rightPaneCollapsed ? "Show relationships pane" : "Hide relationships pane",
    });
    btn.appendChild(panelRightIconSvg(rightPaneCollapsed));
    btn.addEventListener("click", function () {
      rightPaneCollapsed = !rightPaneCollapsed;
      saveRightPaneCollapsed(rightPaneCollapsed);
      applyRightPaneState();
      btn.classList.toggle("is-collapsed", rightPaneCollapsed);
      btn.setAttribute("aria-pressed", rightPaneCollapsed ? "true" : "false");
      var label = rightPaneCollapsed ? "Show relationships pane" : "Hide relationships pane";
      btn.title = label;
      btn.setAttribute("aria-label", label);
      btn.replaceChildren(panelRightIconSvg(rightPaneCollapsed));
    });
    slot.replaceChildren(btn);
  }

  function mountFollowAgentToggle() {
    var slot = document.getElementById("cockpit-follow-slot");
    if (!slot) return;
    function render(btn) {
      btn.textContent = followAgent ? "Following" : "Manual";
      btn.title = followAgent
        ? "Cockpit follows agent navigation events (click to opt out)"
        : "Cockpit ignores agent navigation events (click to follow)";
      btn.setAttribute("aria-pressed", followAgent ? "true" : "false");
      btn.classList.toggle("is-active", followAgent);
    }
    var btn = el("button", {
      class: "follow-agent-toggle",
      type: "button",
    });
    render(btn);
    btn.addEventListener("click", function () {
      followAgent = !followAgent;
      saveFollowAgent(followAgent);
      render(btn);
      postTabState();
    });
    slot.replaceChildren(btn);
  }

  function mountCockpitEventStream() {
    // Listen for control events broadcast by the cockpit server
    // (cockpit:focus today; pin / toggle / etc. later). Browser-native
    // EventSource auto-reconnects after server restart.
    var es;
    try { es = new EventSource("/_events"); }
    catch (e) { return; }
    es.addEventListener("cockpit:focus", function (ev) {
      if (!followAgent) return;
      var payload;
      try { payload = JSON.parse(ev.data); }
      catch (e) { return; }
      var url = payload && payload.url;
      if (!url) return;
      // Auto-switch left-pane mode so the agent's focus is visible in
      // the nav (TASK-0052) — otherwise the centre updates but the nav
      // still shows whatever mode the user happened to be in, and the
      // selected/highlighted item doesn't move.
      var nextMode = inferNavModeForTarget(payload.target, url);
      var navPromise = (nextMode && nextMode !== navMode)
        ? switchNavMode(nextMode)
        : Promise.resolve();
      navigateTo(url).then(function () {
        return navPromise;
      }).then(function () {
        // After both nav-mode-switch + navigateTo complete, re-highlight
        // and ensure the active item is in view (might be far down a
        // long list).
        highlightActiveInLeftPane();
        scrollActiveIntoLeftPaneView();
      });
    });
    // Soft live-reload (TASK-0014). Replaces sse-reload.js's full
    // `location.reload()` for cockpit pages — refreshes the three panes
    // in place so the embedded terminal session survives. Debounced so
    // a save-burst from an editor collapses into a single refresh.
    var softReloadTimer = null;
    function scheduleSoftReload() {
      if (softReloadTimer) clearTimeout(softReloadTimer);
      softReloadTimer = setTimeout(function () {
        softReloadTimer = null;
        // Centre re-fetches the current URL; navigateTo also refreshes
        // the right pane internally.
        var here = window.location.pathname + window.location.search;
        navigateTo(here, { replace: true });
        // Left pane — clear cache so the fetch always goes out.
        navCache = null;
        loadLeftPane().then(highlightActiveInLeftPane);
      }, 150);
    }
    es.addEventListener("file-changed", scheduleSoftReload);
    window.addEventListener("beforeunload", function () {
      try { es.close(); } catch (e) {}
    });
  }

  function mountFilterBar() {
    var slot = document.getElementById("cockpit-filter-slot");
    if (!slot) return;
    var btn = el("button", {
      class: "filter-toggle" + (hideCompleted ? " is-active" : ""),
      type: "button",
      "aria-pressed": hideCompleted ? "true" : "false",
      title: "Toggle visibility of done / closed / obsolete items",
      text: hideCompleted ? "Hiding completed" : "Hide completed",
    });
    btn.addEventListener("click", function () {
      hideCompleted = !hideCompleted;
      saveHideCompleted(hideCompleted);
      btn.classList.toggle("is-active", hideCompleted);
      btn.setAttribute("aria-pressed", hideCompleted ? "true" : "false");
      btn.textContent = hideCompleted ? "Hiding completed" : "Hide completed";
      if (navCache) renderLeftPane(navCache);
      if (ctxCache) renderRightPane(ctxCache);
    });
    slot.replaceChildren(btn);
  }

  // ------------------------------------------------------------------ fetch

  function fetchJson(url) {
    return fetch(url, { headers: { Accept: "application/json" } }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      var schema = parseInt(r.headers.get("X-Cockpit-Schema") || "0", 10);
      if (schema && schema !== EXPECTED_SCHEMA) {
        console.warn("cockpit: schema mismatch (server " + schema + ", client " + EXPECTED_SCHEMA + ")");
      }
      return r.json();
    });
  }

  // ------------------------------------------------------------------ left pane

  function mountModeTabs() {
    // Mode tabs live in the page header (Row 1) so they don't move when
    // the breadcrumb width changes per-page.
    var slot = document.getElementById("cockpit-mode-slot");
    if (!slot) return;
    var bar = el("div", { class: "nav-mode-bar", role: "tablist" });
    NAV_MODES.forEach(function (mode) {
      var btn = el("button", {
        class: "nav-mode-tab" + (mode.id === navMode ? " is-active" : ""),
        type: "button",
        role: "tab",
        "aria-selected": mode.id === navMode ? "true" : "false",
        "data-mode": mode.id,
        text: mode.label,
      });
      btn.addEventListener("click", function () {
        switchNavMode(mode.id);
      });
      bar.appendChild(btn);
    });
    slot.replaceChildren(bar);
  }

  function refreshModeTabsUI() {
    var bar = document.querySelector(".nav-mode-bar");
    if (!bar) return;
    bar.querySelectorAll(".nav-mode-tab").forEach(function (b) {
      var isActive = b.getAttribute("data-mode") === navMode;
      b.classList.toggle("is-active", isActive);
      b.setAttribute("aria-selected", isActive ? "true" : "false");
    });
  }

  // Programmatic mode switch (used both by tab clicks and by the
  // follow-agent auto-switch). Returns a Promise that resolves once
  // the left pane has been re-rendered.
  function switchNavMode(nextMode) {
    if (nextMode === navMode) return Promise.resolve();
    navMode = nextMode;
    saveMode(navMode);
    navCache = null;
    refreshModeTabsUI();
    return loadLeftPane().then(highlightActiveInLeftPane);
  }

  // Infer the most useful nav mode for a focus target so the agent's
  // selection is visible + highlightable in the left pane. TASK-0052.
  function inferNavModeForTarget(target, url) {
    var probe = (target || "").trim().toUpperCase();
    if (/^TASK-\d/.test(probe)) return "tasks";
    if (/^ISS-\d/.test(probe))  return "issues";
    if (/^FEAT-\d/.test(probe)) return "features";
    // REQ / PHASE live inside the Features mode (nested under their feature).
    if (/^(REQ|PHASE)-/.test(probe)) return "features";
    // Library "rare" types: ADR, CHG, REL, RISK, TST, WF, PLAN.
    if (/^(ADR|CHG|REL|RISK|TST|WF|PLAN)-/.test(probe)) return "library";
    // URLs without an ID hint — keep the current mode (don't yank the
    // user just because the agent opened a generic doc).
    return null;
  }

  function scrollActiveIntoLeftPaneView() {
    if (!leftEl) return;
    var node = leftEl.querySelector(".nav-item.is-active");
    if (node && typeof node.scrollIntoView === "function") {
      node.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }

  // Default layout (Features / Tasks / Issues / Recent):
  //   row 1: [icon] [id (mono, truncates)] [spacer] [status chip right-aligned]
  //   row 2: [title]
  //   row 3: [subtitle] when present (goal / parent · effort / type · date / ...)
  // Optional children render as a sibling collapsible <details> below the
  // card — used for nested requirements under features.
  function navItem(item) {
    var topLine = el("div", { class: "nav-line" }, [
      typeIcon(item.type),
      item.id
        ? el("span", { class: "nav-id mono", text: item.id, title: item.id })
        : null,
      el("span", { class: "nav-line-spacer" }),
      statusChip(item.status),
    ]);
    var titleNode = item.title
      ? el("p", {
          class: "nav-title",
          text: item.title,
          title: item.title,
        })
      : null;
    var subtitleNode = item.subtitle
      ? el("p", {
          class: "nav-subtitle",
          text: item.subtitle,
          title: item.subtitle,
        })
      : null;
    var card = el("a", {
      class: "nav-item" + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine, titleNode, subtitleNode]);
    var childrenNode = (item.children && item.children.length)
      ? renderItemChildren(item)
      : null;
    return el("li", null, [card, childrenNode]);
  }

  // Collapsible nested children list (used for requirements under features).
  // Default = collapsed. The persisted-collapse-set storage is repurposed
  // as a persisted-OPEN set (key "nav:item-children-open:<id>") so the
  // default is the inverse of the rest of the cockpit.
  function renderItemChildren(item) {
    // Apply the Hide-completed filter to nested children too. Without
    // this the filter only hits top-level group items (features /
    // tasks / etc.), leaving verified / retired requirements visible
    // under their feature card.
    var visibleChildren = (item.children || []).filter(function (c) {
      return !isHidden(c.status);
    });
    if (!visibleChildren.length) return null;
    var openedKey = "nav:item-children-open:" + (item.id || item.url || "");
    var startOpen = isCollapsed(openedKey);
    var details = el("details", {
      class: "nav-item-children",
      open: startOpen ? "" : null,
    });
    var label = visibleChildren.length === 1
      ? "1 requirement"
      : visibleChildren.length + " requirements";
    var summary = el("summary", { class: "nav-item-children-toggle" }, [
      el("span", { class: "nav-children-chevron", "aria-hidden": "true" }),
      el("span", { text: label }),
    ]);
    details.appendChild(summary);
    var list = el("ul", { class: "nav-item-children-list" });
    visibleChildren.forEach(function (child) {
      list.appendChild(navItemNested(child));
    });
    details.appendChild(list);
    details.addEventListener("toggle", function () {
      // Mirror the "user opened it" state into collapsed storage so it
      // survives reload. Open => store key; closed => remove.
      var stored = isCollapsed(openedKey);
      if (details.open !== stored) toggleCollapsed(openedKey);
    });
    return details;
  }

  // Compact stacked card used for items nested under another card (reqs
  // under features). Smaller padding, single-line title with ellipsis.
  function navItemNested(item) {
    var topLine = el("div", { class: "nav-line" }, [
      typeIcon(item.type, 12),
      item.id ? el("span", { class: "nav-id mono", text: item.id }) : null,
      el("span", { class: "nav-line-spacer" }),
      statusChip(item.status),
    ]);
    var titleNode = item.title
      ? el("p", {
          class: "nav-title-nested",
          text: item.title,
          title: item.title,
        })
      : null;
    var card = el("a", {
      class: "nav-item nav-item-nested"
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine, titleNode]);
    return el("li", null, [card]);
  }

  // Stacked layout: icon + id on the top line (status right-aligned),
  // human title on a second line, optional path/parent-dir subtitle on a
  // third. Used by Project mode's pinned and rare-types sections.
  function navItemStacked(item) {
    var topLine = el("div", { class: "nav-line" }, [
      typeIcon(item.type),
      item.id ? el("span", { class: "nav-id mono", text: item.id }) : null,
      el("span", { class: "nav-line-spacer" }),
      statusChip(item.status),
    ]);
    var titleNode = item.title
      ? el("p", {
          class: "nav-title-stacked",
          text: item.title,
          title: item.title,
        })
      : null;
    var subtitleNode = item.subtitle
      ? el("p", {
          class: "nav-subtitle-stacked mono",
          text: item.subtitle,
          title: item.subtitle,
        })
      : null;
    var card = el("a", {
      class: "nav-item nav-item-stacked"
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine, titleNode, subtitleNode]);
    return el("li", null, [card]);
  }

  // Compact layout: filename only, single line, tight padding.
  // Used by Project mode's Docs tree. Typed entries (references) render
  // their type icon instead of the default file mask; untyped entries
  // keep the generic file icon (CSS ::before).
  function navItemCompact(item) {
    var iconNode = item.type ? typeIcon(item.type, 12) : null;
    var titleSpan = el("span", {
      class: "nav-title-compact",
      text: item.title || "",
      title: item.title || "",
    });
    var card = el("a", {
      class: "nav-item nav-item-compact"
        + (item.type ? " has-type-icon" : "")
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [iconNode, titleSpan]);
    return el("li", null, [card]);
  }

  function pickItemRenderer(layout) {
    if (layout === "stacked") return navItemStacked;
    if (layout === "compact") return navItemCompact;
    return navItem;
  }

  // Build collapsible-group nodes for nested directory-tree groups.
  function renderSubgroups(parent, mode, depth) {
    var subs = (parent.subgroups || []);
    var nodes = [];
    subs.forEach(function (sg) {
      var node = renderSubgroup(sg, mode, depth || 0);
      if (node) nodes.push(node);
    });
    return nodes;
  }

  function renderSubgroup(group, mode, depth) {
    var visibleItems = (group.items || []).filter(function (it) { return !isHidden(it.status); });
    var childNodes = renderSubgroups(group, mode, depth + 1);
    if (!visibleItems.length && !childNodes.length) return null;

    var renderItem = pickItemRenderer(group.item_layout);
    var list = el("ul", { class: "nav-items" });
    visibleItems.forEach(function (item) { list.appendChild(renderItem(item)); });

    var bodyChildren = [list];
    childNodes.forEach(function (node) { bodyChildren.push(node); });

    var subKey = "nav:" + mode + ":" + (group.key || "");
    var sectionExtra = group.item_layout ? " nav-group-" + group.item_layout : "";
    var indentStyle = "--tree-indent:" + String((depth || 0) * 12) + "px";
    var node = collapsibleGroup({
      key: subKey,
      sectionClass: "nav-subgroup" + sectionExtra,
      headerClass: "nav-subgroup-header",
      headerStyle: indentStyle,
      bodyStyle: indentStyle,
      headerChildren: [el("span", { text: group.label || group.key || "" })],
      bodyChildren: bodyChildren,
      defaultOpen: group.default_open !== false,
    });
    // Mirror the indent on the <details> itself so CSS selectors targeting
    // the section (e.g. indent guides) can read --tree-indent there too.
    node.style.setProperty("--tree-indent", String((depth || 0) * 12) + "px");
    node.dataset.depth = String(depth || 0);
    return node;
  }

  function renderLeftPane(payload) {
    var groups = (payload && payload.groups) || [];
    var mode = (payload && payload.mode) || navMode;
    var frag = document.createDocumentFragment();

    if (!groups.length) {
      frag.appendChild(el("p", {
        class: "cockpit-empty",
        text: emptyMessageFor(mode),
      }));
      leftEl.replaceChildren(frag);
      return;
    }

    var anyVisible = false;
    groups.forEach(function (g) {
      var visibleItems = (g.items || []).filter(function (it) { return !isHidden(it.status); });
      var subgroupNodes = renderSubgroups(g, mode);
      if (!visibleItems.length && !subgroupNodes.length) return;
      anyVisible = true;

      var label = g.label || g.key || "";
      var titleNode = g.url
        ? el("a", {
            class: "group-header-link",
            href: g.url,
            text: label,
            title: "Open " + label,
          })
        : el("span", { text: label });
      var headerChildren = [groupIcon(mode, g), titleNode];
      if (g.status) {
        headerChildren.push(el("span", { class: "nav-group-spacer" }));
        headerChildren.push(statusChip(g.status));
      }

      var renderItem = pickItemRenderer(g.item_layout);
      var list = el("ul", { class: "nav-items" });
      visibleItems.forEach(function (item) { list.appendChild(renderItem(item)); });

      var bodyChildren = [list];
      subgroupNodes.forEach(function (n) { bodyChildren.push(n); });

      var sectionExtra = g.item_layout ? " nav-group-" + g.item_layout : "";
      var key = "nav:" + mode + ":" + (g.key || label || "unkeyed");
      frag.appendChild(collapsibleGroup({
        key: key,
        sectionClass: "nav-group" + sectionExtra,
        headerClass: "nav-group-header",
        headerChildren: headerChildren,
        bodyChildren: bodyChildren,
      }));
    });

    if (!anyVisible) {
      frag.appendChild(el("p", {
        class: "cockpit-empty",
        text: "Everything in this view is completed (toggle filter to show).",
      }));
    }
    leftEl.replaceChildren(frag);
  }

  function emptyMessageFor(mode) {
    if (mode === "tasks")  return "No tasks in this docs tree.";
    if (mode === "issues") return "No issues in this docs tree.";
    if (mode === "recent") return "No recent notes.";
    return "No features.";
  }

  function loadLeftPane() {
    var pins = loadPinned();
    var pinKey = pins.join(",");
    if (
      navCache && navCache.mode === navMode && navCache.platform === platform
      && navCache._pinKey === pinKey
    ) {
      renderLeftPane(navCache);
      return Promise.resolve();
    }
    var url = "/api/cockpit/nav?mode=" + encodeURIComponent(navMode)
            + "&platform=" + encodeURIComponent(platform);
    if (navMode === "library" && pins.length) {
      url += "&pinned=" + encodeURIComponent(pins.join(","));
    }
    return fetchJson(url)
      .then(function (payload) {
        payload._pinKey = pinKey;
        navCache = payload;
        availablePlatforms = (payload.available_platforms || []).slice();
        mountPlatformBar();
        renderLeftPane(payload);
      })
      .catch(function (err) {
        leftEl.replaceChildren(
          el("p", { class: "cockpit-error", text: "Nav failed: " + err.message })
        );
      });
  }

  // ------------------------------------------------------------------ right pane

  function ctxItem(item, kind) {
    var priorityChip = null;
    if (item.severity) {
      // Issues surface severity (TASK-0035). Reuse the --severity-* token
      // palette also used by the left-pane issue group icons.
      priorityChip = el("span", {
        class: "ctx-severity",
        "data-severity": String(item.severity).toLowerCase(),
        text: item.severity,
      });
    } else if (item.priority) {
      priorityChip = el("span", {
        class: "ctx-priority",
        "data-priority": String(item.priority).toLowerCase(),
        text: item.priority,
      });
    }
    var topLine = el("div", { class: "ctx-line" }, [
      typeIcon(item.type),
      item.id ? el("span", { class: "ctx-id mono", text: item.id }) : null,
      el("span", { class: "nav-line-spacer" }),
      priorityChip,
      statusChip(item.status),
    ]);
    var titleNode = el("p", {
      class: "ctx-title",
      text: item.title || item.id || "",
      title: item.title || "",
    });
    var card = el("a", {
      class: "ctx-item ctx-item-" + kind,
      href: item.url,
    }, [topLine, titleNode]);
    return el("li", null, [card]);
  }

  // Merge `linked` (outbound) and `backlinks` (inbound-only) into one
  // per-type structure. Outbound items render first; inbound-only items
  // follow underneath the same type group, visually distinguished.
  // Final order matches the canonical TYPE_ORDER (REQ-0013) — first-
  // appearance order from server-side payloads would put inbound-only
  // types after outbound ones regardless of their rank, which violates
  // the spec.
  function mergeContext(linked, backlinks) {
    var byType = {};
    function pushGroup(group, kind) {
      if (!group || !group.items) return;
      var t = String(group.type || "").toLowerCase();
      if (!byType[t]) byType[t] = { type: t, linked: [], inbound: [] };
      group.items.forEach(function (it) { byType[t][kind].push(it); });
    }
    (linked || []).forEach(function (g) { pushGroup(g, "linked"); });
    (backlinks || []).forEach(function (g) { pushGroup(g, "inbound"); });
    var types = Object.keys(byType);
    types.sort(function (a, b) {
      var ra = TYPE_RANK.hasOwnProperty(a) ? TYPE_RANK[a] : TYPE_ORDER.length;
      var rb = TYPE_RANK.hasOwnProperty(b) ? TYPE_RANK[b] : TYPE_ORDER.length;
      if (ra !== rb) return ra - rb;
      return a < b ? -1 : a > b ? 1 : 0;
    });
    return types.map(function (t) { return byType[t]; });
  }

  function renderRelationships(merged, container) {
    if (!merged.length) return false;
    var any = false;
    merged.forEach(function (g) {
      var visibleLinked = g.linked.filter(function (it) { return !isHidden(it.status); });
      var visibleInbound = g.inbound.filter(function (it) { return !isHidden(it.status); });
      if (!visibleLinked.length && !visibleInbound.length) return;
      any = true;
      var typeName = g.type;
      var typeLabel = el("span", {
        class: "ctx-type-label",
        "data-type": typeName,
      }, [
        typeIcon(typeName, 13),
        el("span", { text: pluralizeType(typeName) }),
      ]);
      var list = el("ul", { class: "ctx-items" });
      visibleLinked.forEach(function (item) { list.appendChild(ctxItem(item, "linked")); });
      if (visibleLinked.length && visibleInbound.length) {
        list.appendChild(el("li", {
          class: "ctx-divider",
          "aria-hidden": "true",
          text: "↩ inbound only",
        }));
      } else if (visibleInbound.length && !visibleLinked.length) {
        // No outbound at all — still mark the inbound-only origin clearly.
        list.appendChild(el("li", {
          class: "ctx-divider ctx-divider-leading",
          "aria-hidden": "true",
          text: "↩ inbound only",
        }));
      }
      visibleInbound.forEach(function (item) { list.appendChild(ctxItem(item, "inbound")); });

      var key = "ctx:" + (typeName || "_untyped");
      container.appendChild(collapsibleGroup({
        key: key,
        sectionClass: "ctx-group",
        headerClass: "ctx-group-header",
        headerChildren: [typeLabel],
        bodyChildren: [list],
      }));
    });
    return any;
  }

  // Lower-case plural label for type group headers ("features", "tasks", etc.).
  // Falls back to type + "s" for unknown types.
  var TYPE_PLURALS = {
    feature: "features", task: "tasks", requirement: "requirements",
    issue: "issues", risk: "risks", adr: "decisions", decision: "decisions",
    change: "changes", release: "releases", workflow: "workflows",
    test: "tests", phase: "phases", plan: "plans",
    reference: "references",
  };
  function pluralizeType(t) {
    if (!t) return "";
    return TYPE_PLURALS[t] || (t + "s");
  }

  function renderRightPane(payload) {
    var frag = document.createDocumentFragment();

    if (!payload || !payload.active) {
      frag.appendChild(el("p", { class: "cockpit-empty", text: "No active note selected." }));
      rightEl.replaceChildren(frag);
      return;
    }
    var merged = mergeContext(payload.linked, payload.backlinks);
    var any = renderRelationships(merged, frag);
    if (!any) {
      frag.appendChild(el("p", { class: "cockpit-empty", text: "No relationships." }));
    }
    rightEl.replaceChildren(frag);
  }

  function loadRightPane() {
    var ctxThis = thisParam();
    var qs = [];
    if (ctxThis) qs.push("this=" + encodeURIComponent(ctxThis));
    qs.push("platform=" + encodeURIComponent(platform));
    var url = "/api/cockpit/context" + (qs.length ? "?" + qs.join("&") : "");
    return fetchJson(url)
      .then(function (payload) {
        ctxCache = payload;
        renderRightPane(payload);
      })
      .catch(function (err) {
        rightEl.replaceChildren(
          el("p", { class: "cockpit-error", text: "Context failed: " + err.message })
        );
      });
  }

  // ------------------------------------------------------------------ navigation

  // Intercept any same-origin link that renders inside the cockpit shell
  // so we do an in-pane swap (preserves the terminal session, side-pane
  // scroll positions, etc.) instead of a full page reload. The explicit
  // deny-list keeps URLs that should NOT route through navigateTo:
  // static assets, the terminal proxy, the SSE channel, the cockpit JSON
  // API, the favicon. Everything else (/, /docs/*, /README.md, /index/*,
  // ...) gets in-pane treatment; navigateTo falls back to a full
  // navigation if a target's response doesn't contain #cockpit-centre.
  function isInternalNoteLink(href) {
    if (!href) return false;
    if (href.charAt(0) === "#") return false;       // fragment-only, no nav
    var url;
    try { url = new URL(href, document.location.href); }
    catch (e) { return false; }
    if (url.origin !== document.location.origin) return false;
    var path = url.pathname;
    if (path.indexOf("/_static/") === 0) return false;
    if (path === "/_terminal" || path.indexOf("/_terminal/") === 0) return false;
    if (path === "/_events") return false;
    if (path.indexOf("/api/") === 0) return false;
    if (path === "/favicon.ico") return false;
    return true;
  }

  function setActiveFromUrl(url) {
    var u = new URL(url, document.location.origin);
    active.url = u.pathname;
    // active.path should only be set for URLs that map to a real note —
    // not for the landing page, type indexes, etc. (which intercept via
    // isInternalNoteLink purely so we keep the cockpit shell mounted).
    if (/^\/docs\//.test(u.pathname)) {
      active.path = u.pathname.replace(/^\/docs\//, "");
    } else if (/^\/(README|ROADMAP|SECURITY)\.md$/i.test(u.pathname)) {
      active.path = u.pathname.replace(/^\//, "");
    } else {
      active.path = "";
    }
    active.id = null;
    active.title = null;
  }

  function syncActiveFromCentre() {
    var fresh = document.getElementById("cockpit-config");
    if (!fresh) return;
    try {
      var data = JSON.parse(fresh.textContent || "{}");
      Object.assign(active, data);
    } catch (e) {}
  }

  function highlightActiveInLeftPane() {
    if (!leftEl) return;
    leftEl.querySelectorAll(".nav-item.is-active").forEach(function (n) {
      n.classList.remove("is-active");
    });
    if (!active.url) return;
    leftEl.querySelectorAll(".nav-item").forEach(function (a) {
      if (a.getAttribute("href") === active.url) a.classList.add("is-active");
    });
  }

  function navigateTo(url, options) {
    var pushState = !(options && options.replace);
    return fetch(url, { headers: { Accept: "text/html" } })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var newCentre = doc.getElementById("cockpit-centre");
        if (!newCentre) {
          window.location.href = url;
          return;
        }
        centreEl.innerHTML = newCentre.innerHTML;
        var newConfig = doc.getElementById("cockpit-config");
        if (newConfig) {
          var oldConfig = document.getElementById("cockpit-config");
          if (oldConfig) oldConfig.replaceWith(newConfig);
        }
        document.title = doc.title;
        var newReload = doc.querySelector('meta[name="project-os-cockpit:source"]');
        var oldReload = document.querySelector('meta[name="project-os-cockpit:source"]');
        if (newReload && oldReload) {
          oldReload.setAttribute("content", newReload.getAttribute("content") || "");
        }
        // Swap Row 2 (pin slot + breadcrumb) so the path reflects the new
        // active note. Row 1 (mode tabs + global controls) stays put — its
        // contents are JS-mounted and don't need server-side updates.
        var newRow2 = doc.querySelector(".page-header-row-2");
        var oldRow2 = document.querySelector(".page-header-row-2");
        if (newRow2 && oldRow2) {
          oldRow2.className = newRow2.className;
          var newCrumb = newRow2.querySelector(".breadcrumb");
          var oldCrumb = oldRow2.querySelector(".breadcrumb");
          if (newCrumb && oldCrumb) oldCrumb.innerHTML = newCrumb.innerHTML;
        }
        if (pushState) history.pushState({ url: url }, "", url);
        setActiveFromUrl(url);
        syncActiveFromCentre();
        highlightActiveInLeftPane();
        mountPinButton();
        applyMetaStripState();
        centreEl.scrollTop = 0;
        postTabState();
        return loadRightPane();
      })
      .catch(function (err) {
        console.warn("cockpit: navigate failed", err);
        window.location.href = url;
      });
  }

  // ------------------------------------------------------------------ events

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented) return;
    if (e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest("a");
    if (!a) return;
    if (a.target && a.target !== "" && a.target !== "_self") return;
    var href = a.getAttribute("href");
    if (!isInternalNoteLink(href)) return;
    e.preventDefault();
    navigateTo(href);
  });

  window.addEventListener("popstate", function () {
    navigateTo(window.location.pathname, { replace: true });
  });

  // ------------------------------------------------------------------ boot

  mountModeTabs();
  mountFilterBar();
  mountFollowAgentToggle();
  mountLeftPaneToggle();
  mountRightPaneToggle();
  mountPinButton();
  mountBottomPanel();
  mountCockpitEventStream();
  applyLeftPaneState();
  applyRightPaneState();
  applyMetaStripState();

  // Tell the server we're here, then ping on a 15s cadence so
  // /api/cockpit/state can show this tab in its live-tabs list. The
  // server prunes anything that hasn't pinged in 45s (TASK-0053).
  postTabState();
  setInterval(postTabState, TAB_HEARTBEAT_MS);
  window.addEventListener("pagehide", postTabState);
  loadLeftPane().then(highlightActiveInLeftPane);
  loadRightPane();
})();
