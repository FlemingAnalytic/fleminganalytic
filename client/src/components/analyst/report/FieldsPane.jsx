import React, { useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, Hash, Calendar, MapPin, Type, Sigma, Search, Sparkles } from 'lucide-react';
import { BORDER, INK, ACCENT } from '../../../theme/vizTheme';
import { AXIS_CARDINALITY_LIMIT, createVisual } from '../../../state/reportTypes';
import { useDataset } from '../../../state/DatasetContext';
import { useReport } from '../../../state/ReportContext';
import { formatCount } from '../../../utils/format';

/**
 * The list of what this dataset contains.
 *
 * None of this is inferred in the client. The profiler already tags every
 * column `measure` or `dimension` and gives its type, distinct count and geo
 * hint - the same split a report tool needs for its field list. The client's
 * only job is to show it and to say which fields will not make a readable
 * axis.
 *
 * Clicking a field assigns it, rather than dragging it. Drag is the gesture
 * people picture, but it is a day of sensor and accessibility work that adds
 * no analytical capability, and the well it lands in is the same either way -
 * so it can be added later without touching any of this state.
 */
export default function FieldsPane() {
    const { profile } = useDataset();
    const { report, dispatch } = useReport();
    const [query, setQuery] = useState('');
    const [open, setOpen] = useState({ suggested: true, measures: true, dimensions: true, geo: false });

    const selectedVisual = useMemo(
        () => report.pages
            .find((p) => p.id === report.activePageId)
            ?.visuals.find((v) => v.id === report.selectedVisualId) || null,
        [report]
    );

    const groups = useMemo(() => {
        const columns = Object.values(profile?.columns || {});
        const match = (c) => !query || c.name.toLowerCase().includes(query.toLowerCase());
        return {
            measures: columns.filter((c) => c.role === 'measure' && match(c)),
            dimensions: columns.filter((c) => c.role === 'dimension' && match(c)),
            geo: columns.filter((c) => c.geo_hint && match(c)),
        };
    }, [profile, query]);

    const suggestions = useMemo(() => {
        const seen = new Set();
        return (profile?.suggested_questions || [])
            .filter((s) => s.action?.type === 'pivot')
            .filter((s) => {
                const key = `${s.action.rows?.[0]}|${s.action.values?.[0]}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            })
            .slice(0, 6);
    }, [profile]);

    /**
     * Assign a field to the well it most likely belongs in.
     *
     * A measure is something to aggregate, a dimension is something to
     * aggregate by - the profiler has already made that call, so the obvious
     * default is right nearly every time. A second dimension goes to Columns,
     * which is how a cross-tab gets built without explaining what a cross-tab
     * is. The wells below stay editable for the times this guesses wrong.
     */
    const assign = (column) => {
        if (!selectedVisual) return;
        const wells = selectedVisual.fieldWells;
        let well;
        if (column.role === 'measure') {
            well = 'values';
        } else {
            well = wells.rows.length && !wells.cols.length ? 'cols' : 'rows';
        }
        dispatch({ type: 'ASSIGN_FIELD', visualId: selectedVisual.id, well, field: column.name });
    };

    const applySuggestion = (s) => {
        dispatch({
            type: 'ADD_VISUAL',
            visual: createVisual({
                type: 'column',
                title: s.question,
                fieldWells: {
                    rows: s.action.rows || [],
                    cols: [],
                    values: s.action.values || [],
                    agg: s.action.agg || 'sum',
                    weightCol: null,
                },
            }),
        });
    };

    if (!profile) return null;

    return (
        <div className="flex flex-col min-h-0">
            <div className="px-3 py-2" style={{ borderBottom: `1px solid ${BORDER}` }}>
                <div className="relative">
                    <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2" style={{ color: INK.faint }} />
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search fields"
                        className="w-full pl-7 pr-2 py-1.5 rounded text-[11.5px] outline-none transition-colors"
                        style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER}`, color: INK.primary }}
                    />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-hide">
                {suggestions.length > 0 && !query && (
                    <Group
                        label="Suggested"
                        icon={<Sparkles size={11} />}
                        count={suggestions.length}
                        open={open.suggested}
                        onToggle={() => setOpen((o) => ({ ...o, suggested: !o.suggested }))}
                    >
                        {suggestions.map((s, i) => (
                            <button
                                key={i}
                                onClick={() => applySuggestion(s)}
                                className="w-full text-left px-2 py-1.5 rounded text-[11px] leading-snug hover:bg-white/[0.05] transition-colors"
                                style={{ color: INK.secondary }}
                            >
                                {s.question}
                            </button>
                        ))}
                    </Group>
                )}

                <Group
                    label="Measures" icon={<Sigma size={11} />} count={groups.measures.length}
                    open={open.measures} onToggle={() => setOpen((o) => ({ ...o, measures: !o.measures }))}
                >
                    {groups.measures.map((c) => (
                        <FieldChip key={c.name} column={c} onClick={() => assign(c)} disabled={!selectedVisual} />
                    ))}
                </Group>

                <Group
                    label="Dimensions" icon={<Type size={11} />} count={groups.dimensions.length}
                    open={open.dimensions} onToggle={() => setOpen((o) => ({ ...o, dimensions: !o.dimensions }))}
                >
                    {groups.dimensions.map((c) => (
                        <FieldChip key={c.name} column={c} onClick={() => assign(c)} disabled={!selectedVisual} />
                    ))}
                </Group>

                {groups.geo.length > 0 && (
                    <Group
                        label="Geography" icon={<MapPin size={11} />} count={groups.geo.length}
                        open={open.geo} onToggle={() => setOpen((o) => ({ ...o, geo: !o.geo }))}
                    >
                        {groups.geo.map((c) => (
                            <FieldChip key={c.name} column={c} onClick={() => assign(c)} disabled={!selectedVisual} />
                        ))}
                    </Group>
                )}
            </div>

            {!selectedVisual && (
                <p className="px-3 py-2 text-[10.5px] leading-relaxed"
                   style={{ color: INK.muted, borderTop: `1px solid ${BORDER}` }}>
                    Select a visual to add fields to it.
                </p>
            )}
        </div>
    );
}

function Group({ label, icon, count, open, onToggle, children }) {
    return (
        <div style={{ borderBottom: `1px solid ${BORDER}` }}>
            <button
                onClick={onToggle}
                className="w-full flex items-center gap-1.5 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] hover:bg-white/[0.03] transition-colors"
                style={{ color: INK.muted }}
            >
                {open ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                {icon}
                <span className="flex-1 text-left">{label}</span>
                <span style={{ color: INK.faint }}>{count}</span>
            </button>
            {open && <div className="px-2 pb-2 space-y-0.5">{children}</div>}
        </div>
    );
}

const TYPE_ICON = {
    continuous: <Hash size={10} />,
    categorical_numeric: <Hash size={10} />,
    datetime: <Calendar size={10} />,
    categorical: <Type size={10} />,
};

function FieldChip({ column, onClick, disabled }) {
    // Distinct count is the thing that decides whether a field can be an
    // axis at all, so it is on the chip rather than hidden in a tooltip.
    const tooGranular =
        column.role === 'dimension' && column.unique > AXIS_CARDINALITY_LIMIT;

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            title={
                tooGranular
                    ? `${formatCount(column.unique)} distinct values — too granular for an axis; the visual will show the top ${AXIS_CARDINALITY_LIMIT}`
                    : `${column.type} · ${formatCount(column.unique)} distinct`
            }
            className="w-full flex items-center gap-1.5 px-2 py-1 rounded text-[11.5px] text-left transition-colors hover:bg-white/[0.06] disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ color: tooGranular ? INK.muted : INK.secondary }}
        >
            <span style={{ color: column.role === 'measure' ? ACCENT : INK.faint }}>
                {TYPE_ICON[column.type] || <Type size={10} />}
            </span>
            <span className="flex-1 truncate">{column.name}</span>
            {tooGranular && (
                <span className="text-[9px] tabular-nums" style={{ color: INK.faint }}>
                    {formatCount(column.unique)}
                </span>
            )}
        </button>
    );
}
