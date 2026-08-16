import React, { useCallback, useMemo } from 'react';
import { BarChart3, FilterX, Layers, Sigma } from 'lucide-react';
import Tile, { TileError, TileMessage, TileSkeleton } from './Tile';
import MatrixVisual from './visuals/MatrixVisual';
import ColumnVisual from './visuals/ColumnVisual';
import { usePivot } from '../../../hooks/usePivot';
import { useDataset } from '../../../state/DatasetContext';
import { useReport } from '../../../state/ReportContext';
import { describeWells } from '../../../utils/pivotRequest';
import { describeFilters, effectiveFilters } from '../../../utils/filterMerge';
import { topN } from '../../../utils/pivotTransform';
import { AXIS_CARDINALITY_LIMIT } from '../../../state/reportTypes';

/**
 * One visual: its data, its states, and its part in cross-filtering.
 *
 * The tile decides what to draw; the visual components below it only know
 * how to draw. Keeping the states here means a matrix and a column chart
 * cannot disagree about what "empty" or "loading" looks like, which they
 * would within a week if each handled its own.
 */
export default function VisualTile({ visual }) {
    const { profile } = useDataset();
    const { report, dispatch, debouncedFilters } = useReport();
    const data = usePivot(visual);

    const selected = report.selectedVisualId === visual.id;
    const crossFilter = report.filters.crossFilter;
    const selection = crossFilter?.sourceId === visual.id ? crossFilter : null;

    const filterLabels = useMemo(() => {
        const settled = { ...report, filters: debouncedFilters };
        return describeFilters(effectiveFilters(settled, visual.id, profile));
    }, [report, debouncedFilters, visual.id, profile]);

    const handleSelect = useCallback(
        (column, value, additive) => {
            if (!visual.interactions?.crossFilter) return;
            dispatch({ type: 'SET_CROSS_FILTER', sourceId: visual.id, column, value, additive });
        },
        [dispatch, visual.id, visual.interactions]
    );

    // A dimension with thousands of distinct values returns all of them -
    // /analyst/pivot has no top-N - so the chart shows the largest and says
    // so, rather than drawing 31,864 unreadable bars or silently cutting.
    const { rows, truncated } = useMemo(() => {
        if (visual.type !== 'column') return { rows: data.rows, truncated: false };
        return topN(data.rows, data.measures[0], AXIS_CARDINALITY_LIMIT);
    }, [data.rows, data.measures, visual.type]);

    const title = visual.title || describeWells(visual.fieldWells);
    const subtitle = data.status === 'ready' || data.status === 'stale'
        ? `${data.rows.length} ${data.rows.length === 1 ? 'category' : 'categories'}`
        : null;

    const frame = (children, note = null) => (
        <Tile
            title={title}
            subtitle={subtitle}
            filterLabels={filterLabels}
            selected={selected}
            stale={data.status === 'stale'}
            truncatedNote={note}
            currentType={visual.type}
            onSelect={() => dispatch({ type: 'SELECT_VISUAL', visualId: visual.id })}
            onRemove={() => dispatch({ type: 'REMOVE_VISUAL', visualId: visual.id })}
            onDuplicate={() => dispatch({ type: 'DUPLICATE_VISUAL', visualId: visual.id })}
            onChangeType={(t) => dispatch({ type: 'SET_VISUAL_TYPE', visualId: visual.id, visualType: t })}
        >
            {children}
        </Tile>
    );

    if (data.status === 'unconfigured') {
        return frame(
            <TileMessage
                icon={<Layers size={20} />}
                title="Nothing to show yet"
                detail="Pick a field for Rows and one for Values in the Fields pane."
            />
        );
    }

    if (data.status === 'loading') return frame(<TileSkeleton />);

    if (data.status === 'error') {
        return frame(<TileError message={data.error?.message || data.message} />);
    }

    // The measure has no value at all for at least one of these groups, so
    // the server produced a NaN it could not send. Counting rows asks a
    // question that always has an answer, so the tile offers that rather
    // than leaving the user to work out which of two fields to change.
    if (data.status === 'aggregation-failed') {
        return frame(
            <TileMessage
                icon={<Sigma size={20} />}
                title="The server could not summarise this"
                detail={`Some ${visual.fieldWells.rows[0]} groups have no ${visual.fieldWells.values[0]} at all, and an average of nothing cannot be returned.`}
                action={
                    visual.fieldWells.agg !== 'count' && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                dispatch({ type: 'SET_AGG', visualId: visual.id, agg: 'count' });
                            }}
                            className="mt-1 px-2.5 py-1 rounded text-[11px] hover:bg-white/[0.06] transition-colors"
                            style={{ border: '1px solid rgba(255,255,255,0.12)', color: '#c3c2b7' }}
                        >
                            Count rows instead
                        </button>
                    )
                }
            />
        );
    }

    if (data.status === 'empty') {
        return frame(
            <TileMessage
                icon={<FilterX size={20} />}
                title="No data for the current selection"
                detail="The filters in play exclude every row this visual would show."
                action={
                    <button
                        onClick={(e) => { e.stopPropagation(); dispatch({ type: 'CLEAR_ALL_FILTERS' }); }}
                        className="mt-1 px-2.5 py-1 rounded text-[11px] hover:bg-white/[0.06] transition-colors"
                        style={{ border: '1px solid rgba(255,255,255,0.12)', color: '#c3c2b7' }}
                    >
                        Clear filters
                    </button>
                }
            />
        );
    }

    const note = truncated
        ? `Showing the top ${AXIS_CARDINALITY_LIMIT} of ${data.rows.length} categories by value.`
        : null;

    if (visual.type === 'matrix') {
        return frame(
            <MatrixVisual
                rows={data.rows}
                columns={data.columns}
                rowDims={data.rowDims}
                measures={data.measures}
                agg={visual.fieldWells.agg}
                selection={selection}
                onSelect={handleSelect}
            />,
            null
        );
    }

    if (!data.measures.length) {
        return frame(
            <TileMessage icon={<BarChart3 size={20} />} title="No measure to plot" />
        );
    }

    return frame(
        <ColumnVisual
            rows={rows}
            rowDims={data.rowDims}
            measures={data.measures}
            selection={selection}
            onSelect={handleSelect}
        />,
        note
    );
}
