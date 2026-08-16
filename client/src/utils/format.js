/**
 * Number formatting for a report surface.
 *
 * Aggregations come back at full float precision - a mean of 1926.7029194078948 -
 * and printed raw they turn a matrix into a wall of digits where no column
 * lines up and no value can be compared at a glance.
 */

const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
const plain = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const integer = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

/**
 * A value as it appears in a cell or a tooltip.
 *
 * Whole numbers keep their thousands separators and lose the decimal point;
 * fractions keep two places. Nothing is abbreviated here - a matrix is read
 * for exact figures, and 1.9K in a cell hides the difference between two
 * rows that differ by fifty.
 */
export function formatValue(value) {
    if (value === null || value === undefined || value === '') return '—';
    if (typeof value !== 'number') return String(value);
    if (!Number.isFinite(value)) return '—';
    if (Number.isInteger(value)) return integer.format(value);
    if (Math.abs(value) >= 1000) return integer.format(value);
    return plain.format(value);
}

/**
 * Axis ticks, where space is the constraint and the exact figure is not the
 * point - the tooltip and the matrix carry that.
 */
export function formatAxis(value) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '';
    return Math.abs(value) >= 10000 ? compact.format(value) : integer.format(value);
}

/** Category labels on an axis, which are frequently long enough to collide. */
export function truncateLabel(value, max = 18) {
    const s = String(value ?? '');
    return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export function formatCount(n) {
    return integer.format(n || 0);
}
