import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Filter, ListTree, SlidersHorizontal, X } from 'lucide-react';
import FieldsPane from './FieldsPane';
import FieldWells from './FieldWells';
import { useReport } from '../../../state/ReportContext';
import { BORDER, INK, SURFACE, ACCENT } from '../../../theme/vizTheme';

/**
 * Fields, wells, and what is currently filtered.
 *
 * The filters section is read-only in this milestone: it lists what is in
 * play and lets each one be removed. Adding filters from here needs the
 * value picker that slicers will bring, and a half-built filter editor is
 * worse than an honest list - this way nothing on screen claims a capability
 * that is not there, and every filter that exists can still be undone.
 */
export default function RightRail() {
    const { report, dispatch } = useReport();
    const [open, setOpen] = useState({ filters: true, fields: true, wells: true });

    const { page = {}, crossFilter } = report.filters;
    const pageEntries = Object.entries(page);
    const nothingFiltered = pageEntries.length === 0 && !crossFilter;

    return (
        <aside
            className="w-[300px] shrink-0 flex flex-col min-h-0"
            style={{ background: SURFACE, borderLeft: `1px solid ${BORDER}` }}
        >
            <Section
                label="Filters" icon={<Filter size={11} />}
                open={open.filters} onToggle={() => setOpen((o) => ({ ...o, filters: !o.filters }))}
            >
                {nothingFiltered ? (
                    <p className="px-3 pb-2 text-[10.5px]" style={{ color: INK.muted }}>
                        Nothing filtered. Click a bar or a row to filter every other visual by it.
                    </p>
                ) : (
                    <div className="px-3 pb-2 space-y-1">
                        {crossFilter && (
                            <FilterRow
                                label={crossFilter.column}
                                values={crossFilter.values}
                                origin="from a selection"
                                onClear={() => dispatch({ type: 'CLEAR_CROSS_FILTER' })}
                            />
                        )}
                        {pageEntries.map(([column, values]) => (
                            <FilterRow
                                key={column}
                                label={column}
                                values={values}
                                origin="page filter"
                                onClear={() =>
                                    dispatch({ type: 'SET_PAGE_FILTER', column, values: [] })
                                }
                            />
                        ))}
                    </div>
                )}
            </Section>

            <Section
                label="Fields" icon={<ListTree size={11} />} grow
                open={open.fields} onToggle={() => setOpen((o) => ({ ...o, fields: !o.fields }))}
            >
                <FieldsPane />
            </Section>

            <Section
                label="Field wells" icon={<SlidersHorizontal size={11} />}
                open={open.wells} onToggle={() => setOpen((o) => ({ ...o, wells: !o.wells }))}
            >
                {/* Capped rather than free-growing: a weighted average adds
                    two more controls, and the wells would otherwise take the
                    rail over. */}
                <div className="overflow-y-auto scrollbar-hide" style={{ maxHeight: '46vh' }}>
                    <FieldWells />
                </div>
            </Section>
        </aside>
    );
}

function Section({ label, icon, open, onToggle, grow, children }) {
    return (
        <div
            // The fields list grows into whatever is left, but not below the
            // height of a few rows: without the floor, opening the field
            // wells squeezed the field list until only its heading was
            // visible, which is the one thing on this rail that has to stay
            // usable while wells are being edited.
            className={`flex flex-col min-h-0 ${grow && open ? 'flex-1 min-h-[200px]' : 'shrink-0'}`}
            style={{ borderBottom: `1px solid ${BORDER}` }}
        >
            <button
                onClick={onToggle}
                className="w-full flex items-center gap-1.5 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.12em] hover:bg-white/[0.03] transition-colors shrink-0"
                style={{ color: INK.muted }}
            >
                {open ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                {icon}
                <span className="flex-1 text-left">{label}</span>
            </button>
            {open && <div className="flex-1 min-h-0 flex flex-col overflow-hidden">{children}</div>}
        </div>
    );
}

function FilterRow({ label, values, origin, onClear }) {
    const shown = values.slice(0, 3).join(', ');
    const more = values.length > 3 ? ` +${values.length - 3}` : '';
    return (
        <div
            className="flex items-start gap-1.5 px-2 py-1.5 rounded"
            style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${BORDER}` }}
        >
            <div className="min-w-0 flex-1">
                <p className="text-[11px] truncate" style={{ color: ACCENT }}>{label}</p>
                <p className="text-[10.5px] truncate" style={{ color: INK.secondary }}>{shown}{more}</p>
                <p className="text-[9.5px]" style={{ color: INK.faint }}>{origin}</p>
            </div>
            <button
                onClick={onClear}
                className="p-0.5 rounded hover:bg-white/10 transition-colors shrink-0"
                aria-label={`Clear filter on ${label}`}
                style={{ color: INK.muted }}
            >
                <X size={11} />
            </button>
        </div>
    );
}
