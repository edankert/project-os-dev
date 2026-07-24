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

  function thisParam() {
    return active.id || active.path || "";
  }

  // Generic collapsible group via <details>/<summary>. Native browser toggling;
  // persists open/closed state under `collapsed[key]` in localStorage.
  function collapsibleGroup(opts) {
    // opts: { key, headerClass, headerStyle, headerChildren, bodyStyle, bodyChildren, sectionClass }
    var startCollapsed = isCollapsed(opts.key);
    var details = el("details", {
      class: opts.sectionClass || "",
      open: startCollapsed ? null : "",
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
      var nowCollapsed = !details.open;
      var stored = isCollapsed(opts.key);
      if (nowCollapsed !== stored) toggleCollapsed(opts.key);
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
        if (mode.id === navMode) return;
        navMode = mode.id;
        saveMode(navMode);
        navCache = null;
        // Update the active-tab styling in place; loadLeftPane re-renders the pane only.
        bar.querySelectorAll(".nav-mode-tab").forEach(function (b) {
          var isActive = b.getAttribute("data-mode") === navMode;
          b.classList.toggle("is-active", isActive);
          b.setAttribute("aria-selected", isActive ? "true" : "false");
        });
        loadLeftPane().then(highlightActiveInLeftPane);
      });
      bar.appendChild(btn);
    });
    slot.replaceChildren(bar);
  }

  // Default layout: status + id + title on a single line, optional subtitle below.
  // Used by Features / Tasks / Issues / Recent modes.
  function navItem(item) {
    var titleSpan = el("span", {
      class: "nav-title",
      text: item.title || item.id || "",
      title: item.title || "",
    });
    var topLine = el("div", { class: "nav-line" }, [
      statusChip(item.status),
      item.id ? el("span", { class: "nav-id mono", text: item.id }) : null,
      titleSpan,
    ]);
    var subtitle = item.subtitle
      ? el("p", { class: "nav-subtitle", text: item.subtitle, title: item.subtitle })
      : null;
    var card = el("a", {
      class: "nav-item" + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine, subtitle]);
    return el("li", null, [card]);
  }

  // Stacked layout: status + id on the top line, title on a second line.
  // Used by Project mode's pinned and rare-types sections — same shape as
  // the right pane's relationship items.
  function navItemStacked(item) {
    var topLine = el("div", { class: "nav-line" }, [
      statusChip(item.status),
      item.id ? el("span", { class: "nav-id mono", text: item.id }) : null,
    ]);
    var titleNode = el("p", {
      class: "nav-title-stacked",
      text: item.title || item.id || "",
      title: item.title || "",
    });
    var card = el("a", {
      class: "nav-item nav-item-stacked"
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [topLine, titleNode]);
    return el("li", null, [card]);
  }

  // Compact layout: filename only, single line, tight padding.
  // Used by Project mode's docs/reference directory trees.
  function navItemCompact(item) {
    var titleSpan = el("span", {
      class: "nav-title-compact",
      text: item.title || "",
      title: item.title || "",
    });
    var card = el("a", {
      class: "nav-item nav-item-compact"
        + (item.url === active.url ? " is-active" : ""),
      href: item.url,
    }, [titleSpan]);
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
    return collapsibleGroup({
      key: subKey,
      sectionClass: "nav-subgroup" + sectionExtra,
      headerClass: "nav-subgroup-header",
      headerStyle: "--tree-indent:" + String((depth || 0) * 12) + "px",
      bodyStyle: "--tree-indent:" + String((depth || 0) * 12) + "px",
      headerChildren: [el("span", { text: group.label || group.key || "" })],
      bodyChildren: bodyChildren,
    });
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
      var headerChildren = [titleNode];
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
    var priority = item.priority
      ? el("span", {
          class: "ctx-priority",
          "data-priority": String(item.priority).toLowerCase(),
          text: item.priority,
        })
      : null;
    var topLine = el("div", { class: "ctx-line" }, [
      statusChip(item.status),
      item.id ? el("span", { class: "ctx-id mono", text: item.id }) : null,
      priority,
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
  function mergeContext(linked, backlinks) {
    var byType = {};
    var order = [];
    function pushGroup(group, kind) {
      if (!group || !group.items) return;
      var t = String(group.type || "").toLowerCase();
      if (!byType[t]) {
        byType[t] = { type: t, linked: [], inbound: [] };
        order.push(t);
      }
      group.items.forEach(function (it) {
        byType[t][kind].push(it);
      });
    }
    (linked || []).forEach(function (g) { pushGroup(g, "linked"); });
    (backlinks || []).forEach(function (g) { pushGroup(g, "inbound"); });
    return order.map(function (t) { return byType[t]; });
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
        text: pluralizeType(typeName),
      });
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

  function isInternalNoteLink(href) {
    if (!href) return false;
    if (href.indexOf("#") === 0) return false;
    var pathOnly = href.split(/[?#]/)[0];
    if (!/\.md$/i.test(pathOnly)) return false;
    if (/^\/docs\//.test(pathOnly)) return true;
    return /^\/(README|ROADMAP|SECURITY)\.md$/.test(pathOnly);
  }

  function setActiveFromUrl(url) {
    var u = new URL(url, document.location.origin);
    active.url = u.pathname;
    if (/^\/docs\//.test(u.pathname)) {
      active.path = u.pathname.replace(/^\/docs\//, "");
    } else if (isInternalNoteLink(u.pathname)) {
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
        centreEl.scrollTop = 0;
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
  mountPinButton();
  loadLeftPane().then(highlightActiveInLeftPane);
  loadRightPane();
})();
