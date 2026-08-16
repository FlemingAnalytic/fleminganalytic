import React, { useRef } from 'react';
import { Download, FilterX, RotateCcw, Upload, Database } from 'lucide-react';
import { useDataset } from '../../../state/DatasetContext';
import { useReport } from '../../../state/ReportContext';
import { activeFilterCount } from '../../../utils/filterMerge';
import { exportReport, parseReport, clearReport } from '../../../hooks/useReportPersistence';
import { formatCount } from '../../../utils/format';
import { BORDER, INK, ACCENT, SURFACE } from '../../../theme/vizTheme';

/**
 * What is loaded, what is filtered, and the two irreversible-looking buttons.
 *
 * The filter count is here rather than only in the right rail because a
 * cross-filter set three visuals ago is otherwise invisible while it quietly
 * shapes everything on the canvas - and the way out of that state should be
 * where the user is looking when they notice.
 */
export default function ReportHeader() {
    const { displayName, rowCount, colCount, hasDataset } = useDataset();
    const { report, dispatch } = useReport();
    const fileInput = useRef(null);

    const filters = activeFilterCount(report);

    const onImport = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            const imported = parseReport(await file.text(), report.filename);
            dispatch({ type: 'LOAD_REPORT', report: imported });
        } catch (err) {
            console.error('Could not read that report file:', err);
        } finally {
            event.target.value = '';
        }
    };

    return (
        <header
            className="h-12 shrink-0 flex items-center gap-3 px-3"
            style={{ background: SURFACE, borderBottom: `1px solid ${BORDER}` }}
        >
            <div className="flex items-center gap-2 min-w-0">
                <Database size={14} style={{ color: ACCENT }} />
                <div className="min-w-0">
                    <h1 className="text-[13px] font-semibold leading-tight truncate" style={{ color: INK.primary }}>
                        {displayName || 'Analyst'}
                    </h1>
                    {hasDataset && (
                        <p className="text-[10px] leading-tight" style={{ color: INK.muted }}>
                            {formatCount(rowCount)} rows · {colCount} columns
                        </p>
                    )}
                </div>
            </div>

            <div className="flex-1" />

            {filters > 0 && (
                <button
                    onClick={() => dispatch({ type: 'CLEAR_ALL_FILTERS' })}
                    className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] transition-colors hover:brightness-125"
                    style={{ background: 'rgba(57,135,229,0.16)', color: '#8bb9f2' }}
                >
                    <FilterX size={11} />
                    {filters} filter{filters === 1 ? '' : 's'} · clear
                </button>
            )}

            {hasDataset && (
                <>
                    <HeaderButton icon={<Upload size={12} />} label="Import"
                                  onClick={() => fileInput.current?.click()} />
                    <HeaderButton icon={<Download size={12} />} label="Export"
                                  onClick={() => exportReport(report, displayName)} />
                    <HeaderButton
                        icon={<RotateCcw size={12} />} label="Reset"
                        onClick={() => {
                            // The saved layout goes too, otherwise the next
                            // load restores exactly what was just discarded.
                            clearReport(report.filename);
                            dispatch({ type: 'RESET_REPORT' });
                        }}
                    />
                    <input ref={fileInput} type="file" accept="application/json"
                           className="hidden" onChange={onImport} />
                </>
            )}
        </header>
    );
}

function HeaderButton({ icon, label, onClick }) {
    return (
        <button
            onClick={onClick}
            className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] transition-colors hover:bg-white/[0.06]"
            style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}
        >
            {icon} {label}
        </button>
    );
}
