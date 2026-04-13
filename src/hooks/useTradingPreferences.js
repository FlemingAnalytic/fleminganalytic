import { useState, useEffect } from 'react';

/**
 * Hook to manage trading parameters and portfolio assumptions locally in the browser.
 * This ensures sensitive or personal financial parameters never need to reside on the server.
 */
export const useTradingPreferences = () => {
    // Initial default assumptions
    const DEFAULT_PREFERENCES = {
        tickers: "LLY:.39,CMG:.22,PWR:.12,PANW:.07,AXON:.06,AZO:.05,ORLY:.04,ODFL:.03",
        riskTolerance: 0.5,
        targetReturn: 0.15,
        useSentiment: true,
        rebalanceFrequency: 'monthly'
    };

    // Initialize state from localStorage or defaults
    const [preferences, setPreferences] = useState(() => {
        const saved = localStorage.getItem('trading_preferences');
        return saved ? JSON.parse(saved) : DEFAULT_PREFERENCES;
    });

    // Save to localStorage whenever preferences change
    useEffect(() => {
        localStorage.setItem('trading_preferences', JSON.stringify(preferences));
    }, [preferences]);

    /**
     * Update a single preference key
     */
    const updatePreference = (key, value) => {
        setPreferences(prev => ({
            ...prev,
            [key]: value
        }));
    };

    /**
     * Reset to system defaults
     */
    const resetToDefaults = () => {
        setPreferences(DEFAULT_PREFERENCES);
    };

    return {
        preferences,
        updatePreference,
        resetToDefaults
    };
};

export default useTradingPreferences;
