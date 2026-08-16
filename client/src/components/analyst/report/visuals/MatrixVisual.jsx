import React from 'react';
import { BORDER, INK, ACCENT } from '../../../../theme/vizTheme';
import { formatValue } from '../../../../utils/format';
import { deriveTotals } from '../../../../utils/pivotTransform';

/**
 * The pivot result as a table.
 *
 * This is the visual that tells the truth about what the backend returned -
 * a chart can look plausible while plotting the wrong column, but a matrix
 * showing the wrong numbers is obviously showing the wrong numbers. It is
 * the first thing seeded onto a new report for that reason.
 *
 * It renders the response's own flattened column names, so a cross-tab
 * ("North | 2024") comes through without the client having to reconstruct
 * the shape pandas took apart.
 *
 * The total row is computed here rather than taken from the response.
 * PivotEngine appends a `_is_total` row built with `.sum()` whatever the
 * aggregation was, so a mean-aggregated pivot arrives with a total that is
 * the sum of the group means - a number six times larger than any real value
 * and not the mean of anything. `deriveTotals` only produces a footer for
 * sums and counts, where folding the rows is genuinely equivalent, and
 * returns nothing otherwise instead of guessing.
 */
export default function MatrixVisual({ rows, columns, rowDims, measures, agg, onSelect, selection }) {
    const totals = deriveTotals(rows, measures, agg);
    const dimKey = rowDims[0];
    const selectedValues = new Set((selection?.values || []).map(String));
    const hasSelection = selectedValues.size > 0;

    return (
        <div className="h-full overflow-auto scrollbar-hide -mx-1">
            <table className="w-full border-collapse text-[11.5px]">
                <thead className="sticky top-0 z-10" style={{ background: '#141417' }}>
                    <tr>
                        {columns.map((col, i) => {
                            const isDim = rowDims.includes(col);
                            return (
                                <th
                                    key={col}
                                    className={`px-2.5 py-1.5 font-semibold whitespace-nowrap ${isDim ? 'text-left' : 'text-right'} ${i === 0 ? 'sticky left-0' : ''}`}
                                    style={{
                                        color: INK.secondary,
                                        borderBottom: `1px solid ${BORDER}`,
                                        background: i === 0 ? '#141417' : undefined,
                                    }}
                                >
                                    {col}
                                </th>
                            );
                        })}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, r) => {
                        const value = dimKey ? row[dimKey] : null;
                        const isSelected = hasSelection && selectedValues.has(String(value));
                        return (
                            <tr
                                key={r}
                                onClick={(e) => dimKey && onSelect?.(dimKey, value, e.ctrlKey || e.metaKey)}
                                className="transition-colors"
                                style={{
                                    background: isSelected ? 'rgba(57,135,229,0.12)' : undefined,
                                    opacity: hasSelection && !isSelected ? 0.45 : 1,
                                    cursor: dimKey ? 'pointer' : 'default',
                                }}
                            >
                                {columns.map((col, i) => {
                                    const isDim = rowDims.includes(col);
                                    return (
                                        <td
                                            key={col}
                                            className={`px-2.5 py-1.5 whitespace-nowrap ${isDim ? 'text-left' : 'text-right tabular-nums'} ${i === 0 ? 'sticky left-0' : ''}`}
                                            style={{
                                                color: isDim ? INK.secondary : INK.primary,
                                                borderBottom: `1px solid rgba(255,255,255,0.035)`,
                                                background: i === 0 ? (isSelected ? '#16233a' : '#0f0f11') : undefined,
                                                maxWidth: 220,
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                            }}
                                        >
                                            {isDim ? String(row[col] ?? '—') : formatValue(row[col])}
                                        </td>
                                    );
                                })}
                            </tr>
                        );
                    })}
                </tbody>
                {totals && (
                    <tfoot className="sticky bottom-0" style={{ background: '#141417' }}>
                        <tr>
                            {columns.map((col, i) => {
                                const isDim = rowDims.includes(col);
                                return (
                                    <td
                                        key={col}
                                        className={`px-2.5 py-1.5 font-semibold whitespace-nowrap ${isDim ? 'text-left' : 'text-right tabular-nums'} ${i === 0 ? 'sticky left-0' : ''}`}
                                        style={{
                                            color: i === 0 ? INK.muted : ACCENT,
                                            borderTop: `1px solid ${BORDER}`,
                                            background: i === 0 ? '#141417' : undefined,
                                        }}
                                    >
                                        {i === 0 ? 'Total' : isDim ? '' : formatValue(totals[col])}
                                    </td>
                                );
                            })}
                        </tr>
                    </tfoot>
                )}
            </table>
        </div>
    );
}
