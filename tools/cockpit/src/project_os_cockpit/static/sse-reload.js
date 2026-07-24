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
 */
(function () {
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
