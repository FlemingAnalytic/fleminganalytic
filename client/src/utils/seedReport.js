/**
 * The tiles a dataset opens with.
 *
 * An empty canvas asking the user to pick fields is the worst first screen a
 * report tool can show, because answering it requires already knowing what
 * is in the data. The profiler has done that reading - it returns
 * `suggested_questions`, each carrying a ready-made pivot spec - so opening
 * a dataset opens a report that already says something, and the fields pane
 * becomes a way to disagree with it rather than a blank form.
 */

import { AXIS_CARDINALITY_LIMIT, createVisual } from '../state/reportTypes';

const MAX_SEEDED = 4;

function cardinality(profile, column) {
    return profile?.columns?.[column]?.unique ?? Infinity;
}

/** Dimensions coarse enough to read as an axis, coarsest first. */
function axisDimensions(profile) {
    return Object.values(profile?.columns || {})
        .filter((c) => c.role === 'dimension' && c.unique > 1 && c.unique <= AXIS_CARDINALITY_LIMIT)
        .sort((a, b) => a.unique - b.unique)
        .map((c) => c.name);
}

function measures(profile) {
    return Object.values(profile?.columns || {})
        .filter((c) => c.role === 'measure')
        .map((c) => c.name);
}

/**
 * Pick pivot suggestions worth showing.
 *
 * The profiler emits its suggestions measure-first, so the same dimension
 * arrives several times in a row - sqft by owner_occupied, then lot_sqft by
 * owner_occupied. Four tiles that all split by the same column look like one
 * chart drawn four times, so this keeps the first suggestion per dimension
 * and drops fields too granular to plot.
 */
function usableSuggestions(profile) {
    const seen = new Set();
    const out = [];
    for (const s of profile?.suggested_questions || []) {
        const a = s.action;
        if (!a || a.type !== 'pivot') continue;
        const dim = a.rows?.[0];
        const measure = a.values?.[0];
        if (!dim || !measure || seen.has(dim)) continue;
        if (cardinality(profile, dim) > AXIS_CARDINALITY_LIMIT) continue;
        seen.add(dim);
        out.push({ dim, measure, agg: a.agg || 'sum', question: s.question });
        if (out.length >= MAX_SEEDED) break;
    }
    return out;
}

/** Anything at all, for a dataset the profiler had no suggestions about. */
function fallbackSpecs(profile) {
    const dims = axisDimensions(profile);
    const vals = measures(profile);
    if (!dims.length) return [];
    if (!vals.length) {
        // No measures: counting rows per category is still a real answer,
        // and count works against a dimension.
        return dims.slice(0, 2).map((dim) => ({ dim, measure: dim, agg: 'count', question: null }));
    }
    return dims.slice(0, 2).map((dim, i) => ({
        dim,
        measure: vals[i % vals.length],
        agg: 'mean',
        question: null,
    }));
}

/**
 * Build the starting visuals for a profile.
 *
 * The first is a matrix. It shows the numbers themselves, which is what
 * makes the charts beside it legible - and it is the visual that proves the
 * pivot round trip is working, so if anything is wrong it is wrong somewhere
 * visible rather than hidden behind a chart that merely looks empty.
 */
export function seedVisuals(profile) {
    const specs = usableSuggestions(profile);
    const chosen = specs.length ? specs : fallbackSpecs(profile);
    if (!chosen.length) return [];

    return chosen.map((spec, i) =>
        createVisual({
            type: i === 0 ? 'matrix' : 'column',
            title: spec.question || null,
            fieldWells: {
                rows: [spec.dim],
                cols: [],
                values: [spec.measure],
                agg: spec.agg,
                weightCol: null,
            },
            position: { x: (i % 2) * 6, y: Math.floor(i / 2) * 4, w: 6, h: 4 },
        })
    );
}
