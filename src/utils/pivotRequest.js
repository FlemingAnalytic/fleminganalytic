/**
 * Turning a visual's field wells into a /analyst/pivot request, and into a
 * cache key.
 *
 * Every visual on the canvas queries through this one endpoint - a matrix, a
 * column chart and a KPI card differ in how they draw a result, not in how
 * they ask for one. That is what makes cross-filtering tractable: there is a
 * single request shape to add a filter to.
 */

/**
 * @param {string} filename  session key returned by the load call, e.g. 'saved_chicagoland'
 * @param {object} visual    a visual spec (see state/reportTypes.js)
 * @param {object} filters   already merged and coerced by filterMerge.js
 */
export function buildPivotRequest(filename, visual, filters) {
    const { rows = [], cols = [], values = [], agg, weightCol } = visual.fieldWells || {};
    return {
        filename,
        rows,
        // The backend distinguishes "no column dimension" from "an empty
        // one": null takes the groupby path, [] takes pivot_table and fails.
        cols: cols.length ? cols : null,
        values: values.length ? values : null,
        aggfunc: agg || 'sum',
        filters: filters && Object.keys(filters).length ? filters : null,
        weight_col: weightCol || null,
    };
}

/**
 * True when a request can actually be answered.
 *
 * `rows: []` is not an empty result, it is a 200 with
 * {"error": "No group keys passed!"} - the backend's groupby path has no
 * grand-total branch. Asking anyway costs a round trip to be told something
 * we already know, so tiles with an empty Rows well show "add a field"
 * instead of an error.
 */
export function isQueryable(visual) {
    const { rows = [], values = [] } = visual.fieldWells || {};
    return rows.length > 0 && values.length > 0;
}

/**
 * A stable key for the cache.
 *
 * Both the object keys and the filter value arrays are sorted, so two tiles
 * that ask the same question in a different order share one cache entry and
 * one in-flight request. Without the inner sort, clicking two bars in the
 * other order would miss a cache entry that holds the exact answer.
 */
export function pivotKey(request) {
    const norm = (value) => {
        if (Array.isArray(value)) return [...value].map(norm).sort();
        if (value && typeof value === 'object') {
            return Object.keys(value).sort().reduce((out, k) => {
                out[k] = norm(value[k]);
                return out;
            }, {});
        }
        return value;
    };
    return JSON.stringify(norm(request));
}

/** A readable title for a tile the user has not named. */
export function describeWells(wells) {
    const { rows = [], cols = [], values = [], agg = 'sum' } = wells || {};
    if (!values.length && !rows.length) return 'Empty visual';
    const AGG_LABEL = {
        sum: 'Sum', mean: 'Average', count: 'Count', median: 'Median',
        min: 'Min', max: 'Max', nunique: 'Distinct', std: 'Std dev',
        var: 'Variance', p25: '25th pct', p75: '75th pct', p90: '90th pct',
        weighted_avg: 'Weighted avg', first: 'First', last: 'Last',
    };
    const measure = values.length
        ? `${AGG_LABEL[agg] || agg} of ${values.join(', ')}`
        : 'Value';
    const by = rows.length ? ` by ${rows.join(', ')}` : '';
    const split = cols.length ? ` split by ${cols.join(', ')}` : '';
    return `${measure}${by}${split}`;
}
