import React, {
    createContext, useContext, useEffect, useMemo, useReducer, useRef, useState,
} from 'react';
import { reportReducer } from './reportReducer';
import { emptyReport } from './reportTypes';
import { useDataset } from './DatasetContext';
import { seedVisuals } from '../utils/seedReport';
import { loadReport, saveReport } from '../hooks/useReportPersistence';

/**
 * The report: what is on the canvas and what it is filtered by.
 *
 * Filters are exposed twice on purpose. `filters` is the raw state, which
 * the panes edit; `debouncedFilters` lags it by a moment and is what the
 * tiles key their queries on. Dragging through a slicer's checkboxes or
 * clicking along a row of bars produces a burst of state changes, and
 * without the lag every intermediate step becomes a wave of requests to a
 * single-worker backend that will still be answering the first wave when the
 * user has moved on.
 */
const ReportContext = createContext(null);

const FILTER_DEBOUNCE_MS = 150;

/** What a set of visuals asks, ignoring ids and where the tiles sit. */
function seedSignature(visuals) {
    return JSON.stringify((visuals || []).map((v) => [
        v.type, v.title, v.fieldWells?.rows, v.fieldWells?.cols, v.fieldWells?.values, v.fieldWells?.agg,
    ]));
}

export function ReportProvider({ children }) {
    const { filename, profile } = useDataset();
    const [report, dispatch] = useReducer(reportReducer, null, () => emptyReport(null));
    const [debouncedFilters, setDebouncedFilters] = useState(report.filters);
    const seededFor = useRef(null);

    // A new dataset means a new report: either the one saved for it, or a
    // starter built from the profiler's own suggested questions, so the
    // canvas is never a blank rectangle with an invitation to configure it.
    useEffect(() => {
        if (!filename || !profile) return;
        if (seededFor.current === filename) return;
        seededFor.current = filename;

        const seeded = seedVisuals(profile);
        const seed = seedSignature(seeded);
        const saved = loadReport(filename);
        // Keep a saved report unless it is still exactly the starter it was
        // seeded with and the dataset now starts somewhere else. Anything the
        // visitor changed - a field, a chart type, another tile or page - stays.
        const untouchedStarter = saved && saved.seed && saved.pages.length === 1
            && seedSignature(saved.pages[0].visuals) === saved.seed;
        if (saved && !(untouchedStarter && saved.seed !== seed)) {
            dispatch({ type: 'LOAD_REPORT', report: saved });
            return;
        }
        const fresh = emptyReport(filename);
        fresh.pages[0].visuals = seeded;
        fresh.seed = seed;
        dispatch({ type: 'LOAD_REPORT', report: fresh });
    }, [filename, profile]);

    useEffect(() => {
        const id = setTimeout(() => setDebouncedFilters(report.filters), FILTER_DEBOUNCE_MS);
        return () => clearTimeout(id);
    }, [report.filters]);

    // Autosave, but not the transient parts: which tile is selected and
    // which bar is currently clicked are where the user is, not what they
    // built, and reloading into someone else's cross-filter is confusing.
    useEffect(() => {
        if (!filename || report.filename !== filename) return;
        const id = setTimeout(() => {
            saveReport(filename, {
                ...report,
                selectedVisualId: null,
                filters: { ...report.filters, crossFilter: null },
            });
        }, 500);
        return () => clearTimeout(id);
    }, [report, filename]);

    const value = useMemo(
        () => ({ report, dispatch, debouncedFilters }),
        [report, debouncedFilters]
    );

    return <ReportContext.Provider value={value}>{children}</ReportContext.Provider>;
}

export function useReport() {
    const ctx = useContext(ReportContext);
    if (!ctx) throw new Error('useReport must be used inside a ReportProvider');
    return ctx;
}
