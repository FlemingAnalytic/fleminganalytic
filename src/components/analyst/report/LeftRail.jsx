import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Database, Plus, Table2, BarChart3 } from 'lucide-react';
import DatasetSelector from '../DatasetSelector';
import { useDataset } from '../../../state/DatasetContext';
import { useReport } from '../../../state/ReportContext';
import { createVisual, VISUAL_TYPES } from '../../../state/reportTypes';
import { BORDER, INK, ACCENT, SURFACE } from '../../../theme/vizTheme';

const TYPE_ICON = { matrix: <Table2 size={14} />, column: <BarChart3 size={14} /> };

/**
 * Visual types to add, and the dataset to add them about.
 *
 * The dataset picker used to be a permanent 380px column - a quarter of the
 * screen given over to an action performed once per session. It folds away
 * here as soon as something is loaded, which is most of where the room for
 * a canvas came from.
 */
export default function LeftRail() {
    const { hasDataset, displayName } = useDataset();
    const { report, dispatch } = useReport();
    const [dataOpen, setDataOpen] = useState(!hasDataset);

    const addVisual = (type) => dispatch({ type: 'ADD_VISUAL', visual: createVisual({ type }) });

    return (
        <aside
            className="w-[260px] shrink-0 flex flex-col min-h-0"
            style={{ background: SURFACE, borderRight: `1px solid ${BORDER}` }}
        >
            <Section label="Visualizations">
                <div className="grid grid-cols-2 gap-1.5 px-3 pb-3">
                    {VISUAL_TYPES.map((v) => (
                        <button
                            key={v.type}
                            onClick={() => addVisual(v.type)}
                            disabled={!hasDataset}
                            title={v.hint}
                            className="flex flex-col items-center gap-1 py-2.5 rounded text-[10.5px] transition-colors hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed"
                            style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}
                        >
                            <span style={{ color: ACCENT }}>{TYPE_ICON[v.type]}</span>
                            {v.label}
                        </button>
                    ))}
                </div>
            </Section>

            <div style={{ borderTop: `1px solid ${BORDER}` }}>
                <button
                    onClick={() => setDataOpen((o) => !o)}
                    className="w-full flex items-center gap-1.5 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] hover:bg-white/[0.03] transition-colors"
                    style={{ color: INK.muted }}
                >
                    {dataOpen ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                    <Database size={11} />
                    <span className="flex-1 text-left">Data</span>
                </button>
                {!dataOpen && hasDataset && (
                    <p className="px-3 pb-2 text-[11px] truncate" style={{ color: INK.secondary }}>
                        {displayName}
                    </p>
                )}
            </div>

            {dataOpen && (
                <div className="flex-1 min-h-0 overflow-hidden">
                    <DatasetSelector />
                </div>
            )}

            {!dataOpen && (
                <div className="flex-1 flex items-end p-3">
                    <button
                        onClick={() => dispatch({ type: 'ADD_VISUAL', visual: createVisual() })}
                        disabled={!hasDataset}
                        className="w-full flex items-center justify-center gap-1.5 py-2 rounded text-[11px] transition-colors hover:bg-white/[0.06] disabled:opacity-30"
                        style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}
                    >
                        <Plus size={12} /> Blank visual
                    </button>
                </div>
            )}
        </aside>
    );
}

function Section({ label, children }) {
    return (
        <div>
            <p className="px-3 pt-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.12em]"
               style={{ color: INK.muted }}>
                {label}
            </p>
            {children}
        </div>
    );
}
