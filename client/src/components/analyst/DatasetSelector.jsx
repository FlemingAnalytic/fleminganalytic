import React from 'react';
import { Globe, Link as LinkIcon, HardDrive, Loader2 } from 'lucide-react';
import { useDatasetViewModel } from '../../viewmodels/datasetViewModel';
import { useDataset } from '../../state/DatasetContext';
import { BORDER, INK, ACCENT } from '../../theme/vizTheme';

/**
 * Choosing what to report on.
 *
 * Rebuilt for the left rail. The previous version was 380px wide with 40px
 * of padding per row - reasonable as a full-page step, far too loose for a
 * panel that folds away once a dataset is loaded and that has to share the
 * screen with the canvas it feeds.
 *
 * It reports the loaded dataset to the context rather than through a prop,
 * so the rail does not have to relay it and the report state can react to a
 * dataset change wherever it happens.
 */
const PUBLIC_SAMPLES = [
    { id: 'titanic', label: 'Titanic survivors', category: 'Foundation' },
    { id: 'tips', label: 'Restaurant tips', category: 'Foundation' },
    { id: 'iris', label: 'Iris species', category: 'Foundation' },
    { id: 'diamonds', label: 'Diamond grading', category: 'Foundation' },
    { id: 'mpg', label: 'Fuel efficiency', category: 'Foundation' },
    { id: 'sp500_companies', label: 'S&P 500 companies', category: 'Strategic' },
    { id: 'world_happiness', label: 'World happiness', category: 'Strategic' },
    { id: 'gapminder', label: 'Health and wealth', category: 'Strategic' },
    { id: 'us_car_dealerships', label: 'US car dealerships', category: 'Strategic' },
    { id: 'seattle_weather', label: 'Seattle weather', category: 'Research' },
    { id: 'state_unemployment', label: 'US unemployment', category: 'Research' },
    { id: 'nyc_311_calls', label: 'NYC 311 calls', category: 'Research' },
    { id: 'census_county_pop', label: 'County population', category: 'Research' },
];

const CATEGORIES = ['Foundation', 'Strategic', 'Research'];

export default function DatasetSelector() {
    const { loadDataset, filename } = useDataset();
    const {
        savedDatasets, loading, activeTab, setActiveTab, url, setUrl, error,
        loadSaved, loadPublic, loadUrl,
    } = useDatasetViewModel(loadDataset);

    return (
        <div className="flex flex-col h-full min-h-0">
            <div className="flex gap-1 px-3 pb-2">
                <Tab active={activeTab === 'saved'} onClick={() => setActiveTab('saved')}
                     label="Saved" icon={<HardDrive size={11} />} />
                <Tab active={activeTab === 'public'} onClick={() => setActiveTab('public')}
                     label="Samples" icon={<Globe size={11} />} />
                <Tab active={activeTab === 'url'} onClick={() => setActiveTab('url')}
                     label="URL" icon={<LinkIcon size={11} />} />
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto scrollbar-hide px-2 pb-3 space-y-0.5">
                {loading && (
                    <p className="flex items-center gap-1.5 px-2 py-2 text-[11px]" style={{ color: INK.muted }}>
                        <Loader2 size={11} className="animate-spin" /> Loading and profiling…
                    </p>
                )}

                {error && (
                    <p className="px-2 py-2 text-[11px]" style={{ color: '#e66767' }}>{error}</p>
                )}

                {activeTab === 'saved' && !loading && (
                    savedDatasets.length ? savedDatasets.map((ds) => (
                        <Item
                            key={ds.filename}
                            label={ds.display_name}
                            sub={ds.filename}
                            active={filename === `saved_${ds.base_name}`}
                            onClick={() => loadSaved(ds.filename)}
                        />
                    )) : (
                        <p className="px-2 py-2 text-[11px]" style={{ color: INK.muted }}>No saved datasets.</p>
                    )
                )}

                {activeTab === 'public' && CATEGORIES.map((cat) => (
                    <div key={cat} className="pt-1.5">
                        <p className="px-2 pb-1 text-[9.5px] font-semibold uppercase tracking-[0.12em]"
                           style={{ color: INK.faint }}>
                            {cat}
                        </p>
                        {PUBLIC_SAMPLES.filter((p) => p.category === cat).map((p) => (
                            <Item key={p.id} label={p.label} onClick={() => loadPublic(p.id)} />
                        ))}
                    </div>
                ))}

                {activeTab === 'url' && (
                    <div className="px-1 pt-1 space-y-2">
                        <input
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="https://example.com/data.csv"
                            className="w-full px-2 py-1.5 rounded text-[11px] outline-none"
                            style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER}`, color: INK.primary }}
                        />
                        <button
                            onClick={() => loadUrl()}
                            disabled={!url || loading}
                            className="w-full py-1.5 rounded text-[11px] font-medium transition-colors disabled:opacity-40"
                            style={{ background: ACCENT, color: '#fff' }}
                        >
                            Load
                        </button>
                        <p className="text-[10px] leading-relaxed" style={{ color: INK.muted }}>
                            CSV, JSON or XLSX, fetched and profiled on the server.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

function Tab({ active, onClick, label, icon }) {
    return (
        <button
            onClick={onClick}
            className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded text-[10.5px] transition-colors"
            style={{
                background: active ? 'rgba(57,135,229,0.14)' : 'transparent',
                color: active ? ACCENT : INK.muted,
                border: `1px solid ${active ? 'rgba(57,135,229,0.3)' : BORDER}`,
            }}
        >
            {icon} {label}
        </button>
    );
}

function Item({ label, sub, active, onClick }) {
    return (
        <button
            onClick={onClick}
            className="w-full text-left px-2 py-1.5 rounded transition-colors hover:bg-white/[0.05]"
            style={{ background: active ? 'rgba(57,135,229,0.10)' : undefined }}
        >
            <span className="block text-[11.5px] truncate" style={{ color: active ? ACCENT : INK.secondary }}>
                {label}
            </span>
            {sub && (
                <span className="block text-[9.5px] truncate" style={{ color: INK.faint }}>{sub}</span>
            )}
        </button>
    );
}
