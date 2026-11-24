import { createVisual } from '../state/reportTypes';

/**
 * Putting a field into a visual's wells, shared by clicking a field and
 * dragging one onto a well.
 *
 * Built like Excel's pivot field list (2026-11-24): with nothing selected, a
 * field starts a new Matrix instead of doing nothing, and the aggregation
 * follows the field the way Excel's does where the default would be wrong.
 */

/** The MIME type a dragged field travels under. */
export const FIELD_MIME = 'application/x-analyst-field';

/**
 * A rate or score: its sum is meaningless and its average is the answer
 * (a 0/100 late flag averages to the % late). Same name rule the profiler
 * uses to call these columns measures.
 */
export function isRateLike(name) {
    const n = String(name || '').toLowerCase();
    return /(_pct|_percent|_rate)$/.test(n) || n.endsWith('score');
}

/** The well a field goes to when it is clicked rather than dropped. */
export function defaultWell(column, wells) {
    if (column.role === 'measure') return 'values';
    if (!wells) return 'rows';
    return wells.rows.length && !wells.cols.length ? 'cols' : 'rows';
}

/** The aggregation to use once `column` is in Values, or null to leave it. */
function aggFor(column, wells) {
    if (wells.values.length) return null;          // the visual already has a verb
    if (column.role !== 'measure') return 'count';  // Excel: text in Values counts
    if (isRateLike(column.name) && wells.agg === 'sum') return 'mean';
    return null;
}

/**
 * Add `column` to `well` of `visual`, or to a new Matrix when `visual` is
 * null. A field already grouping the visual cannot also be its value -
 * "count of X by X" puts the count in the label column and shows a column of
 * 1s (2026-11-23) - so that drop is ignored.
 */
export function placeField(dispatch, visual, column, well = defaultWell(column, visual?.fieldWells)) {
    if (!visual) {
        const empty = createVisual().fieldWells;
        const agg = well === 'values' ? aggFor(column, empty) : null;
        dispatch({
            type: 'ADD_VISUAL',
            visual: createVisual({
                type: 'matrix',
                fieldWells: { [well]: [column.name], ...(agg ? { agg } : {}) },
            }),
        });
        return true;
    }
    const w = visual.fieldWells;
    const grouping = [...w.rows, ...w.cols];
    if (well === 'values' && grouping.includes(column.name)) return false;
    if ((well === 'rows' || well === 'cols') && w.values.includes(column.name)) return false;

    if (well === 'values') {
        const agg = aggFor(column, w);
        if (agg) dispatch({ type: 'SET_AGG', visualId: visual.id, agg });
    }
    dispatch({ type: 'ASSIGN_FIELD', visualId: visual.id, well, field: column.name });
    return true;
}
