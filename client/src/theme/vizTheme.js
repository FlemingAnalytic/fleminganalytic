/**
 * The one place chart colour and chart furniture are decided.
 *
 * Before this file, the app had a single chart with `#3b82f6` and its
 * tooltip styles written inline. Eight visual types doing that would be
 * eight slightly different charts sharing a page.
 *
 * The categorical palette is validated, not chosen by eye: eight slots on
 * the #20242d tile surface, checked for lightness band, chroma floor,
 * adjacent-pair separation under protanopia and tritanopia, a normal-vision
 * floor, and 3:1 contrast against the surface. Worst adjacent pair is
 * amber/green at deltaE 8.4 under protan - above the 8 threshold, so the
 * colours stand alone without needing texture to tell them apart. If any
 * value here changes, re-run the dataviz skill's validate_palette.js against
 * the dark surface before shipping it.
 */

/*
 * Canvas and surface were #050505 and #0f0f11: 1.06:1 apart, which is to say
 * indistinguishable. Tiles had no edge to be seen by - the border was 7% white,
 * another 1.18:1 - so the report read as one flat black rectangle. Raising the
 * tile surface to #20242d puts real light between them (1.35:1) and gives the
 * borders and axis ink something to sit against. The eight series colours were
 * re-validated against the new surface and pass all six checks unchanged.
 */
export const CANVAS = '#000000';   // the report background, behind tiles
export const SURFACE = '#20242d';  // a tile's own background - the validated surface
export const SURFACE_RAISED = '#2b3140';

export const BORDER = 'rgba(255,255,255,0.18)';
export const BORDER_STRONG = 'rgba(255,255,255,0.30)';
export const ACCENT = '#4f96ea';

/** Text never wears a series colour; a mark beside it carries the identity. */
export const INK = {
    primary: '#ffffff',   // 15.5:1 on the surface
    secondary: '#cdd3de', // 10.3:1
    muted: '#98a1b2',     //  6.0:1 - clears AA for body text, which the old #7a7975 did not
    faint: '#6b7484',     //  3.3:1 - axis lines and rules, the 3:1 graphics floor
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
export const GRID = 'rgba(255,255,255,0.10)';

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
