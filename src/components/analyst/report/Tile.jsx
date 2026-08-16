import React, { useState } from 'react';
import { Filter, MoreHorizontal, RefreshCw, Trash2, Copy, BarChart3, Table2 } from 'lucide-react';
import { BORDER, SURFACE, ACCENT, INK } from '../../../theme/vizTheme';

/**
 * The frame every visual sits in.
 *
 * There was no shared card, panel or table component anywhere in this app -
 * each page invented its own surface inline, which is why nothing looked
 * like it belonged with anything else. One frame, used by every visual type
 * and by the panes, is most of what makes a canvas of tiles read as a single
 * product rather than a collection of widgets.
 *
 * The states matter more than the styling. A tile is nearly always in one of
 * six conditions - unconfigured, loading, showing stale data while it
 * refetches, ready, empty because a filter excluded everything, or broken -
 * and each needs to look different enough to act on without reading.
 */
export default function Tile({
    title,
    subtitle,
    filterLabels = [],
    selected = false,
    stale = false,
    truncatedNote = null,
    onSelect,
    onRemove,
    onDuplicate,
    onChangeType,
    currentType,
    children,
}) {
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <section
            onClick={onSelect}
            className="relative flex flex-col rounded-lg overflow-hidden transition-colors duration-150 cursor-default"
            style={{
                background: SURFACE,
                border: `1px solid ${selected ? ACCENT : BORDER}`,
                boxShadow: selected ? `0 0 0 1px ${ACCENT}33` : 'none',
            }}
        >
            {/* Refetching with data already on screen: a thread at the top
                edge rather than a spinner over the content, so the numbers
                stay readable while they are being replaced. */}
            {stale && (
                <div className="absolute top-0 left-0 right-0 h-[2px] overflow-hidden z-10">
                    <div className="h-full w-1/3 animate-[tileProgress_1.1s_ease-in-out_infinite]"
                         style={{ background: ACCENT }} />
                </div>
            )}

            <header className="flex items-start justify-between gap-2 px-3 pt-2.5 pb-2">
                <div className="min-w-0">
                    <h3 className="text-[12.5px] font-semibold leading-tight truncate"
                        style={{ color: INK.primary }}>
                        {title}
                    </h3>
                    {subtitle && (
                        <p className="text-[10.5px] mt-0.5 truncate" style={{ color: INK.muted }}>
                            {subtitle}
                        </p>
                    )}
                </div>

                <div className="flex items-center gap-1 shrink-0">
                    {filterLabels.length > 0 && (
                        <span
                            title={filterLabels.join('\n')}
                            className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px]"
                            style={{ background: 'rgba(57,135,229,0.14)', color: '#8bb9f2' }}
                        >
                            <Filter size={10} /> {filterLabels.length}
                        </span>
                    )}
                    <div className="relative">
                        <button
                            onClick={(e) => { e.stopPropagation(); setMenuOpen((o) => !o); }}
                            className="p-1 rounded hover:bg-white/[0.06] transition-colors"
                            style={{ color: INK.muted }}
                            aria-label="Visual options"
                        >
                            <MoreHorizontal size={14} />
                        </button>
                        {menuOpen && (
                            <>
                                <div className="fixed inset-0 z-20"
                                     onClick={(e) => { e.stopPropagation(); setMenuOpen(false); }} />
                                <div className="absolute right-0 top-full mt-1 z-30 w-44 rounded-md py-1 shadow-xl"
                                     style={{ background: '#18181b', border: `1px solid ${BORDER}` }}>
                                    {onChangeType && (
                                        <>
                                            <MenuItem icon={<Table2 size={12} />} label="Show as matrix"
                                                      active={currentType === 'matrix'}
                                                      onClick={() => { onChangeType('matrix'); setMenuOpen(false); }} />
                                            <MenuItem icon={<BarChart3 size={12} />} label="Show as column chart"
                                                      active={currentType === 'column'}
                                                      onClick={() => { onChangeType('column'); setMenuOpen(false); }} />
                                            <div className="my-1 h-px" style={{ background: BORDER }} />
                                        </>
                                    )}
                                    {onDuplicate && (
                                        <MenuItem icon={<Copy size={12} />} label="Duplicate"
                                                  onClick={() => { onDuplicate(); setMenuOpen(false); }} />
                                    )}
                                    {onRemove && (
                                        <MenuItem icon={<Trash2 size={12} />} label="Remove" danger
                                                  onClick={() => { onRemove(); setMenuOpen(false); }} />
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </header>

            <div className="flex-1 min-h-0 px-3 pb-3">{children}</div>

            {truncatedNote && (
                <footer className="px-3 py-1.5 text-[10px] border-t"
                        style={{ borderColor: BORDER, color: INK.muted }}>
                    {truncatedNote}
                </footer>
            )}
        </section>
    );
}

function MenuItem({ icon, label, onClick, active, danger }) {
    return (
        <button
            onClick={(e) => { e.stopPropagation(); onClick(); }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-[11.5px] text-left hover:bg-white/[0.06] transition-colors"
            style={{ color: danger ? '#e66767' : active ? ACCENT : INK.secondary }}
        >
            {icon} {label}
        </button>
    );
}

/** The states a tile body can be in, styled once so every visual agrees. */
export function TileSkeleton() {
    return (
        <div className="h-full w-full flex flex-col gap-2 justify-end pb-2 animate-pulse">
            {[0.45, 0.7, 0.35, 0.9, 0.6].map((h, i) => (
                <div key={i} className="rounded-sm" style={{ height: `${h * 18}%`, background: 'rgba(255,255,255,0.045)' }} />
            ))}
        </div>
    );
}

export function TileMessage({ icon, title, detail, action }) {
    return (
        <div className="h-full w-full flex flex-col items-center justify-center text-center gap-2 px-4">
            {icon && <div style={{ color: INK.faint }}>{icon}</div>}
            <p className="text-[12px] font-medium" style={{ color: INK.secondary }}>{title}</p>
            {detail && <p className="text-[10.5px] leading-relaxed" style={{ color: INK.muted }}>{detail}</p>}
            {action}
        </div>
    );
}

export function TileError({ message, onRetry }) {
    return (
        <TileMessage
            icon={<RefreshCw size={20} />}
            title="This visual could not load"
            detail={message}
            action={
                onRetry && (
                    <button onClick={(e) => { e.stopPropagation(); onRetry(); }}
                            className="mt-1 px-2.5 py-1 rounded text-[11px] transition-colors hover:bg-white/[0.06]"
                            style={{ border: `1px solid ${BORDER}`, color: INK.secondary }}>
                        Retry
                    </button>
                )
            }
        />
    );
}
