/**
 * Cleaning up what /analyst/pivot returns, before anything draws it.
 *
 * The response carries totals that cannot be trusted. `PivotEngine` has two
 * code paths and they disagree:
 *
 *   - with column dimensions it uses pandas `pivot_table(margins=True)`,
 *     whose margins are computed over the underlying rows and are correct;
 *   - without them it appends its own `_is_total` row built as
 *     `pivot[col].sum()` regardless of the aggregation asked for.
 *
 * So a mean-aggregated pivot returns a TOTAL that is the sum of the group
 * means. Verified on chicagoland: six county means of roughly 2.4k-3.4k sqft
 * come back with a TOTAL of 16,872 - a number that is not the mean of
 * anything and is nearly six times the real dataset mean. Charting it would
 * draw one bar dwarfing every real category.
 *
 * Nothing here tries to repair those numbers. It removes them, and a visual
 * that wants a footer re-derives it from the rows it can see, which is only
 * honest for sum and count.
 */

/** Aggregations where a total can be recomputed from group results. */
const RECOMPOSABLE = new Set(['sum', 'count']);

/**
 * Strip every total row and column from a pivot result.
 *
 * @param {object} result  raw response: { data, columns, has_col_dims, row_dims }
 * @returns {{rows: object[], columns: string[], rowDims: string[]}}
 */
export function stripTotals(result) {
    const rowDims = result.row_dims || [];
    const firstDim = rowDims[0];

    const rows = (result.data || []).filter((row) => {
        if (row._is_total) return false;
        // pivot_table(margins=True) labels its margin row "Total" in the
        // first row dimension rather than flagging it.
        if (firstDim && row[firstDim] === 'Total') return false;
        return true;
    });

    // ...and the matching margin column, which is named "Total" outright.
    const columns = (result.columns || []).filter((c) => c !== 'Total');

    return { rows, columns, rowDims };
}

/**
 * A footer for the matrix, or null when one cannot honestly be produced.
 *
 * Sums and counts are additive, so folding the visible rows gives the same
 * answer the backend would. Means, medians and percentiles are not - a mean
 * of means is only the true mean when every group is the same size, and
 * there is no way to know that from the response. Those return null and the
 * matrix simply shows no total, which is better than a number that looks
 * authoritative and is wrong.
 */
export function deriveTotals(rows, measureColumns, agg) {
    if (!RECOMPOSABLE.has(agg) || !rows.length) return null;
    const totals = {};
    for (const col of measureColumns) {
        let sum = 0;
        let sawNumber = false;
        for (const row of rows) {
            const v = row[col];
            if (typeof v === 'number' && Number.isFinite(v)) {
                sum += v;
                sawNumber = true;
            }
        }
        if (sawNumber) totals[col] = sum;
    }
    return Object.keys(totals).length ? totals : null;
}

/**
 * Which returned columns hold measures rather than the row dimensions.
 *
 * With column dimensions the names are flattened by the backend as
 * "North | 2024", so they cannot be matched against the Values well by name -
 * anything that is not a row dimension is a measure.
 */
export function measureColumns(columns, rowDims) {
    const dims = new Set(rowDims);
    return columns.filter((c) => !dims.has(c));
}

/**
 * Sort descending by a measure and keep the top N.
 *
 * /analyst/pivot has no limit or sort, so a dimension with 31,864 distinct
 * values (chicagoland's `address`) returns all of them. The payload is
 * already paid for by the time this runs - this only stops the chart from
 * trying to draw it. The tile says so rather than silently showing a slice.
 */
export function topN(rows, measure, n) {
    if (!measure || rows.length <= n) return { rows, truncated: false };
    const sorted = [...rows].sort((a, b) => (b[measure] ?? -Infinity) - (a[measure] ?? -Infinity));
    return { rows: sorted.slice(0, n), truncated: true };
}
