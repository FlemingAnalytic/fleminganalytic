import React, { createContext, useContext, useCallback, useMemo, useState } from 'react';
import { invalidateCache } from '../services/pivotClient';
import { resetSeriesColors } from '../theme/vizTheme';

/**
 * The dataset the report is built on: which session the backend is holding,
 * and what it told us about the columns.
 *
 * Kept apart from the report state because they have different lifetimes.
 * The report is edited constantly - a field assigned, a bar clicked - while
 * the dataset changes once and then anchors everything. Merging them would
 * put a profile of 34 columns through the same reducer that fires on every
 * click, for no benefit.
 *
 * `sessionLost` exists because the backend's sessions are an in-process
 * dict: a gunicorn restart forgets the dataframe while the browser still has
 * the filename, and every tile would otherwise fill with errors that all
 * have the same cause and one fix.
 */
const DatasetContext = createContext(null);

export function DatasetProvider({ children }) {
    const [dataset, setDataset] = useState(null);
    const [sessionLost, setSessionLost] = useState(false);

    // Both of these are keyed to the dataset, not to the report: cached
    // pivots answer questions about the old frame, and remembered series
    // colours belong to category names that may not exist in the new one.
    const loadDataset = useCallback((result) => {
        invalidateCache();
        resetSeriesColors();
        setDataset(result);
        setSessionLost(false);
    }, []);

    const clearDataset = useCallback(() => {
        invalidateCache();
        resetSeriesColors();
        setDataset(null);
        setSessionLost(false);
    }, []);

    const value = useMemo(
        () => ({
            dataset,
            // The session key the load call returned, not the file name the
            // user picked. load-saved answers 'saved_chicagoland' for
            // 'chicagoland.csv', and every later call has to use that.
            filename: dataset?.filename || null,
            displayName: dataset?.display_name || dataset?.filename || null,
            profile: dataset?.profile || null,
            preview: dataset?.preview || [],
            rowCount: dataset?.profile?.shape?.rows || 0,
            colCount: dataset?.profile?.shape?.cols || 0,
            hasDataset: Boolean(dataset),
            sessionLost,
            reportSessionLost: () => setSessionLost(true),
            loadDataset,
            clearDataset,
        }),
        [dataset, sessionLost, loadDataset, clearDataset]
    );

    return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>;
}

export function useDataset() {
    const ctx = useContext(DatasetContext);
    if (!ctx) throw new Error('useDataset must be used inside a DatasetProvider');
    return ctx;
}
