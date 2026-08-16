import React from 'react';
import { useDataset } from '../../../state/DatasetContext';
import { useReport } from '../../../state/ReportContext';
import { activeFilterCount } from '../../../utils/filterMerge';
import { BORDER, INK, SURFACE } from '../../../theme/vizTheme';

/**
 * The bar along the bottom.
 *
 * It replaces a decorative ticker that read "Engine: Operational · Latency:
 * 14ms · Neural Core v3.1" - none of which was measured, and the latency was
 * a literal in the markup. The same strip now carries things that are true
 * and occasionally useful: the session the backend is holding, how many
 * visuals are on the page, and how many filters are shaping them.
 */
export default function StatusBar() {
    const { filename, hasDataset } = useDataset();
    const { report } = useReport();

    const page = report.pages.find((p) => p.id === report.activePageId);
    const visuals = page?.visuals.length || 0;
    const filters = activeFilterCount(report);

    return (
        <footer
            className="h-7 shrink-0 flex items-center gap-4 px-3 text-[10px]"
            style={{ background: SURFACE, borderTop: `1px solid ${BORDER}`, color: INK.faint }}
        >
            {hasDataset ? (
                <>
                    <span>{visuals} visual{visuals === 1 ? '' : 's'}</span>
                    <span>{filters} filter{filters === 1 ? '' : 's'} active</span>
                    <span className="truncate">session: {filename}</span>
                </>
            ) : (
                <span>No dataset loaded</span>
            )}
            <span className="flex-1" />
            <span>Aggregated server-side · layout saved in this browser</span>
        </footer>
    );
}
