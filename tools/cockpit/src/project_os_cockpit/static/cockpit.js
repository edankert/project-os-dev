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
  var HEALTH_PANEL_KEY     = "project-os-cockpit.cockpit.health-panel-open";

  // "Project" is first — the orienting mode (directory trees + pinned +
  // rare lifecycle/supporting types). The mode id stays "library" for storage compatibility,
  // but the user-facing label is "Project".
  // Tasks retired in TASK-0368 — tasks hang under their feature (TASK-0366).
  // The server still serves `mode=tasks`; no front door offers it.
  var NAV_MODES = [
    { id: "library",  label: "Project" },
    { id: "features", label: "Features" },
    { id: "issues",   label: "Issues" },
    { id: "recent",   label: "Recent" },
  ];
  var DEFAULT_MODE = "features";

  // Terminal statuses — what the collapse control folds at (FEAT-0056;
  // nothing filters on them any more). Mirrors the Done-positive
  // and Done-negative palette buckets — anything terminal disappears.
  //
  // Canonical membership lives in src/project_os_cockpit/statuses.py
  // (COMPLETED_STATUSES); tests/test_status_vocabulary.py parses this
  // object and fails if the two drift apart.
  //
  // NOTE: `staged` / `monitoring` are deliberately NOT here (ISS-0023).
  // They are the Delivered band — shipped but not signed off (a release
  // ready but not live; a risk mitigated but still watched). Do not "fix"
  // this by adding them; they carry their own amber chip instead.
  // `implemented` WAS in that band until ADR-0007 retired the requirement
  // `verified` status and made `implemented` terminal — it is completed now.
  var COMPLETED_STATUSES = {
    // Done — positive (accepted / verified / shipped)
    done: 1, merged: 1, fixed: 1, resolved: 1, fulfilled: 1, met: 1,
    complete: 1, implemented: 1, verified: 1, passing: 1, published: 1,
    released: 1,
    closed: 1,
    // Done — negative (terminal without success)
    obsolete: 1, retired: 1, cancelled: 1, superseded: 1,
    "declined": 1, reverted: 1, deprecated: 1, reconciled: 1,
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

  // `isHidden` lived here until FEAT-0056. Nothing removes an item by
  // status any more.
  //
  // At 99% lifecycle completion a state filter is not a filter: with
  // Hide-completed on, 1 of 18 feature groups survived, 0 of the 4 issue
  // severity buckets, 5 item rows of 270 tasks, and the right-hand
  // context pane of a finished note emptied outright. The rule that
  // replaced it is FOLD ON VOLUME, NEVER ON MEANING — the same rule the desktop renderer encodes in
  // `completed-work.ts`, and the four functions below are its twin.

  function completionRank(item) {
    var st = item && item.status ? String(item.status).toLowerCase() : "";
    // An UNRECOGNISED status ranks open, deliberately: sinking it would
    // quietly bury a note whose status is a typo.
    return COMPLETED_STATUSES[st] ? 1 : 0;
  }

  // True when every item is terminal — the group has nothing to act on.
  // An EMPTY group counts as settled, same as the desktop twin.
  //
  // ISS-0138: this file CALLED this function four times and defined it
  // nowhere, so `groupIsSettled is not defined` threw on the first group
  // either side pane rendered — which is every page. Both panes showed an
  // error box and mode 1 has been unusable since. The desktop shell got
  // away with it because `completed-work.js` publishes the name as a
  // global there; nothing loads that file here, and `templates.py` emits
  // exactly one script tag.
  //
  // The comment above says "the three functions below are its twin" and
  // there were only two. That is the twin problem stated by its own
  // comment and not noticed — ADR-0021 is the proposal to end it.
  function groupIsSettled(items) {
    return !(items || []).some(function (it) { return completionRank(it) === 0; });
  }

  // Open work first, the server's order (ID, severity, path) preserved
  // beneath — Array.sort is stable, so nothing else moves.
  function openFirst(items) {
    return (items || []).slice().sort(function (a, b) {
      return completionRank(a) - completionRank(b);
    });
  }

  // How much of a group renders. Two independent reasons to fold:
  // `collapse` (the switch) folds at the first completed item — meaning;
  // `limit` folds at a length nobody reads past — volume. Neither can
  // return nothing, so a group can shorten but never vanish.
  function foldGroup(items, limit, collapse) {
    var ordered = openFirst(items);
    if (!ordered.length) return { head: [], hidden: 0 };
    // head + hidden must equal items.length for EVERY input, not just the
    // ones we pass: the count is the only thing telling the reader that
    // anything was withheld.
    var cap = isFinite(limit) ? Math.max(0, Math.floor(limit)) : ordered.length;
    var cut = ordered.length;
    if (collapse) {
      var firstDone = -1;
      for (var i = 0; i < ordered.length; i++) {
        if (completionRank(ordered[i]) === 1) { firstDone = i; break; }
      }
      // An entirely settled group cuts to ZERO rows, not one: a single
      // arbitrary row tells the reader nothing the count does not. The
      // group stays visible through its header and its count.
      if (firstDone >= 0) cut = firstDone;
    }
    if (cut > cap) cut = cap;
    return { head: ordered.slice(0, cut), hidden: ordered.length - cut };
  }

  // Measured group sizes in the pilot corpus: tasks 261/3/2/2/2, issues
  // 52/18/11/2/1/1/1, features 19/10/5/3/2/2/2/2/2 then nine 1s. A clean
  // cliff — twelve folds the four that are unreadable (261, 52, 19, 18)
  // and leaves the other twenty-six whole.
  // What a group's head should say about its items' status (TASK-0272).
  // null means "the statuses vary — leave the per-row chips alone". The
  // rule: repeat a fact per-row only when it varies per-row.
  function uniformStatus(items) {
    if (!items || !items.length) return null;
    var first = String(items[0].status || "").toLowerCase();
    if (!first) return null;
    for (var i = 0; i < items.length; i++) {
      if (String(items[i].status || "").toLowerCase() !== first) return null;
    }
    return first;
  }

  // The short handle for a note ID (ISS-0084). Changes carry
  // CHG-YYYYMMDD-Short-Description, so their id IS a description and a
  // row printed it twice — at several times the width of every other ID,
  // in a column whose width is set by its widest member. Display only;
  // never feed this back into a lookup.
  function shortNoteId(id) {
    if (!id) return "";
    var m = /^(CHG-\d{8})-.+/.exec(String(id));
    return m ? m[1] : String(id);
  }

  // True when the head summary already ends in `· <status>`, so showing
  // the group's own chip would restate it.
  function endsWithStatus(summary, status) {
    var suffix = "\u00b7 " + status;
    return summary.slice(-suffix.length) === suffix;
  }

  // `19 · done`, `6 · 5 done`, or just `4`.
  function groupHeadSummary(items) {
    var n = items ? items.length : 0;
    if (!n) return "";
    var uniform = uniformStatus(items);
    if (uniform) return n + " \u00b7 " + uniform;
    var done = 0;
    for (var i = 0; i < n; i++) if (completionRank(items[i]) === 1) done++;
    return done ? n + " \u00b7 " + done + " done" : String(n);
  }

  // The context pane's rows: ordered, folded on length, NEVER on state.
  // Takes no `collapse` argument on purpose — review reverted the caller
  // from `false` to `hideCompleted` in one character with every test
  // still green, on the pane whose emptying was the whole point of the
  // phase. Removing the parameter is what makes that mutation impossible
  // to write by accident.
  function contextGroupRows(items, limit) {
    return foldGroup(items, limit, false);
  }

  var NAV_GROUP_FOLD_LIMIT = 12;

  // The fold's own row. The count is never optional: a fold that hides
  // the fact that it hid something is indistinguishable from having
  // nothing there — which is exactly how the old filter emptied three
  // views without ever looking broken.
  // The context pane's own more-row. Separate from `appendMoreRow`
  // because this pane renders two runs (linked, then inbound) into one
  // list and each folds independently.
  function appendCtxMoreRow(list, folded, allItems, kind) {
    if (!folded.hidden) return;
    var btn = el("button", {
      type: "button",
      class: "nav-more-btn",
      text: "\u2026 " + folded.hidden + " more",
      title: "Show the rest of this group",
    });
    btn.addEventListener("click", function (ev) {
      ev.stopPropagation();
      ev.preventDefault();
      var li = btn.parentNode;
      var frag = document.createDocumentFragment();
      openFirst(allItems).slice(folded.head.length).forEach(function (item) {
        frag.appendChild(ctxItem(item, kind));
      });
      list.replaceChild(frag, li);
    });
    list.appendChild(el("li", { class: "nav-item nav-more" }, [btn]));
  }

  function appendMoreRow(list, folded, group, renderItem) {
    if (!folded.hidden) return;
    var btn = el("button", {
      type: "button",
      class: "nav-more-btn",
      text: "\u2026 " + folded.hidden + " more",
      title: "Show the rest of this group",
    });
    btn.addEventListener("click", function (ev) {
      ev.stopPropagation();
      ev.preventDefault();
      // Reveal in place. Deliberately NOT a change to `hideCompleted`:
      // expanding one group must not flip a preference governing every
      // other group on the surface.
      var all = openFirst(group.items || []);
      var frag = document.createDocumentFragment();
      all.forEach(function (item) { frag.appendChild(renderItem(item)); });
      list.replaceChildren(frag);
    });
    list.appendChild(el("li", { class: "nav-item nav-more" }, [btn]));
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

  // Verification-surface badges (FEAT-0018 / TASK-0113): amber "waived"
  // chip, green/red review-verdict chip, and a "no evidence" marker for
  // TST notes without adequacy evidence. The flags ride on nav/context
  // item payloads (cockpit.py `_verification_flags`); rendered right
  // before the status chip so a waived terminal status can't be
  // mistaken for a verified one.
  function itemBadges(item) {
    var out = [];
    if (!item) return out;
    if (item.waived) {
      out.push(el("span", {
        class: "waiver-chip",
        text: "waived",
        title: "Terminal status held under a recorded verification waiver",
      }));
    }
    if (item.review_verdict) {
      out.push(el("span", {
        class: "verdict-chip",
        "data-verdict": String(item.review_verdict).toLowerCase(),
        text: item.review_verdict,
      }));
    }
    if (item.type === "test" && item.adequacy === false) {
      out.push(el("span", {
        class: "adequacy-chip",
        text: "no evidence",
        title: "No adequacy evidence recorded (adequacy / mutation_score)",
      }));
    }
    return out;
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

  // ---------------------------------------------------- validation health
  // FEAT-0018 / TASK-0112 — top-bar badge (green OK / red error count /
  // grey unavailable) backed by GET /api/cockpit/validation, plus a
  // drift panel deep-linking each violation to the offending note.
  // Live updates arrive over the cockpit:validation SSE event; the
  // panel's open state persists (localStorage) and the panel itself is
  // untouched by soft live-reload (only the panes re-render).

  var validationCache = null;   // last /api/cockpit/validation payload

  function loadHealthPanelOpen() {
    try { return localStorage.getItem(HEALTH_PANEL_KEY) === "1"; } catch (e) { return false; }
  }
  function saveHealthPanelOpen(v) {
    try { localStorage.setItem(HEALTH_PANEL_KEY, v ? "1" : "0"); } catch (e) {}
  }
  var healthPanelOpen = loadHealthPanelOpen();

  function healthState() {
    if (!validationCache) return "unknown";
    if (validationCache.state) return validationCache.state;
    return validationCache.ok ? "ok" : "failing";
  }

  function renderHealthBadge() {
    var slot = document.getElementById("cockpit-health-slot");
    if (!slot) return;
    var state = healthState();
    var errs = (validationCache && validationCache.errors) || [];
    var label = "…";
    var title = "Docs validation state unknown";
    if (state === "ok") {
      label = "OK";
      title = "Docs validation: no drift (validate-docs.py)";
    } else if (state === "failing") {
      label = String(errs.length);
      title = "Docs validation: " + errs.length +
        " violation" + (errs.length === 1 ? "" : "s") +
        " — click for the drift panel";
    } else if (state === "unavailable") {
      label = "n/a";
      title = "Docs validator unavailable" +
        (validationCache && validationCache.detail
          ? ": " + validationCache.detail : "");
    }
    var btn = el("button", {
      class: "health-badge",
      type: "button",
      "data-state": state,
      "aria-expanded": healthPanelOpen ? "true" : "false",
      "aria-label": title,
      title: title,
    }, [
      el("span", { class: "health-dot", "aria-hidden": "true" }),
      el("span", { class: "health-label", text: label }),
    ]);
    btn.addEventListener("click", function () {
      setHealthPanelOpen(!healthPanelOpen);
    });
    slot.replaceChildren(btn);
  }

  function setHealthPanelOpen(open) {
    healthPanelOpen = open;
    saveHealthPanelOpen(open);
    renderHealthBadge();
    renderHealthPanel();
  }

  function healthPanelRow(entry) {
    var codeChip = el("span", {
      class: "health-code mono",
      text: "[" + (entry.code || "?") + "]",
    });
    var msg = el("span", { class: "health-message", text: entry.message || "" });
    var row;
    if (entry.url) {
      // Plain <a href> — the document-level click interceptor routes it
      // through navigateTo, so the centre pane swaps in-place.
      row = el("a", {
        class: "health-row",
        href: entry.url,
        title: "Open " + (entry.id || entry.rel || entry.url),
      }, [codeChip, msg]);
    } else {
      row = el("div", { class: "health-row" }, [codeChip, msg]);
    }
    return el("li", null, [row]);
  }

  function renderHealthPanel() {
    var existing = document.getElementById("cockpit-health-panel");
    if (!healthPanelOpen) {
      if (existing) existing.remove();
      return;
    }
    var panel = existing || el("aside", {
      id: "cockpit-health-panel",
      class: "health-panel",
      "aria-label": "Docs validation drift",
    });
    var state = healthState();
    var frag = document.createDocumentFragment();
    var closeBtn = el("button", {
      class: "health-panel-close", type: "button",
      "aria-label": "Close drift panel", text: "×",
    });
    closeBtn.addEventListener("click", function () { setHealthPanelOpen(false); });
    frag.appendChild(el("header", { class: "health-panel-header" }, [
      el("span", { class: "health-panel-title", text: "Docs validation" }),
      el("span", {
        class: "health-panel-checked mono",
        text: (validationCache && validationCache.checked_at)
          ? String(validationCache.checked_at).replace("T", " ").slice(0, 19)
          : "",
      }),
      closeBtn,
    ]));
    var errs = (validationCache && validationCache.errors) || [];
    var warns = (validationCache && validationCache.warnings) || [];
    if (state === "unavailable") {
      frag.appendChild(el("p", {
        class: "health-panel-empty",
        text: "Validator unavailable" +
          (validationCache && validationCache.detail
            ? ": " + validationCache.detail : "."),
      }));
    } else if (!errs.length) {
      frag.appendChild(el("p", {
        class: "health-panel-empty",
        text: "No drift — SNAPSHOT.yaml and docs/ agree.",
      }));
    } else {
      var list = el("ul", { class: "health-rows" });
      errs.forEach(function (e2) { list.appendChild(healthPanelRow(e2)); });
      frag.appendChild(list);
    }
    if (warns.length) {
      frag.appendChild(el("p", { class: "health-warn-label", text: "Warnings" }));
      var wlist = el("ul", { class: "health-rows health-rows-warn" });
      warns.forEach(function (w) { wlist.appendChild(healthPanelRow(w)); });
      frag.appendChild(wlist);
    }
    panel.replaceChildren(frag);
    if (!existing) document.body.appendChild(panel);
  }

  function mountHealthBadge() {
    renderHealthBadge();      // placeholder ("…") until the fetch lands
    renderHealthPanel();      // restore persisted open state
    fetchJson("/api/cockpit/validation")
      .then(function (payload) {
        validationCache = payload;
        renderHealthBadge();
        renderHealthPanel();
      })
      .catch(function () {
        validationCache = null;
        renderHealthBadge();
      });
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
    // Validation health (FEAT-0018 / TASK-0112): badge + drift panel
    // update live on validator state changes — no reload, no polling.
    es.addEventListener("cockpit:validation", function (ev) {
      var payload;
      try { payload = JSON.parse(ev.data); }
      catch (e) { return; }
      validationCache = payload;
      renderHealthBadge();
      renderHealthPanel();
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
      text: hideCompleted ? "Completed collapsed" : "Collapse completed",
    });
    btn.addEventListener("click", function () {
      hideCompleted = !hideCompleted;
      saveHideCompleted(hideCompleted);
      btn.classList.toggle("is-active", hideCompleted);
      btn.setAttribute("aria-pressed", hideCompleted ? "true" : "false");
      btn.textContent = hideCompleted ? "Completed collapsed" : "Collapse completed";
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
  // TASK-0271: one line — `ID  title…  chip` — at the record column's
  // height. Measured in the running desktop before and after: 60px to
  // 27px for identical text. The 33px was three second-encodings: the
  // type icon (the ID is already type-coloured), the title's own line,
  // and the icon's gutter.
  //
  // `nav-item-line`, NOT `nav-item-compact` — that class already exists
  // in this stylesheet as the Library's file row and paints a file icon
  // through ::before.
  function navItem(item) {
    var li = buildNavRow(item);
    var childrenNode = (item.children && item.children.length)
      ? renderItemChildren(item)
      : null;
    if (childrenNode) li.appendChild(childrenNode);
    return li;
  }

  // Collapsible nested children list (used for requirements under features).
  // Default = collapsed. The persisted-collapse-set storage is repurposed
  // as a persisted-OPEN set (key "nav:item-children-open:<id>") so the
  // default is the inverse of the rest of the cockpit.
  // What the children toggle says a feature carries (TASK-0367). Counts by
  // type: before tasks joined the list this said "N requirements" for every
  // child, which a feature with 3 reqs, a plan and 14 tasks reported as
  // "17 requirements".
  function childrenSummary(kids) {
    function n(type) {
      var c = 0;
      for (var i = 0; i < kids.length; i++) if (kids[i].type === type) c++;
      return c;
    }
    var reqs = n("requirement"), plans = n("plan"), tasks = n("task");
    var other = kids.length - reqs - plans - tasks;
    var parts = [];
    if (reqs) parts.push(reqs + " requirement" + (reqs === 1 ? "" : "s"));
    if (plans) parts.push(plans === 1 ? "plan" : plans + " plans");
    if (tasks) parts.push(tasks + " task" + (tasks === 1 ? "" : "s"));
    if (other) parts.push(other + " other");
    return parts.join(" \u00b7 ");
  }

  function renderItemChildren(item) {
    // Children order open-first like everything else, and are never
    // removed: a feature's completed requirements are part of what the
    // feature is.
    var visibleChildren = openFirst(item.children || []);
    if (!visibleChildren.length) return null;
    var openedKey = "nav:item-children-open:" + (item.id || item.url || "");
    var startOpen = isCollapsed(openedKey);
    var details = el("details", {
      class: "nav-item-children",
      open: startOpen ? "" : null,
    });
    var label = childrenSummary(visibleChildren);
    var summary = el("summary", { class: "nav-item-children-toggle" }, [
      el("span", { class: "nav-children-chevron", "aria-hidden": "true" }),
      el("span", { text: label }),
    ]);
    details.appendChild(summary);
    var list = el("ul", { class: "nav-item-children-list" });
    // Fold on VOLUME (TASK-0367) — tasks joined this list in TASK-0366 and
    // the largest feature carries 48. Same helper, same limit as the groups.
    var foldedKids = foldGroup(visibleChildren, NAV_GROUP_FOLD_LIMIT, hideCompleted);
    foldedKids.head.forEach(function (child) {
      list.appendChild(navItemNested(child));
    });
    if (foldedKids.hidden > 0) {
      var moreBtn = el("button", {
        type: "button",
        class: "nav-more-btn",
        text: "\u2026 " + foldedKids.hidden + " more",
        title: "Show the rest of this feature's children",
      });
      moreBtn.addEventListener("click", function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        while (list.firstChild) list.removeChild(list.firstChild);
        visibleChildren.forEach(function (c) {
          list.appendChild(navItemNested(c));
        });
      });
      list.appendChild(el("li", { class: "nav-item nav-more" }, [moreBtn]));
    }
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
  // The one row every lifecycle list uses (ISS-0085).
  //
  // There were four renderers and TASK-0271 rewrote one, so risks and
  // designs (`stacked`) and requirements and plans (`nested`) kept the old
  // two-line card. One builder now, differing only by an indent class.
  //
  // `item.subtitle` is deliberately NOT rendered: it is the second line,
  // and the server sends one for every feature (`goal`), design and risk
  // (first body paragraph). The left pane is a selection list; a summary
  // belongs in the note, not in the list of things you might open.
  function buildNavRow(item, extraClass) {
    // The id column is a COLUMN: an absent value occupies it rather than
    // skipping it, or the row lands on a different grid from its siblings
    // (ISS-0090). A plan carries `id: ""` deliberately, so its TYPE is the
    // handle — which is what an id is for a note with no number.
    var handle = item.id || (item.type ? String(item.type).toUpperCase() : "");
    var idNode = handle
      ? el("span", {
          // Display handle only — the anchor's href carries the real
          // target, and every lookup goes through that (ISS-0084).
          class: "nav-id mono ov-typed" + (item.id ? "" : " is-typeless"),
          text: item.id ? shortNoteId(item.id) : handle,
          title: item.id || handle, "data-type": item.type || null,
        })
      : null;
    var titleNode = item.title
      ? el("span", { class: "nav-title", text: item.title, title: item.title })
      : el("span", { class: "nav-line-spacer" });
    // The chip is suppressed when the whole group shares one status; the
    // head says it once instead (TASK-0272).
    var tail = itemBadges(item).concat(
      item.chipSuppressed ? [] : [statusChip(item.status)]);
    var topLine = el("div", { class: "nav-line" }, [idNode, titleNode].concat(tail));
    var card = el("a", {
      class: "nav-item nav-item-line" + (extraClass ? " " + extraClass : "")
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine]);
    return el("li", null, [card]);
  }

  // The same row, indented. Requirements and plans under features.
  function navItemNested(item) {
    return buildNavRow(item, "nav-item-nested");
  }

  // Risks and designs. Identical to the default now — "stacked" existed to
  // give a rare type more room, and more room is the thing being removed.
  // Kept as a function because the server still sends
  // `item_layout: "stacked"` and the picker still routes on it.
  function navItemStacked(item) {
    return buildNavRow(item);
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

  // A surface, drawn the same as in the desktop shell (ISS-0230). PHASE-029:
  // the two front doors answer the same questions and differ only where a
  // difference was decided — and nobody decided this one, which is why the
  // guard that checks both files found it.
  function navItemSurface(item) {
    const li = document.createElement("li");
    li.className = "nav-surface";
    const head = document.createElement("div");
    head.className = "nav-surface-head";
    const chev = document.createElement("button");
    chev.type = "button";
    chev.className = "ov-chev";
    chev.setAttribute("aria-expanded", "false");
    head.appendChild(chev);
    if (item.ref) {
      const id = document.createElement("span");
      id.className = "nav-surface-id mono is-link";
      id.textContent = item.ref;
      id.title = "Open " + item.ref;
      id.addEventListener("click", (e) => {
        e.stopPropagation();
        navigateTo("~note/" + item.ref);
      });
      head.appendChild(id);
    }
    const title = document.createElement("span");
    title.className = "nav-surface-title";
    title.textContent = item.ref_title || item.title || "";
    title.title = title.textContent;
    head.appendChild(title);
    if (item.progress) {
      const p = item.progress;
      const bar = document.createElement("span");
      bar.className = "nav-surface-bar" + (p.stale ? " has-stale" : "");
      const fill = document.createElement("i");
      fill.style.width = p.pct + "%";
      bar.appendChild(fill);
      bar.title = p.done + " of " + p.total + " completed"
        + (p.stale ? ", " + p.stale + " stale" : "");
      head.appendChild(bar);
      const pct = document.createElement("span");
      pct.className = "nav-surface-pct num";
      pct.textContent = p.pct + "%";
      head.appendChild(pct);
    }
    li.appendChild(head);
    const kids = document.createElement("ul");
    kids.className = "nav-surface-checks";
    kids.hidden = true;
    for (const kid of item.items || []) kids.appendChild(navCheckRow(kid));
    li.appendChild(kids);
    const toggle = () => {
      kids.hidden = !kids.hidden;
      li.classList.toggle("is-open", !kids.hidden);
      chev.setAttribute("aria-expanded", String(!kids.hidden));
    };
    chev.addEventListener("click", (e) => { e.stopPropagation(); toggle(); });
    head.addEventListener("click", toggle);
    head.style.cursor = "pointer";
    return li;
  }

  // One check — id, name, and its ledger MARK right-aligned. Never a runner
  // status: an acceptance check rests at `active` and its outcome is an event.
  function navCheckRow(item) {
    const li = document.createElement("li");
    li.className = "nav-check";
    const id = document.createElement("span");
    id.className = "nav-check-id mono is-link";
    id.textContent = String(item.id || "");
    li.appendChild(id);
    const name = document.createElement("span");
    name.className = "nav-check-name";
    name.textContent = item.title || "";
    name.title = item.title || "";
    li.appendChild(name);
    if (item.mark) {
      const mark = document.createElement("span");
      mark.className = "nav-check-mark";
      mark.textContent = item.mark;
      li.appendChild(mark);
    }
    return li;
  }

  function pickItemRenderer(layout) {
    if (layout === "surface") return navItemSurface;
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
    var folded = foldGroup(group.items || [], NAV_GROUP_FOLD_LIMIT, hideCompleted);
    var subUniform = uniformStatus(group.items || []) !== null;
    var visibleItems = folded.head.map(function (it) {
      return subUniform ? Object.assign({}, it, { chipSuppressed: true }) : it;
    });
    var childNodes = renderSubgroups(group, mode, depth + 1);
    // A collapsed group cuts to zero rows and is still a group — the
    // header and the count keep it visible.
    if (!visibleItems.length && !childNodes.length && !folded.hidden) return null;

    var renderItem = pickItemRenderer(group.item_layout);
    var list = el("ul", { class: "nav-items" });
    visibleItems.forEach(function (item) { list.appendChild(renderItem(item)); });
    appendMoreRow(list, folded, group, renderItem);

    var bodyChildren = [list];
    childNodes.forEach(function (node) { bodyChildren.push(node); });

    var subKey = "nav:" + mode + ":" + (group.key || "");
    var sectionExtra = group.item_layout ? " nav-group-" + group.item_layout : "";
    var indentStyle = "--tree-indent:" + String((depth || 0) * 12) + "px";
    var node = collapsibleGroup({
      defaultOpen: !groupIsSettled(group.items || []),
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

  // Nouns for the roll-up line. "16 finished phases · 54 features" reads;
  // "16 finished groups · 54 items" does not, and saying what is behind
  // the line is the whole value of collapsing to one.
  var ROLLUP_NOUNS = {
    // A rung, not a group (FEAT-0102): the ladder's units are what
    // publication is about. Mirrored from renderer.ts, which
    // `test_the_two_surfaces_agree_on_the_rollup_nouns` pins.
    publication: { group: ["rung", "rungs"], item: ["item", "items"] },
    features: { group: ["phase", "phases"], item: ["feature", "features"] },
    tasks:    { group: ["bucket", "buckets"], item: ["task", "tasks"] },
    issues:   { group: ["bucket", "buckets"], item: ["issue", "issues"] },
    // `tests` has no button in this front door yet — the Tests view landed in
    // the shell first (TASK-0371) and PHASE-029 owns the alignment. The noun
    // is here because `mode=tests` is served and reachable by URL, and
    // because the parity guard is the reason the two tables have not drifted.
    tests:    { group: ["group", "groups"], item: ["test", "tests"] },
    design:   { group: ["group", "groups"], item: ["design", "designs"] },
    library:  { group: ["group", "groups"], item: ["note", "notes"] },
    review:   { group: ["verdict", "verdicts"], item: ["note", "notes"] },
    _default: { group: ["group", "groups"], item: ["item", "items"] },
  };
  function plural(n, pair) { return n === 1 ? pair[0] : pair[1]; }

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

    // TASK-0273: groups still holding open work render normally; every
    // finished one goes below a divider as ONE expandable line. Sixteen
    // finished phases cost 53px of header each before this.
    // TASK-0276: the tasks navigator groups BY status, so `Done`,
    // `Cancelled` and `Superseded` already name their own state and a
    // divider reading "Completed" would be the word four times over.
    // Everywhere else the group name is on some other axis and says
    // nothing about state, so the divider is the only thing that can.
    var namesStateThemselves = mode === "tasks";
    var liveGroups = [], settledGroups = [];
    groups.forEach(function (g) {
      (!namesStateThemselves && groupIsSettled(g.items || [])
        ? settledGroups : liveGroups).push(g);
    });
    var rollupFrag = settledGroups.length ? document.createDocumentFragment() : null;

    // Where a divider names the finished set, the live set gets a heading
    // too — a set with no name is not one (ISS-0089).
    if (liveGroups.length && settledGroups.length && !namesStateThemselves) {
      frag.appendChild(el("div", {
        class: "nav-set-heading", text: "Open \u00b7 " + liveGroups.length,
      }));
    }

    var anyVisible = false;
    liveGroups.concat(settledGroups).forEach(function (g) {
      var intoRollup = settledGroups.indexOf(g) !== -1;
      var folded = foldGroup(g.items || [], NAV_GROUP_FOLD_LIMIT, hideCompleted);
      // When the head says the status once, the rows must not repeat it.
      var gUniform = uniformStatus(g.items || []) !== null;
      var visibleItems = folded.head.map(function (it) {
        return gUniform ? Object.assign({}, it, { chipSuppressed: true }) : it;
      });
      var subgroupNodes = renderSubgroups(g, mode);
      if (!visibleItems.length && !subgroupNodes.length && !folded.hidden) return;
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
      // ISS-0088: the head uses the ROW's grammar — a type-coloured ID and
      // a name — not an icon plus one flat string.
      var split = /^([A-Z]+-\d+)\s*\u00b7\s*(.*)$/.exec(label);
      // A features head names a THING, not a category, so it renders at
      // row weight rather than in the faint label treatment (ISS-0089).
      var headerClass = "nav-group-header" + (mode === "features" ? " is-thing" : "");
      var headerChildren = split
        ? [el("span", { class: "nav-id mono ov-typed", "data-type": "phase", text: split[1] }),
           el("span", { class: "group-header-name", text: split[2], title: split[2] })]
        : [titleNode];
      headerChildren.push(el("span", { class: "nav-group-spacer" }));
      // The head carries the count, and the status when every item shares
      // one (TASK-0272) — the record card's `7 · all accepted` move.
      // Where the group name IS the status, the summary is the count
      // alone — `Done · 265`, not `Done · 265 · done`.
      var gSummary = namesStateThemselves
        ? String((g.items || []).length || "")
        : groupHeadSummary(g.items || []);
      // ISS-0241: a head that already carries counts gets no second one.
      // The label counts CHECKS and this counts nav ROWS — `361/406` beside
      // `50 · 1 done`, two populations, no way to tell them apart. Read off a
      // server flag rather than sniffed from the label: every other group's
      // trailing count is the ONLY count it has, and must survive.
      if (g.head_counts) gSummary = "";
      if (gSummary) {
        headerChildren.push(el("span", { class: "nav-group-summary", text: gSummary }));
      }
      // A group's OWN status is a different fact from its items' — a done
      // phase can hold an open issue — so it survives unless it would
      // restate the summary.
      // Shown unless the group's own NAME already says it — a `done` pill
      // on a card called `Done` is the word twice (ISS-0089).
      // No pill where the head names a thing — the overview's scope rows
      // never had one, and inside a `Completed` band it is the word a
      // third time (ISS-0090).
      if (g.status && !namesStateThemselves && mode !== "features") {
        headerChildren.push(statusChip(g.status));
      }

      var renderItem = pickItemRenderer(g.item_layout);
      var list = el("ul", { class: "nav-items" });
      visibleItems.forEach(function (item) { list.appendChild(renderItem(item)); });
      appendMoreRow(list, folded, g, renderItem);

      var bodyChildren = [list];
      subgroupNodes.forEach(function (n) { bodyChildren.push(n); });

      var sectionExtra = g.item_layout ? " nav-group-" + g.item_layout : "";
      var key = "nav:" + mode + ":" + (g.key || label || "unkeyed");
      (intoRollup ? rollupFrag : frag).appendChild(collapsibleGroup({
        key: key,
        sectionClass: "nav-group" + sectionExtra,
        headerClass: headerClass,
        headerChildren: headerChildren,
        bodyChildren: bodyChildren,
        // TASK-0275: a settled group opens SHUT, the context pane's own
        // rule. A shut card still carries its name and count.
        defaultOpen: !groupIsSettled(g.items || []),
      }));
    });

    if (rollupFrag) {
      var nItems = 0;
      settledGroups.forEach(function (g) { nItems += (g.items || []).length; });
      var nouns = ROLLUP_NOUNS[mode] || ROLLUP_NOUNS._default;
      // The counts are never optional: a roll-up that does not say how
      // much it rolled up is indistinguishable from an empty pane.
      // `Completed · N` — the overview's exact wording (its scope pane has
      // said this since FEAT-0043), so one idea does not wear two names
      // across two panes. Defaults OPEN: collapsing a group's BODY hides
      // items nobody is working on, but collapsing its HEAD hides which
      // phases exist at all, and that is a taxonomy rather than a backlog
      // (ISS-0086). `collapsibleGroup` persists the divergence from this
      // default, so closing it sticks.
      frag.appendChild(collapsibleGroup({
        key: "nav:" + mode + ":__settled",
        sectionClass: "nav-group nav-rollup",
        headerClass: "nav-group-header nav-rollup-header",
        defaultOpen: true,
        headerChildren: [
          el("span", {
            class: "nav-rollup-label",
            text: "Completed \u00b7 " + settledGroups.length,
          }),
          el("span", {
            class: "nav-rollup-sub",
            text: nItems + " " + plural(nItems, nouns.item),
          }),
        ],
        bodyChildren: [rollupFrag],
      }));
      anyVisible = true;
    }

    if (!anyVisible) {
      // Since FEAT-0056 a group folds but never disappears, so this can
      // only mean the mode genuinely has nothing in it.
      frag.appendChild(el("p", {
        class: "cockpit-empty",
        text: "Nothing in this view yet.",
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
    ].concat(itemBadges(item), [statusChip(item.status)]));
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
      // The context pane orders by state and NEVER filters by it. The
      // left pane is a selection list, where a completed item is one you
      // are not going to click; this pane is a DESCRIPTION, and a note's
      // completed children are what the note is made of. Filtering here
      // emptied the pane of every finished note.
      // Ordered, never filtered — but still folded on LENGTH: 11 of 3192
      // context groups exceed the limit and the largest real one is 79.
      var foldedLinked = contextGroupRows(g.linked, NAV_GROUP_FOLD_LIMIT);
      var foldedInbound = contextGroupRows(g.inbound, NAV_GROUP_FOLD_LIMIT);
      var ctxUniform = uniformStatus(
        (g.linked || []).concat(g.inbound || [])) !== null;
      var suppress = function (it) {
        return ctxUniform ? Object.assign({}, it, { chipSuppressed: true }) : it;
      };
      var visibleLinked = foldedLinked.head.map(suppress);
      var visibleInbound = foldedInbound.head.map(suppress);
      if (!visibleLinked.length && !visibleInbound.length
          && !foldedLinked.hidden && !foldedInbound.hidden) return;
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
      appendCtxMoreRow(list, foldedLinked, g.linked, "linked");
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
      appendCtxMoreRow(list, foldedInbound, g.inbound, "inbound");

      // TASK-0274: the card head carries the count and, when uniform, the
      // status; a card whose every link is terminal starts CLOSED.
      //
      // Closing a body is not filtering, and that distinction is why this
      // is allowed where the old filter was not: a closed card still says
      // the relationship exists, its type and how many. The filter said
      // nothing at all. `contextGroupRows` still has no parameter to
      // filter with.
      var allItems = (g.linked || []).concat(g.inbound || []);
      var ctxSummary = groupHeadSummary(allItems);
      if (ctxSummary) {
        typeLabel.appendChild(el("span", { class: "ctx-card-right", text: ctxSummary }));
      }
      var key = "ctx:" + (typeName || "_untyped");
      container.appendChild(collapsibleGroup({
        key: key,
        sectionClass: "ctx-group",
        headerClass: "ctx-group-header",
        headerChildren: [typeLabel],
        bodyChildren: [list],
        defaultOpen: !groupIsSettled(allItems),
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
    // `~root/<file>` is the nav payload's shape for a top-level project file
    // (ISS-0037). Mode 3 needs that prefix because its `extractRel` cannot
    // otherwise tell `/README.md` from the docs note of the same name — but
    // mode 1 fetches the URL as a page, and `GET /README.md` has always served
    // the project file correctly. So translate rather than route: the prefix is
    // a rel-space disambiguator, not an HTTP path.
    //
    // Restores what ISS-0037's fix broke here: the payload changed under this
    // client and `GET /~root/README.md` 404'd, so mode 3 gained a working link
    // and mode 1 lost one (ISS-0071).
    if (url && url.indexOf("~root/") === 0) url = "/" + url.slice(6);
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
  mountHealthBadge();
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
