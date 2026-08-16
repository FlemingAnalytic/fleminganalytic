import React from 'react';
import { Database, RefreshCw } from 'lucide-react';
import { DatasetProvider, useDataset } from '../state/DatasetContext';
import { ReportProvider } from '../state/ReportContext';
import ReportHeader from '../components/analyst/report/ReportHeader';
import LeftRail from '../components/analyst/report/LeftRail';
import ReportCanvas from '../components/analyst/report/ReportCanvas';
import RightRail from '../components/analyst/report/RightRail';
import StatusBar from '../components/analyst/report/StatusBar';
import { CANVAS, INK, BORDER, ACCENT } from '../theme/vizTheme';

/**
 * The analyst report.
 *
 * This page used to be a dataset inspector: four tabs, one view visible at a
 * time, a single chart of the first twenty preview rows. Tabs are the
 * opposite of what a report is for - the whole point is seeing several
 * answers at once and watching them all move when you narrow the question.
 *
 * So: visuals on the left to add, a canvas of them in the middle, fields and
 * filters on the right, and every number on screen aggregated server-side by
 * the pivot engine rather than sampled from a preview.
 */
export default function AnalystLab() {
    return (
        <DatasetProvider>
            <ReportProvider>
                <ReportShell />
            </ReportProvider>
        </DatasetProvider>
    );
}

function ReportShell() {
    const { hasDataset, sessionLost } = useDataset();

    return (
        <div className="report-root h-[calc(100vh-80px)] flex flex-col" style={{ background: CANVAS }}>
            <ReportHeader />

            {sessionLost && <SessionLostBanner />}

            <div className="flex-1 flex min-h-0">
                <LeftRail />
                {hasDataset ? <ReportCanvas /> : <NoDataset />}
                {hasDataset && <RightRail />}
            </div>

            <StatusBar />
        </div>
    );
}

/**
 * The backend keeps loaded dataframes in the memory of a single worker
 * process, so a restart loses them while this page still holds the session
 * name. Every tile would otherwise fill with the same error at once; one
 * banner naming the actual cause is more use than eight copies of its
 * symptom.
 */
function SessionLostBanner() {
    return (
        <div
            className="shrink-0 flex items-center gap-2 px-3 py-2 text-[11.5px]"
            style={{ background: 'rgba(217,89,38,0.12)', borderBottom: `1px solid ${BORDER}`, color: '#f0a888' }}
        >
            <RefreshCw size={12} />
            The server no longer holds this dataset — it was restarted. Load it again
            from the Data panel; your layout is kept.
        </div>
    );
}

function NoDataset() {
    return (
        <div className="flex-1 flex flex-col items-center justify-center gap-3" style={{ background: CANVAS }}>
            <Database size={40} style={{ color: 'rgba(255,255,255,0.10)' }} />
            <p className="text-[13px]" style={{ color: INK.secondary }}>Choose a dataset to begin</p>
            <p className="text-[11px] max-w-xs text-center leading-relaxed" style={{ color: INK.muted }}>
                Pick one from the Data panel on the left. The report opens with a few
                visuals already built from what the profiler finds.
            </p>
            <span className="text-[10px] px-2 py-0.5 rounded" style={{ color: ACCENT, background: 'rgba(57,135,229,0.12)' }}>
                Saved · Samples · URL
            </span>
        </div>
    );
}
