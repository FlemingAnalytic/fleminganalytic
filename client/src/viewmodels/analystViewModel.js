import { useState, useCallback, useMemo } from 'react';

/**
 * ViewModel for the AnalystLab page.
 * Manages the top-level state of the analysis session.
 */
export const useAnalystViewModel = () => {
    const [dataset, setDataset] = useState(null);
    const [activeView, setActiveView] = useState('profile'); // 'profile', 'preview', 'predict', 'visualize'

    /**
     * Handles the completion of a dataset load operation.
     * Maps the API result to the session state.
     */
    const handleDatasetLoaded = useCallback((result) => {
        setDataset(result);
        setActiveView('profile');
    }, []);

    /**
     * Changes the current active workspace view.
     */
    const switchView = useCallback((view) => {
        setActiveView(view);
    }, []);

    /**
     * Derived properties for the UI to consume.
     */
    const sessionInfo = useMemo(() => ({
        hasDataset: !!dataset,
        filename: dataset?.filename || 'Untitled Session',
        rowCount: dataset?.profile?.shape?.rows || 0,
        colCount: dataset?.profile?.shape?.cols || 0,
        previewData: dataset?.preview || [],
        profileData: dataset?.profile || null
    }), [dataset]);

    return {
        dataset,
        activeView,
        sessionInfo,
        handleDatasetLoaded,
        switchView
    };
};
