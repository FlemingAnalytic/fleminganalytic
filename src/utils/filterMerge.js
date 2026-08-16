/**
 * Working out what a single visual is actually filtered by.
 *
 * A tile is never filtered by one thing. It sees the page filters, every
 * slicer on the canvas, whatever the user last clicked in another visual,
 * and its own visual-level filters - and it has to combine them the way a
 * reader expects: values within one column are alternatives, and separate
 * columns all have to hold at once.
 *
 * Two rules stop this from feeding back on itself:
 *   - a slicer does not filter itself, or picking a value would erase the
 *     other options from its own list;
 *   - the visual that owns the current selection is not filtered by it, so
 *     clicking a bar leaves its neighbours visible instead of collapsing the
 *     chart to the one bar just clicked.
 */

/**
 * Combine filter layers. Same column in two layers -> intersection, because
 * two filters both applying is narrower than either alone.
 */
function intersectByColumn(layers) {
    const out = {};
    for (const layer of layers) {
        if (!layer) continue;
        for (const [column, values] of Object.entries(layer)) {
            if (!values || !values.length) continue;
            if (!(column in out)) {
                out[column] = [...values];
            } else {
                const keep = new Set(values.map(String));
                out[column] = out[column].filter((v) => keep.has(String(v)));
            }
        }
    }
    return out;
}

/**
 * Put filter values back into the dtype the dataframe holds.
 *
 * `PivotEngine` filters with `work_df[col].isin(values)`, which compares
 * against the raw dtype, while /analyst/filter-values returns everything as
 * strings - a numeric column comes back as ["-1.0", "1.0", "2.0", "3.0"].
 * Send those strings straight back and `isin` matches nothing: the response
 * is {"error": "No data after filters"}, with a 200 status and no hint that
 * a type is at fault. Verified on chicagoland's `bedrooms`: filtering on "3"
 * returns nothing, filtering on 3 works.
 *
 * Selections made by clicking a chart are already correctly typed, since
 * they came out of a pivot response as JSON numbers. It is the slicer values
 * that need this. Doing it here, once, on the way out, means no caller has
 * to remember which source a value came from.
 */
export function coerceFilterValues(filters, profile) {
    const columns = profile?.columns || {};
    const out = {};
    for (const [column, values] of Object.entries(filters || {})) {
        const type = columns[column]?.type;
        const numeric = type === 'continuous' || type === 'categorical_numeric';
        out[column] = values.map((v) => {
            if (!numeric) return String(v);
            const n = Number(v);
            // A numeric column can still hold an unparseable label; leaving
            // it as a string at least matches an object-dtype column.
            return Number.isFinite(n) ? n : v;
        });
    }
    return out;
}

/** Every visual on the active page. */
export function activeVisuals(report) {
    const page = report.pages.find((p) => p.id === report.activePageId);
    return page ? page.visuals : [];
}

export function findVisual(report, visualId) {
    return activeVisuals(report).find((v) => v.id === visualId) || null;
}

/**
 * The filters that apply to one visual, ready to send.
 *
 * @param {object} report   the report state
 * @param {string} visualId the visual asking
 * @param {object} profile  the dataset profile, for column types
 */
export function effectiveFilters(report, visualId, profile) {
    const { page = {}, slicers = {}, crossFilter = null } = report.filters || {};

    const slicerLayers = Object.entries(slicers)
        .filter(([tileId]) => tileId !== visualId)
        .map(([, s]) => (s && s.column && s.values?.length ? { [s.column]: s.values } : null));

    const crossLayer =
        crossFilter && crossFilter.sourceId !== visualId && crossFilter.values?.length
            ? { [crossFilter.column]: crossFilter.values }
            : null;

    const visual = findVisual(report, visualId);

    const merged = intersectByColumn([page, ...slicerLayers, crossLayer, visual?.filters]);
    return coerceFilterValues(merged, profile);
}

/** How many filters are active anywhere - for the header chip. */
export function activeFilterCount(report) {
    const { page = {}, slicers = {}, crossFilter = null } = report.filters || {};
    let n = Object.values(page).filter((v) => v?.length).length;
    n += Object.values(slicers).filter((s) => s?.values?.length).length;
    if (crossFilter?.values?.length) n += 1;
    return n;
}

/** Labels for the filter glyph tooltip on a tile. */
export function describeFilters(filters) {
    return Object.entries(filters || {}).map(([column, values]) => {
        const shown = values.slice(0, 3).join(', ');
        const more = values.length > 3 ? ` +${values.length - 3}` : '';
        return `${column}: ${shown}${more}`;
    });
}
