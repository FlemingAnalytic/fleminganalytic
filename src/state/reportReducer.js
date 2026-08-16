/**
 * Every change to the report, in one place.
 *
 * A reducer rather than a handful of useState calls because most of these
 * are not single-field edits. Removing a visual has to drop its slicer entry
 * and clear the selection if that visual owned it; picking a field has to
 * decide which well it belongs in. Doing that across separate setters leaves
 * windows where the report is briefly inconsistent - a slicer filtering on
 * behalf of a tile that no longer exists - and each of those windows is a
 * render that fires a query.
 *
 * Actions being plain data also means the whole report serialises, which is
 * what makes localStorage persistence and Export JSON a few lines each.
 */

import { createVisual, emptyReport } from './reportTypes';

function mapVisuals(state, fn) {
    return {
        ...state,
        pages: state.pages.map((page) =>
            page.id !== state.activePageId ? page : { ...page, visuals: fn(page.visuals) }
        ),
    };
}

function updateVisual(state, visualId, fn) {
    return mapVisuals(state, (visuals) =>
        visuals.map((v) => (v.id === visualId ? fn(v) : v))
    );
}

/** Where the next tile goes: below everything already placed. */
function nextPosition(visuals) {
    const bottom = visuals.reduce((max, v) => Math.max(max, v.position.y + v.position.h), 0);
    return { x: 0, y: bottom, w: 6, h: 4 };
}

export function reportReducer(state, action) {
    switch (action.type) {
        case 'LOAD_REPORT':
            return action.report;

        case 'RESET_REPORT':
            return emptyReport(state.filename);

        case 'SET_FILENAME':
            // A different dataset invalidates every field name in every
            // well, so the report starts over rather than carrying wells
            // that name columns the new frame does not have.
            return state.filename === action.filename ? state : emptyReport(action.filename);

        case 'ADD_VISUAL': {
            const page = state.pages.find((p) => p.id === state.activePageId);
            const visual = createVisual({
                ...action.visual,
                position: action.visual?.position || nextPosition(page.visuals),
            });
            return {
                ...mapVisuals(state, (visuals) => [...visuals, visual]),
                selectedVisualId: visual.id,
            };
        }

        case 'REMOVE_VISUAL': {
            const next = mapVisuals(state, (visuals) =>
                visuals.filter((v) => v.id !== action.visualId)
            );
            const { [action.visualId]: _removed, ...slicers } = state.filters.slicers;
            return {
                ...next,
                selectedVisualId:
                    state.selectedVisualId === action.visualId ? null : state.selectedVisualId,
                filters: {
                    ...state.filters,
                    slicers,
                    // A selection made by a visual that is gone would filter
                    // the rest of the page with nothing on screen to clear it.
                    crossFilter:
                        state.filters.crossFilter?.sourceId === action.visualId
                            ? null
                            : state.filters.crossFilter,
                },
            };
        }

        case 'DUPLICATE_VISUAL': {
            const source = state.pages
                .find((p) => p.id === state.activePageId)
                .visuals.find((v) => v.id === action.visualId);
            if (!source) return state;
            const copy = createVisual({
                ...source,
                id: undefined,
                position: { ...source.position, y: source.position.y + source.position.h },
            });
            return {
                ...mapVisuals(state, (visuals) => [...visuals, copy]),
                selectedVisualId: copy.id,
            };
        }

        case 'SELECT_VISUAL':
            return { ...state, selectedVisualId: action.visualId };

        case 'SET_VISUAL_TYPE':
            return updateVisual(state, action.visualId, (v) => ({ ...v, type: action.visualType }));

        case 'SET_VISUAL_TITLE':
            return updateVisual(state, action.visualId, (v) => ({ ...v, title: action.title }));

        case 'ASSIGN_FIELD':
            return updateVisual(state, action.visualId, (v) => {
                const well = action.well;
                const current = v.fieldWells[well] || [];
                if (current.includes(action.field)) return v;
                // Rows and Columns take one field each for now: a second row
                // dimension returns a nested index the flattened response
                // cannot express unambiguously.
                const single = well === 'rows' || well === 'cols';
                return {
                    ...v,
                    fieldWells: {
                        ...v.fieldWells,
                        [well]: single ? [action.field] : [...current, action.field],
                    },
                };
            });

        case 'REMOVE_FIELD':
            return updateVisual(state, action.visualId, (v) => ({
                ...v,
                fieldWells: {
                    ...v.fieldWells,
                    [action.well]: (v.fieldWells[action.well] || []).filter(
                        (f) => f !== action.field
                    ),
                },
            }));

        case 'SET_AGG':
            return updateVisual(state, action.visualId, (v) => ({
                ...v,
                fieldWells: {
                    ...v.fieldWells,
                    agg: action.agg,
                    // The weight column only means anything for a weighted
                    // average; leaving a stale one set would send it with
                    // every later request.
                    weightCol: action.agg === 'weighted_avg' ? v.fieldWells.weightCol : null,
                },
            }));

        case 'SET_WEIGHT_COL':
            return updateVisual(state, action.visualId, (v) => ({
                ...v,
                fieldWells: { ...v.fieldWells, weightCol: action.column },
            }));

        case 'MOVE_VISUAL':
            return updateVisual(state, action.visualId, (v) => ({
                ...v,
                position: { ...v.position, ...action.position },
            }));

        case 'TOGGLE_CROSS_FILTER_SOURCE':
            return updateVisual(state, action.visualId, (v) => ({
                ...v,
                interactions: { ...v.interactions, crossFilter: !v.interactions.crossFilter },
            }));

        case 'SET_PAGE_FILTER': {
            const page = { ...state.filters.page };
            if (!action.values || !action.values.length) delete page[action.column];
            else page[action.column] = action.values;
            return { ...state, filters: { ...state.filters, page } };
        }

        case 'SET_SLICER':
            return {
                ...state,
                filters: {
                    ...state.filters,
                    slicers: {
                        ...state.filters.slicers,
                        [action.visualId]: { column: action.column, values: action.values },
                    },
                },
            };

        case 'SET_CROSS_FILTER': {
            const current = state.filters.crossFilter;
            const same =
                current &&
                current.sourceId === action.sourceId &&
                current.column === action.column;

            let values;
            if (action.additive && same) {
                // Ctrl-click: build up a selection, and clicking a selected
                // mark again takes it back out.
                const set = new Set(current.values.map(String));
                const key = String(action.value);
                values = set.has(key)
                    ? current.values.filter((v) => String(v) !== key)
                    : [...current.values, action.value];
            } else if (same && current.values.length === 1 &&
                       String(current.values[0]) === String(action.value)) {
                // Clicking the only selected mark clears - the same gesture
                // that made the selection undoes it.
                values = [];
            } else {
                values = [action.value];
            }

            return {
                ...state,
                filters: {
                    ...state.filters,
                    crossFilter: values.length
                        ? { sourceId: action.sourceId, column: action.column, values }
                        : null,
                },
            };
        }

        case 'CLEAR_CROSS_FILTER':
            return { ...state, filters: { ...state.filters, crossFilter: null } };

        case 'CLEAR_ALL_FILTERS':
            return {
                ...state,
                filters: { page: {}, slicers: {}, crossFilter: null },
            };

        default:
            return state;
    }
}
