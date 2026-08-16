import { useState, useMemo } from 'react';

/**
 * ViewModel for dataset profiling and insights.
 * Handles the logic of sorting, filtering, and extracting metadata from the profile.
 */
export const useDataProfileViewModel = (profile) => {
    const [selectedColumn, setSelectedColumn] = useState(null);

    // Derived metadata for the overall dataset
    const stats = useMemo(() => {
        if (!profile) return null;
        return {
            rows: profile.shape?.rows || 0,
            cols: profile.shape?.cols || 0,
            insightsCount: profile.insights?.length || 0,
            strongPairsCount: profile.correlations?.strong_pairs?.length || 0
        };
    }, [profile]);

    // Categorize columns by role/type
    const categorizedColumns = useMemo(() => {
        if (!profile || !profile.columns) return { measures: [], dimensions: [], geo: [] };
        
        const columns = Object.values(profile.columns);
        return {
            measures: columns.filter(c => c.role === 'measure'),
            dimensions: columns.filter(c => c.role === 'dimension'),
            geo: columns.filter(c => c.geo_hint)
        };
    }, [profile]);

    // Format correlation matrix for display
    const correlationMatrix = useMemo(() => {
        if (!profile || !profile.correlations) return null;
        return profile.correlations;
    }, [profile]);

    const handleSelectColumn = (colName) => {
        setSelectedColumn(profile?.columns?.[colName] || null);
    };

    return {
        stats,
        categorizedColumns,
        correlationMatrix,
        insights: profile?.insights || [],
        suggestedQuestions: profile?.suggested_questions || [],
        selectedColumn,
        handleSelectColumn
    };
};
