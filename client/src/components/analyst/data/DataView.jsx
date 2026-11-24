import React, { useMemo, useState } from 'react';
import { AlertTriangle, Copy, Lightbulb, Loader2, Plus, Sigma, Table2 } from 'lucide-react';
import { useDataset } from '../../../state/DatasetContext';
import { analystApi } from '../../../services/api';
import { CANVAS, SURFACE, SURFACE_RAISED, BORDER, BORDER_STRONG, INK, ACCENT } from '../../../theme/vizTheme';
import { formatCount } from '../../../utils/format';

/**
 * What is actually in this dataset, before anyone asks it a question.
 *
 * The profiler has always computed insights, per-column statistics and a
 * duplicate count on load; none of it was rendered anywhere, so every dataset
 * arrived looking identical and the analyst had to discover its shape by
 * building visuals until something looked wrong. This is that work, shown.
 *
 * The transform panel is here rather than in the report because a derived
 * column is a property of the data, not of one report: once created it is a
 * field in the report, a feature in auto-learn, and a column in the export.
 */
export default function DataView() {
    const { hasDataset, profile, preview, rowCount, colCount, filename } = useDataset();
    const [created, setCreated] = useState([]);

    if (!hasDataset) {
        return (
            <div className="flex-1 flex items-center justify-center" style={{ background: CANVAS }}>
                <p className="text-[12px]" style={{ color: INK.muted }}>Open a dataset to start.</p>
            </div>
        );
    }

    const columns = profile?.columns || {};
    const insights = profile?.insights || [];
    const duplicates = profile?.duplicates || {};

    return (
        <div className="flex-1 overflow-auto" style={{ background: CANVAS }}>
            <div className="max-w-6xl mx-auto p-5 flex flex-col gap-4">

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <Stat label="Rows" value={formatCount(rowCount)} />
                    <Stat label="Columns" value={colCount} />
                    <Stat
                        label="Duplicate rows"
                        value={formatCount(duplicates.total_duplicate_rows ?? 0)}
                        warn={(duplicates.total_duplicate_rows ?? 0) > 0}
                    />
                    <Stat
                        label="Columns with gaps"
                        value={Object.values(columns).filter((c) => c.missing > 0).length}
                        warn={Object.values(columns).some((c) => c.missing_pct > 5)}
                    />
                </div>

                {insights.length > 0 && (
                    <Panel icon={<Lightbulb size={14} style={{ color: ACCENT }} />} title="What the profiler noticed">
                        <div className="flex flex-col gap-1.5 mt-2">
                            {insights.map((i, n) => (
                                <div key={n} className="flex items-start gap-2.5 px-3 py-2 rounded"
                                     style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}` }}>
                                    <span className="text-[10px] uppercase tracking-wider mt-0.5 shrink-0"
                                          style={{ color: i.type === 'anomaly' ? '#e0a838' : INK.muted, width: 74 }}>
                                        {i.type}
                                    </span>
                                    <div className="min-w-0">
                                        <div className="text-[12px]" style={{ color: INK.primary }}>{i.title}</div>
                                        <div className="text-[11px]" style={{ color: INK.muted }}>{i.detail}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Panel>
                )}

                <TransformPanel
                    filename={filename}
                    columns={columns}
                    created={created}
                    onCreated={(entry) => setCreated((c) => [...c, entry])}
                />

                <ColumnTable columns={columns} />

                <RowPreview preview={preview} columns={Object.keys(columns)} />
            </div>
        </div>
    );
}

/* ---------------------------------------------------------------- columns */

function ColumnTable({ columns }) {
    const [sort, setSort] = useState('order');
    const rows = useMemo(() => {
        const list = Object.values(columns);
        if (sort === 'missing') return [...list].sort((a, b) => b.missing_pct - a.missing_pct);
        if (sort === 'unique') return [...list].sort((a, b) => b.unique - a.unique);
        return list;
    }, [columns, sort]);

    return (
        <Panel
            icon={<Sigma size={14} style={{ color: ACCENT }} />}
            title={`Every column (${rows.length})`}
            action={
                <select
                    value={sort}
                    onChange={(e) => setSort(e.target.value)}
                    className="px-2 py-1 rounded text-[11px]"
                    style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}`, color: INK.secondary }}
                >
                    <option value="order">Dataset order</option>
                    <option value="missing">Most missing first</option>
                    <option value="unique">Most distinct first</option>
                </select>
            }
        >
            <div className="mt-2 overflow-x-auto">
                <table className="w-full text-[11px]" style={{ borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            {['Column', 'Type', 'Role', 'Missing', 'Distinct', 'Min', 'Median', 'Mean', 'Max'].map((h, i) => (
                                <th key={h}
                                    className="text-left font-medium py-1.5 px-2 whitespace-nowrap"
                                    style={{
                                        color: INK.muted,
                                        borderBottom: `1px solid ${BORDER_STRONG}`,
                                        textAlign: i >= 3 ? 'right' : 'left',
                                    }}>
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((c) => {
                            const s = c.stats || {};
                            return (
                                <tr key={c.name}>
                                    <Td strong>{c.name}</Td>
                                    <Td muted>{c.type}</Td>
                                    <Td muted>{c.role}</Td>
                                    <Td num warn={c.missing_pct > 5}>
                                        {c.missing ? `${c.missing_pct}%` : '—'}
                                    </Td>
                                    <Td num>{formatCount(c.unique)}</Td>
                                    <Td num>{fmt(s.min)}</Td>
                                    <Td num>{fmt(s.median)}</Td>
                                    <Td num>{fmt(s.mean)}</Td>
                                    <Td num>{fmt(s.max)}</Td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </Panel>
    );
}

/* ------------------------------------------------------------- transforms */

const METHODS = [
    { key: 'quintiles', label: 'Five equal-sized bands', note: 'Splits into fifths by rank — each band holds 20% of rows.' },
    { key: 'quartiles', label: 'Four equal-sized bands', note: 'Quarters by rank.' },
    { key: 'deciles', label: 'Ten equal-sized bands', note: 'Tenths by rank — for finer segmentation.' },
    { key: 'statistical', label: 'Distance from average', note: 'Bands by standard deviation, so outliers separate out.' },
    { key: 'kmeans', label: 'Natural clusters', note: 'Groups rows that resemble each other across every numeric column.' },
];

function TransformPanel({ filename, columns, created, onCreated }) {
    const numeric = Object.values(columns).filter((c) => c.role === 'measure').map((c) => c.name);
    const [column, setColumn] = useState(numeric[0] || '');
    const [method, setMethod] = useState('quintiles');
    const [clusters, setClusters] = useState(4);
    const [name, setName] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);

    const chosen = METHODS.find((m) => m.key === method);
    const suggested = method === 'kmeans'
        ? 'Cluster'
        : `${column}${method === 'statistical' ? 'Band' : method === 'quartiles' ? 'Quartile' : method === 'deciles' ? 'Decile' : 'Quintile'}`;

    const submit = async () => {
        const newName = (name || suggested).trim();
        if (!newName) return;
        setBusy(true);
        setError(null);
        try {
            const res = await analystApi.classify(
                filename, column, method, newName,
                method === 'kmeans' ? { n_clusters: clusters } : {},
            );
            onCreated({ name: res.name, distribution: res.distribution });
            setName('');
        } catch (err) {
            setError(err?.response?.data?.detail || 'Could not create that column.');
        } finally {
            setBusy(false);
        }
    };

    return (
        <Panel icon={<Plus size={14} style={{ color: ACCENT }} />} title="Add a column">
            <p className="text-[11px] mt-0.5" style={{ color: INK.muted }}>
                Turn a measure into groups you can compare. The new column becomes a field in the
                report and a column auto-learn can predict or learn from.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                <Labelled label="From">
                    <Select value={column} onChange={setColumn}
                            options={(method === 'kmeans' ? Object.keys(columns) : numeric).map((c) => [c, c])} />
                </Labelled>
                <Labelled label="Grouped by">
                    <Select value={method} onChange={setMethod} options={METHODS.map((m) => [m.key, m.label])} />
                </Labelled>
                <Labelled label="Called">
                    <input
                        value={name}
                        placeholder={suggested}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full px-2 py-1 rounded text-[11px]"
                        style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}`, color: INK.secondary }}
                    />
                </Labelled>
            </div>

            {method === 'kmeans' && (
                <div className="mt-2 flex items-center gap-2">
                    <span className="text-[11px]" style={{ color: INK.muted }}>Clusters</span>
                    <input type="range" min="2" max="10" value={clusters}
                           onChange={(e) => setClusters(Number(e.target.value))} />
                    <span className="text-[11px] tabular-nums" style={{ color: INK.secondary }}>{clusters}</span>
                </div>
            )}

            <p className="text-[10px] mt-2" style={{ color: INK.faint }}>{chosen?.note}</p>

            <button
                onClick={submit}
                disabled={busy || !column}
                className="mt-3 flex items-center gap-2 px-3 py-1.5 rounded text-[12px] font-medium disabled:opacity-50"
                style={{ background: ACCENT, color: '#04121f' }}
            >
                {busy ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
                {busy ? 'Creating…' : 'Create column'}
            </button>

            {error && <p className="text-[11px] mt-2" style={{ color: '#e66767' }}>{error}</p>}

            {created.length > 0 && (
                <div className="mt-3 flex flex-col gap-1.5">
                    {created.map((c) => (
                        <div key={c.name} className="px-3 py-2 rounded"
                             style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}` }}>
                            <div className="text-[12px]" style={{ color: INK.primary }}>{c.name}</div>
                            <div className="text-[10px] mt-1 flex flex-wrap gap-x-3 gap-y-0.5" style={{ color: INK.muted }}>
                                {Object.entries(c.distribution || {}).map(([k, v]) => (
                                    <span key={k}>{k}: {formatCount(v)}</span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </Panel>
    );
}

/* ------------------------------------------------------------------- rows */

function RowPreview({ preview, columns }) {
    const [wide, setWide] = useState(false);
    if (!preview?.length) return null;
    const shown = wide ? columns : columns.slice(0, 10);
    const rows = preview.slice(0, 25);

    return (
        <Panel
            icon={<Table2 size={14} style={{ color: ACCENT }} />}
            title={`First ${rows.length} rows`}
            action={
                columns.length > 10 && (
                    <button
                        onClick={() => setWide((w) => !w)}
                        className="px-2 py-1 rounded text-[11px]"
                        style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}
                    >
                        {wide ? 'First 10 columns' : `All ${columns.length} columns`}
                    </button>
                )
            }
        >
            <div className="mt-2 overflow-x-auto">
                <table className="text-[11px]" style={{ borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            {shown.map((c) => (
                                <th key={c} className="text-left font-medium py-1.5 px-2 whitespace-nowrap"
                                    style={{ color: INK.muted, borderBottom: `1px solid ${BORDER_STRONG}` }}>
                                    {c}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r, i) => (
                            <tr key={i}>
                                {shown.map((c) => (
                                    <Td key={c} muted>{String(r[c] ?? '')}</Td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Panel>
    );
}

/* ----------------------------------------------------------------- pieces */

function Stat({ label, value, warn }) {
    return (
        <div className="px-3 py-2.5 rounded" style={{ background: SURFACE, border: `1px solid ${warn ? '#c98500' : BORDER}` }}>
            <div className="flex items-center gap-1.5">
                <span className="text-[17px] font-semibold tabular-nums" style={{ color: warn ? '#e0a838' : INK.primary }}>
                    {value}
                </span>
                {warn && <AlertTriangle size={11} style={{ color: '#e0a838' }} />}
            </div>
            <div className="text-[10px] mt-0.5" style={{ color: INK.muted }}>{label}</div>
        </div>
    );
}

function Panel({ icon, title, action, children }) {
    return (
        <section className="rounded p-4" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
            <div className="flex items-center gap-2">
                {icon}
                <h2 className="text-[13px] font-semibold flex-1" style={{ color: INK.primary }}>{title}</h2>
                {action}
            </div>
            {children}
        </section>
    );
}

function Labelled({ label, children }) {
    return (
        <div>
            <div className="text-[10px] uppercase tracking-wider mb-1" style={{ color: INK.muted }}>{label}</div>
            {children}
        </div>
    );
}

function Select({ value, onChange, options }) {
    return (
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full px-2 py-1 rounded text-[11px]"
            style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}`, color: INK.secondary }}
        >
            {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
    );
}

function Td({ children, strong, muted, num, warn }) {
    return (
        <td
            className="py-1.5 px-2 whitespace-nowrap"
            style={{
                borderBottom: `1px solid ${BORDER}`,
                color: warn ? '#e0a838' : strong ? INK.primary : muted ? INK.muted : INK.secondary,
                textAlign: num ? 'right' : 'left',
                fontVariantNumeric: num ? 'tabular-nums' : 'normal',
            }}
        >
            {children}
        </td>
    );
}

/** Long decimals from the profiler make the table unreadable at a glance. */
function fmt(v) {
    if (v === null || v === undefined) return '—';
    if (typeof v !== 'number') return String(v);
    if (Number.isInteger(v)) return v.toLocaleString();
    return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
