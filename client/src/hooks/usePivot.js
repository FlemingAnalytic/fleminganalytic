import { useEffect, useMemo, useRef, useState } from 'react';
import { useDataset } from '../state/DatasetContext';
import { useReport } from '../state/ReportContext';
import { buildPivotRequest, isQueryable, pivotKey } from '../utils/pivotRequest';
import { effectiveFilters } from '../utils/filterMerge';
import { stripTotals, measureColumns } from '../utils/pivotTransform';
import {
    AggregationFailedError, cancelTile, fetchPivot, getCached, isAbort, SessionExpiredError,
} from '../services/pivotClient';

/**
 * One tile's data.
 *
 * The status has a `stale` flag alongside `loading` because they call for
 * different treatment. A tile with nothing to show yet gets a skeleton; a
 * tile that already has numbers and is fetching newer ones keeps showing the
 * old ones, dimmed. Blanking a chart on every cross-filter click makes the
 * whole canvas flicker and reads as slower than it is, even though the
 * request underneath takes well under a tenth of a second.
 */
export function usePivot(visual) {
    const { filename, profile, reportSessionLost } = useDataset();
    const { report, debouncedFilters } = useReport();

    // Query off the debounced filters, so a run of clicks resolves to one
    // request per tile rather than one per click. The report object is read
    // through a stand-in that carries the settled filters.
    const settledReport = useMemo(
        () => ({ ...report, filters: debouncedFilters }),
        [report, debouncedFilters]
    );

    const queryable = Boolean(filename) && isQueryable(visual);

    const { key, request } = useMemo(() => {
        if (!queryable) return { key: null, request: null };
        const filters = effectiveFilters(settledReport, visual.id, profile);
        const req = buildPivotRequest(filename, visual, filters);
        return { key: pivotKey(req), request: req };
    }, [queryable, settledReport, visual, filename, profile]);

    // Seed from the cache during render, so a question already answered -
    // toggling a selection back off - draws without a loading frame at all.
    const [state, setState] = useState(() => ({
        result: key ? getCached(key) : null,
        loading: false,
        error: null,
    }));

    const activeKey = useRef(null);

    useEffect(() => {
        if (!key) {
            setState({ result: null, loading: false, error: null });
            return undefined;
        }

        const cached = getCached(key);
        if (cached) {
            activeKey.current = key;
            setState({ result: cached, loading: false, error: null });
            return undefined;
        }

        let live = true;
        activeKey.current = key;
        setState((prev) => ({ ...prev, loading: true, error: null }));

        fetchPivot(key, request, visual.id)
            .then((result) => {
                // A response for a question this tile has since stopped
                // asking is dropped rather than rendered.
                if (!live || activeKey.current !== key) return;
                setState({ result, loading: false, error: null });
            })
            .catch((err) => {
                if (!live || isAbort(err)) return;
                if (err instanceof SessionExpiredError) reportSessionLost();
                setState({ result: null, loading: false, error: err });
            });

        return () => {
            live = false;
        };
    }, [key, request, visual.id, reportSessionLost]);

    useEffect(() => () => cancelTile(visual.id), [visual.id]);

    return useMemo(() => {
        const { result, loading, error } = state;

        if (!queryable) {
            return { status: 'unconfigured', rows: [], columns: [], rowDims: [], measures: [] };
        }
        if (error) {
            const status = error instanceof AggregationFailedError ? 'aggregation-failed' : 'error';
            return { status, error, rows: [], columns: [], rowDims: [], measures: [] };
        }
        if (!result) {
            return { status: 'loading', rows: [], columns: [], rowDims: [], measures: [] };
        }

        // "No data after filters" is the backend saying the question is fine
        // and the answer is nothing - which is a normal thing for a
        // cross-filtered tile to be told, not a failure.
        if (result.error) {
            const empty = /no data/i.test(result.error);
            return {
                status: empty ? 'empty' : 'error',
                error: empty ? null : new Error(result.error),
                message: result.error,
                rows: [], columns: [], rowDims: [], measures: [],
            };
        }

        const { rows, columns, rowDims } = stripTotals(result);
        if (!rows.length) {
            return { status: 'empty', rows: [], columns, rowDims, measures: [] };
        }

        return {
            status: loading ? 'stale' : 'ready',
            rows,
            columns,
            rowDims,
            measures: measureColumns(columns, rowDims),
            hasColDims: Boolean(result.has_col_dims),
        };
    }, [state, queryable]);
}
