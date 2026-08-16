import React from 'react';
import { LayoutGrid, Plus } from 'lucide-react';
import VisualTile from './VisualTile';
import { useReport } from '../../../state/ReportContext';
import { createVisual } from '../../../state/reportTypes';
import { CANVAS, INK, BORDER } from '../../../theme/vizTheme';

/**
 * Where the visuals live.
 *
 * A twelve-column grid, with each tile's width and height in grid units.
 * Not a drag-and-drop surface yet - positions come from the report state and
 * are set when a tile is created, which is enough to lay out a report and
 * leaves the same `position` field for a drag layer to write into later.
 *
 * Clicking the canvas itself clears the current cross-filter. That gesture
 * is worth having because a selection made in one tile changes every other
 * one, and hunting for the exact bar that started it to click it again is a
 * poor way out.
 */
export default function ReportCanvas() {
    const { report, dispatch } = useReport();
    const page = report.pages.find((p) => p.id === report.activePageId);
    const visuals = page?.visuals || [];

    return (
        <div
            className="flex-1 overflow-y-auto scrollbar-hide p-3"
            style={{ background: CANVAS }}
            onClick={() => {
                if (report.filters.crossFilter) dispatch({ type: 'CLEAR_CROSS_FILTER' });
                dispatch({ type: 'SELECT_VISUAL', visualId: null });
            }}
        >
            {visuals.length === 0 ? (
                <EmptyCanvas onAdd={() => dispatch({ type: 'ADD_VISUAL', visual: createVisual() })} />
            ) : (
                <div className="grid grid-cols-12 gap-3 auto-rows-[64px]">
                    {visuals.map((visual) => (
                        <div
                            key={visual.id}
                            onClick={(e) => e.stopPropagation()}
                            style={{
                                gridColumn: `span ${Math.min(12, visual.position.w)} / span ${Math.min(12, visual.position.w)}`,
                                gridRow: `span ${visual.position.h} / span ${visual.position.h}`,
                            }}
                            className="min-w-0"
                        >
                            <div className="h-full">
                                <div className="h-full flex flex-col">
                                    <VisualTileWrapper visual={visual} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/** Keeps the tile filling its grid cell, whatever the visual inside it does. */
function VisualTileWrapper({ visual }) {
    return (
        <div className="h-full [&>section]:h-full [&>section]:flex [&>section]:flex-col">
            <VisualTile visual={visual} />
        </div>
    );
}

function EmptyCanvas({ onAdd }) {
    return (
        <div className="h-full flex flex-col items-center justify-center gap-3">
            <LayoutGrid size={36} style={{ color: 'rgba(255,255,255,0.10)' }} />
            <p className="text-[12.5px]" style={{ color: INK.secondary }}>This page has no visuals</p>
            <button
                onClick={(e) => { e.stopPropagation(); onAdd(); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11.5px] hover:bg-white/[0.06] transition-colors"
                style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}
            >
                <Plus size={12} /> Add a visual
            </button>
        </div>
    );
}
