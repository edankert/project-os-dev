/* project-os-cockpit soft-reload over SSE.
 *
 * Each rendered page carries:
 *   <meta name="project-os-cockpit:source" content="<rel-path-or-*>">
 *
 * - rel-path: the docs-root-relative .md path. Reload only when that path
 *   changes (note pages render this).
 * - "*"    : reload on any file event (used by index, landing, and
 *   directory-listing pages, which depend on the whole tree).
 *
 * The browser's EventSource auto-reconnects with backoff when the server
 * restarts; nothing extra is needed here for that.
 *
 * Cockpit pages are handled separately: cockpit.js does a soft pane-by-
 * pane refresh in response to `file-changed` (TASK-0014) so the embedded
 * terminal session survives. When the cockpit shell is mounted on this
 * page (presence of #cockpit-centre), bail — the full `location.reload()`
 * below would tear down the iframe.
 */
(function () {
  if (document.getElementById("cockpit-centre")) return;

  var meta = document.querySelector('meta[name="project-os-cockpit:source"]');
  if (!meta) return;
  var source = meta.getAttribute("content") || "";
  if (!source) return;

  var es;
  try {
    es = new EventSource("/_events");
  } catch (e) {
    return;
  }

  function shouldReload(changed) {
    if (source === "*") return true;
    return source === changed;
  }

  es.addEventListener("file-changed", function (ev) {
    if (shouldReload(ev.data)) {
      // Small delay so a save burst finishes before we re-fetch.
      setTimeout(function () { location.reload(); }, 80);
    }
  });

  // Best-effort cleanup on tab close.
  window.addEventListener("beforeunload", function () {
    try { es.close(); } catch (e) {}
  });
})();
