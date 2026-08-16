import { useState, useEffect, useCallback } from 'react';
import { analystApi } from '../services/api';

export const useDatasetViewModel = (onDatasetLoaded) => {
    const [savedDatasets, setSavedDatasets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('saved');
    const [url, setUrl] = useState('');
    const [error, setError] = useState(null);

    const fetchSaved = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await analystApi.listSaved();
            setSavedDatasets(data.datasets || []);
        } catch (err) {
            console.error('Failed to list saved datasets:', err);
            setError('Failed to list saved datasets');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSaved();
    }, [fetchSaved]);

    const loadSaved = async (filename) => {
        setLoading(true);
        setError(null);
        try {
            const result = await analystApi.loadSaved(filename);
            if (onDatasetLoaded) onDatasetLoaded(result);
            return result;
        } catch (err) {
            console.error('Load error:', err);
            setError('Failed to load dataset');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const loadPublic = async (name) => {
        setLoading(true);
        setError(null);
        try {
            const result = await analystApi.loadPublic(name);
            if (onDatasetLoaded) onDatasetLoaded(result);
            return result;
        } catch (err) {
            console.error('Public load error:', err);
            setError('Failed to load public dataset');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const loadUrl = async (inputUrl) => {
        const targetUrl = inputUrl || url;
        if (!targetUrl) return;
        
        setLoading(true);
        setError(null);
        try {
            const result = await analystApi.loadUrl(targetUrl);
            if (onDatasetLoaded) onDatasetLoaded(result);
            return result;
        } catch (err) {
            console.error('URL load error:', err);
            setError('Failed to load URL');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return {
        savedDatasets,
        loading,
        activeTab,
        setActiveTab,
        url,
        setUrl,
        error,
        loadSaved,
        loadPublic,
        loadUrl,
        refreshSaved: fetchSaved
    };
};
