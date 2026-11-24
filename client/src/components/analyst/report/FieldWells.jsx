import React, { useState } from 'react';
import { X, Rows3, Columns3, Sigma, Weight } from 'lucide-react';
import { BORDER, INK, ACCENT } from '../../../theme/vizTheme';
import { AGGREGATIONS } from '../../../state/reportTypes';
import { useReport } from '../../../state/ReportContext';
import { useDataset } from '../../../state/DatasetContext';
import { FIELD_MIME, placeField } from '../../../utils/fieldAssign';

/**
 * What the selected visual is actually asking for.
 *
 * These four wells are the pivot request, shown as a form: Rows and Columns
 * are what it groups by, Values is what it aggregates, and the aggregation
 * dropdown is the verb. Making that mapping visible is most of what teaches
 * somebody how the tool thinks.
 *
 * The file this replaces, PivotBuilder.jsx, existed as a zero-byte
 * placeholder.
 */
export default function FieldWells() {
    const { profile } = useDataset();
    const { report, dispatch } = useReport();

    const visual = report.pages
        .find((p) => p.id === report.activePageId)
        ?.visuals.find((v) => v.id === report.selectedVisualId);

    const columnOf = (name) => profile?.columns?.[name] || Object.values(profile?.columns || {}).find((c) => c.name === name);
    // A field dropped on a well goes in that well; dropped here with no
    // visual selected, it starts a new Matrix in its natural well.
    const dropInto = (well) => (name) => {
        const column = columnOf(name);
        if (column) placeField(dispatch, visual || null, column, well || undefined);
    };

    if (!visual) {
        return (
            <div className="px-3 py-3">
                <DropZone onDropField={dropInto(null)}>
                    <p className="px-1 py-2 text-[10.5px] leading-relaxed" style={{ color: INK.muted }}>
                        No visual selected. Drop a field here, or click one, to start a new table.
                    </p>
                </DropZone>
            </div>
        );
    }

    const { rows, cols, values, agg, weightCol } = visual.fieldWells;
    const remove = (well, field) =>
        dispatch({ type: 'REMOVE_FIELD', visualId: visual.id, well, field });

    // A weighted average needs to know what to weight by, and offering the
    // wrong kind of column would only produce an error from the backend.
    const measureNames = Object.values(profile?.columns || {})
        .filter((c) => c.role === 'measure')
        .map((c) => c.name);

    return (
        <div className="px-3 py-2 space-y-3">
            <Well label="Rows" icon={<Rows3 size={11} />} fields={rows}
                  hint="What to group by — drop a field here" onRemove={(f) => remove('rows', f)}
                  onDropField={dropInto('rows')} />
            <Well label="Columns" icon={<Columns3 size={11} />} fields={cols}
                  hint="Optional — splits into a cross-tab" onRemove={(f) => remove('cols', f)}
                  onDropField={dropInto('cols')} />
            <Well label="Values" icon={<Sigma size={11} />} fields={values}
                  hint="What to measure — drop a field here" onRemove={(f) => remove('values', f)}
                  onDropField={dropInto('values')} />

            <div>
                <Label>Aggregation</Label>
                <select
                    value={agg}
                    onChange={(e) => dispatch({ type: 'SET_AGG', visualId: visual.id, agg: e.target.value })}
                    className="w-full mt-1 px-2 py-1.5 rounded text-[11.5px] outline-none"
                    style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER}`, color: INK.primary }}
                >
                    {AGGREGATIONS.map((a) => (
                        <option key={a.value} value={a.value} style={{ background: '#18181b' }}>
                            {a.label}
                        </option>
                    ))}
                </select>
            </div>

            {agg === 'weighted_avg' && (
                <div>
                    <Label>
                        <Weight size={10} className="inline mr-1" />
                        Weight by
                    </Label>
                    <select
                        value={weightCol || ''}
                        onChange={(e) =>
                            dispatch({ type: 'SET_WEIGHT_COL', visualId: visual.id, column: e.target.value || null })
                        }
                        className="w-full mt-1 px-2 py-1.5 rounded text-[11.5px] outline-none"
                        style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${BORDER}`, color: INK.primary }}
                    >
                        <option value="" style={{ background: '#18181b' }}>Choose a column…</option>
                        {measureNames.map((n) => (
                            <option key={n} value={n} style={{ background: '#18181b' }}>{n}</option>
                        ))}
                    </select>
                    <p className="mt-1 text-[10px] leading-relaxed" style={{ color: INK.muted }}>
                        sum(weight × value) ÷ sum(weight) — an average where larger rows
                        count for more.
                    </p>
                </div>
            )}
        </div>
    );
}

function Label({ children }) {
    return (
        <span className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: INK.muted }}>
            {children}
        </span>
    );
}

/** Accepts a field dragged from the Fields pane, highlighting while one is over it. */
function DropZone({ onDropField, className = '', children }) {
    const [over, setOver] = useState(false);
    const accepts = (e) => e.dataTransfer.types.includes(FIELD_MIME);
    return (
        <div
            onDragOver={(e) => {
                if (!accepts(e)) return;
                e.preventDefault();
                e.dataTransfer.dropEffect = 'copy';
                if (!over) setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
                setOver(false);
                const name = e.dataTransfer.getData(FIELD_MIME);
                if (!name) return;
                e.preventDefault();
                onDropField(name);
            }}
            className={`rounded p-1 ${className}`}
            style={{
                background: over ? 'rgba(57,135,229,0.14)' : 'rgba(255,255,255,0.02)',
                border: `1px dashed ${over ? ACCENT : BORDER}`,
            }}
        >
            {children}
        </div>
    );
}

function Well({ label, icon, fields, hint, onRemove, onDropField }) {
    return (
        <div>
            <Label>{icon} {label}</Label>
            <DropZone onDropField={onDropField} className="mt-1 min-h-[30px] space-y-1">
                {fields.length === 0 ? (
                    <p className="px-1 py-0.5 text-[10.5px]" style={{ color: INK.faint }}>{hint}</p>
                ) : (
                    fields.map((f) => (
                        <div
                            key={f}
                            className="flex items-center gap-1 px-1.5 py-1 rounded text-[11px]"
                            style={{ background: 'rgba(57,135,229,0.12)', color: '#a9caf5' }}
                        >
                            <span className="flex-1 truncate">{f}</span>
                            <button
                                onClick={() => onRemove(f)}
                                className="p-0.5 rounded hover:bg-white/10 transition-colors"
                                aria-label={`Remove ${f}`}
                                style={{ color: ACCENT }}
                            >
                                <X size={10} />
                            </button>
                        </div>
                    ))
                )}
            </DropZone>
        </div>
    );
}
