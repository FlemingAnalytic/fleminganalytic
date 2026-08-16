/**
 * The shapes the report canvas is built from.
 *
 * A visual is a description of a question, not a chart. Its field wells map
 * onto /analyst/pivot's arguments, so changing a visual's type - a matrix to
 * a column chart - asks the backend nothing new and redraws from data
 * already in the cache.
 */

/**
 * @typedef {Object} FieldWells
 * @property {string[]} rows    -> pivot.rows    (the axis / row headers)
 * @property {string[]} cols    -> pivot.cols    (the legend / column headers)
 * @property {string[]} values  -> pivot.values  (the measure)
 * @property {string}   agg     -> pivot.aggfunc
 * @property {?string}  weightCol -> pivot.weight_col, only for weighted_avg
 */

/**
 * @typedef {Object} Visual
 * @property {string} id
 * @property {'matrix'|'column'} type
 * @property {?string} title           null -> derived from the wells
 * @property {FieldWells} fieldWells
 * @property {{x:number,y:number,w:number,h:number}} position  12-column grid
 * @property {Object<string,(string|number)[]>} filters        visual-level
 * @property {{crossFilter:boolean}} interactions
 */

/** Aggregations PivotEngine.create_pivot accepts, in the order to offer them. */
export const AGGREGATIONS = [
    { value: 'sum', label: 'Sum' },
    { value: 'mean', label: 'Average' },
    { value: 'count', label: 'Count' },
    { value: 'median', label: 'Median' },
    { value: 'min', label: 'Min' },
    { value: 'max', label: 'Max' },
    { value: 'nunique', label: 'Distinct count' },
    { value: 'std', label: 'Std deviation' },
    { value: 'p25', label: '25th percentile' },
    { value: 'p75', label: '75th percentile' },
    { value: 'p90', label: '90th percentile' },
    { value: 'weighted_avg', label: 'Weighted average' },
];

export const VISUAL_TYPES = [
    { type: 'matrix', label: 'Matrix', hint: 'Rows, columns and totals' },
    { type: 'column', label: 'Column chart', hint: 'Compare categories' },
];

/**
 * A dimension with more distinct values than this makes an unreadable axis.
 * The backend has no top-N, so the whole result arrives either way; this is
 * where the chart decides to show the top slice and say that it has.
 */
export const AXIS_CARDINALITY_LIMIT = 50;

let counter = 0;
export function newVisualId() {
    counter += 1;
    return `v_${counter.toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

export function createVisual(overrides = {}) {
    return {
        id: newVisualId(),
        type: 'column',
        title: null,
        fieldWells: { rows: [], cols: [], values: [], agg: 'sum', weightCol: null },
        position: { x: 0, y: 0, w: 6, h: 4 },
        filters: {},
        interactions: { crossFilter: true },
        ...overrides,
        fieldWells: {
            rows: [], cols: [], values: [], agg: 'sum', weightCol: null,
            ...(overrides.fieldWells || {}),
        },
    };
}

export function emptyReport(filename = null) {
    return {
        version: 1,
        filename,
        pages: [{ id: 'p1', name: 'Page 1', visuals: [] }],
        activePageId: 'p1',
        selectedVisualId: null,
        filters: { page: {}, slicers: {}, crossFilter: null },
    };
}
