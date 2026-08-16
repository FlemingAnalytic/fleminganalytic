import React, { useMemo } from 'react';
import {
    Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import {
    axisProps, barGaps, barProps, DIM_OPACITY, gridProps, INK, MAX_SERIES,
    OTHER, seriesColor, tooltipProps,
} from '../../../../theme/vizTheme';
import { formatAxis, formatValue, truncateLabel } from '../../../../utils/format';

/**
 * A clustered column chart over a pivot result.
 *
 * One y-axis, always. Two measures of different magnitude go in two tiles -
 * a second axis lets any two series be made to look correlated by choosing
 * the scales, and the reader has no way to see that choice.
 *
 * Series colour comes from the category name, not its position in the
 * current result. Cross-filtering the data down to fewer categories then
 * leaves the survivors the colour they already were, instead of shuffling
 * every colour along by one and making the chart look like it changed
 * subject.
 */
export default function ColumnVisual({ rows, rowDims, measures, onSelect, selection }) {
    const dimKey = rowDims[0];

    // With column dimensions the backend flattens series into "North | 2024";
    // with none, the series are simply the measures. Either way, what is
    // plotted is "every returned column that is not a row dimension".
    const series = useMemo(() => {
        const shown = measures.slice(0, MAX_SERIES);
        const folded = measures.length - shown.length;
        return { shown, folded };
    }, [measures]);

    const selectedValues = new Set((selection?.values || []).map(String));
    const hasSelection = selectedValues.size > 0;

    const handleClick = (payload, event) => {
        if (!dimKey || !payload) return;
        const value = payload[dimKey] ?? payload.payload?.[dimKey];
        if (value === undefined) return;
        onSelect?.(dimKey, value, event?.ctrlKey || event?.metaKey);
    };

    return (
        <div className="h-full w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rows} margin={{ top: 6, right: 8, bottom: 4, left: 0 }} {...barGaps}>
                    <CartesianGrid {...gridProps} />
                    <XAxis
                        dataKey={dimKey}
                        {...axisProps}
                        interval="preserveStartEnd"
                        tickFormatter={(v) => truncateLabel(v, 14)}
                    />
                    <YAxis {...axisProps} width={52} tickFormatter={formatAxis} />
                    <Tooltip {...tooltipProps} formatter={(v, name) => [formatValue(v), name]} />
                    {/* A single series is named by the tile's own title; a
                        legend repeating it is furniture. Two or more always
                        get one, so identity is never carried by colour alone. */}
                    {series.shown.length > 1 && (
                        <Legend
                            wrapperStyle={{ fontSize: 11, color: INK.muted, paddingTop: 4 }}
                            iconType="circle"
                            iconSize={7}
                        />
                    )}
                    {series.shown.map((key) => (
                        <Bar
                            key={key}
                            dataKey={key}
                            name={key}
                            fill={seriesColor(key)}
                            onClick={handleClick}
                            cursor={dimKey ? 'pointer' : 'default'}
                            isAnimationActive={false}
                            {...barProps}
                        >
                            {/* Per-cell opacity so a live selection dims the
                                categories it excludes rather than removing
                                them - the reader keeps the context of what
                                was filtered out. */}
                            {rows.map((row, i) => {
                                const dim = hasSelection && selectedValues.has(String(row[dimKey]));
                                return (
                                    <Cell
                                        key={i}
                                        fillOpacity={!hasSelection || dim ? 1 : DIM_OPACITY}
                                    />
                                );
                            })}
                        </Bar>
                    ))}
                </BarChart>
            </ResponsiveContainer>

            {series.folded > 0 && (
                <p className="text-[10px] mt-1" style={{ color: OTHER }}>
                    {series.folded} further series not shown — the palette holds {MAX_SERIES}.
                </p>
            )}
        </div>
    );
}
