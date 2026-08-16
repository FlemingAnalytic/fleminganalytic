/**
 * The one place chart colour and chart furniture are decided.
 *
 * Before this file, the app had a single chart with `#3b82f6` and its
 * tooltip styles written inline. Eight visual types doing that would be
 * eight slightly different charts sharing a page.
 *
 * The categorical palette is validated, not chosen by eye: eight slots on
 * the #0f0f11 tile surface, checked for lightness band, chroma floor,
 * adjacent-pair separation under protanopia and tritanopia, a normal-vision
 * floor, and 3:1 contrast against the surface. Worst adjacent pair is
 * amber/green at deltaE 8.4 under protan - above the 8 threshold, so the
 * colours stand alone without needing texture to tell them apart. If any
 * value here changes, re-run the dataviz skill's validate_palette.js against
 * the dark surface before shipping it.
 */

export const CANVAS = '#050505';   // the report background, behind tiles
export const SURFACE = '#0f0f11';  // a tile's own background - the validated surface
export const SURFACE_RAISED = '#18181b';

export const BORDER = 'rgba(255,255,255,0.07)';
export const BORDER_STRONG = 'rgba(255,255,255,0.14)';
export const ACCENT = '#3987e5';

/** Text never wears a series colour; a mark beside it carries the identity. */
export const INK = {
    primary: '#ffffff',
    secondary: '#c3c2b7',
    muted: '#7a7975',
    faint: '#4a4a48',
};

/** Assigned in this order, never cycled. A ninth series folds into OTHER. */
export const SERIES = [
    '#3987e5', '#d95926', '#199e70', '#c98500',
    '#d55181', '#008300', '#9085e9', '#e66767',
];

/** One hue, light to dark - for magnitude, never for identity. */
export const SEQUENTIAL = [
    '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b',
];

export const OTHER = '#57565a';
export const GRID = 'rgba(255,255,255,0.06)';

/**
 * Colour for a named series.
 *
 * Assigned on first sight and remembered, rather than taken from the
 * series' position in the current result. Position would mean that
 * cross-filtering away one category repaints every category after it -
 * the chart appearing to change what it is about when the user only
 * narrowed it. Keying on the value itself keeps a category the same colour
 * for as long as the dataset is open.
 */
const assigned = new Map();

export function seriesColor(key) {
    const k = String(key);
    if (assigned.has(k)) return assigned.get(k);
    const colour = assigned.size < SERIES.length ? SERIES[assigned.size] : OTHER;
    assigned.set(k, colour);
    return colour;
}

/** Called when the dataset changes: the old category names mean nothing now. */
export function resetSeriesColors() {
    assigned.clear();
}

/**
 * Series beyond the eighth become "Other".
 *
 * A generated ninth hue would sit outside the validated set and could not be
 * told from one of the eight. Folding is the honest option, and the caller
 * says so in the legend.
 */
export const MAX_SERIES = SERIES.length;

// --- Recharts furniture. Spread these; never restate them per chart. ------

export const axisProps = {
    stroke: INK.faint,
    tick: { fill: INK.muted, fontSize: 11 },
    tickLine: false,
    axisLine: false,
};

export const gridProps = {
    stroke: GRID,
    strokeDasharray: '0',
    vertical: false,
};

export const tooltipProps = {
    contentStyle: {
        background: SURFACE_RAISED,
        border: `1px solid ${BORDER_STRONG}`,
        borderRadius: 8,
        fontSize: 12,
        color: INK.primary,
        boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
    },
    labelStyle: { color: INK.secondary, fontSize: 11, marginBottom: 4 },
    itemStyle: { color: INK.primary, fontSize: 12 },
    cursor: { fill: 'rgba(255,255,255,0.04)' },
};

/**
 * Thin marks, rounded at the data end only - the end that carries the value.
 * Rounding the baseline too would lift the bar off its own axis and make
 * small values look larger than they are.
 */
export const barProps = {
    radius: [4, 4, 0, 0],
    maxBarSize: 42,
};

/** A 2px gap of surface between adjacent bars, so they read as separate marks. */
export const barGaps = { barGap: 2, barCategoryGap: '18%' };

/** Unselected marks recede rather than disappear while a selection is live. */
export const DIM_OPACITY = 0.28;
