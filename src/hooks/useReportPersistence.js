/**
 * Saving a report layout, in the browser.
 *
 * Not on the server, for two reasons that both have to change before that is
 * the right call. The backend's dataset sessions are an in-process dict that
 * a restart empties, so a report stored against `saved_chicagoland` would
 * outlive the thing it describes. And /analyst/* has no authentication at
 * all - adding a save endpoint would put an unauthenticated write on a
 * public host, which is a larger decision than a layout feature deserves to
 * make on its own.
 *
 * Export and import cover the case localStorage does not: getting a report
 * to somebody else.
 */

const PREFIX = 'analyst_report_v1:';
const VERSION = 1;

export function loadReport(filename) {
    try {
        const raw = localStorage.getItem(PREFIX + filename);
        if (!raw) return null;
        const report = JSON.parse(raw);
        // A report from an older shape is discarded rather than migrated:
        // there is one version so far, and a half-understood layout is worse
        // than the seeded default the caller falls back to.
        if (report?.version !== VERSION) return null;
        if (report.filename !== filename) return null;
        return report;
    } catch {
        // A corrupt entry, or storage disabled entirely (private browsing,
        // an embedded webview). Neither is worth failing the page over.
        return null;
    }
}

export function saveReport(filename, report) {
    try {
        localStorage.setItem(PREFIX + filename, JSON.stringify(report));
        return true;
    } catch {
        return false;
    }
}

export function clearReport(filename) {
    try {
        localStorage.removeItem(PREFIX + filename);
    } catch {
        /* nothing to do - the layout simply stays */
    }
}

/** Download the report as JSON, for sharing or keeping. */
export function exportReport(report, displayName) {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(displayName || report.filename || 'report').replace(/\W+/g, '_')}.report.json`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Read a report file back.
 *
 * The filename is rewritten to the session currently loaded. A shared report
 * describes a set of questions about a shape of data; the session key it was
 * built against is local to whoever exported it and means nothing here. If
 * the columns do not match, the wells will name fields that are missing and
 * those tiles will say so - which is a clearer failure than refusing the
 * import outright.
 */
export function parseReport(text, filename) {
    const report = JSON.parse(text);
    if (report?.version !== VERSION) throw new Error('Unsupported report version');
    if (!Array.isArray(report.pages)) throw new Error('Not a report file');
    return {
        ...report,
        filename,
        selectedVisualId: null,
        filters: { page: {}, slicers: {}, crossFilter: null, ...(report.filters || {}) },
    };
}
