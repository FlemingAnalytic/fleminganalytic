/**
 * One place where pivot queries are actually issued.
 *
 * The backend runs a single gunicorn worker, because its dataset sessions
 * live in that process's memory. Every request the canvas makes is therefore
 * queued behind every other one, and a canvas of eight tiles that all
 * refetch when a bar is clicked can put eight requests in that queue in the
 * same frame - repeatedly, as the user keeps clicking.
 *
 * Three things keep that in hand, and all of them need to be in one module
 * because they share a key:
 *
 *   cache     an answer already received is not asked for again, which is
 *             what makes toggling a selection off feel instant;
 *   inflight  two tiles asking the identical question share one request
 *             rather than racing each other;
 *   aborters  a tile that asks a new question cancels its previous one, so
 *             a slow answer to a question nobody is asking any more cannot
 *             arrive late and overwrite a fresh one.
 *
 * The pivot itself is fast - around 56ms on a 100k-row frame - so none of
 * this is about the backend being slow. It is about not building a queue.
 */

import { analystApi } from './api';

const MAX_CACHE_ENTRIES = 120;

const cache = new Map();      // key -> result
const inflight = new Map();   // key -> Promise
const aborters = new Map();   // tileId -> AbortController

/** Map iteration is insertion-ordered, so the oldest key is the first one. */
function remember(key, value) {
    cache.set(key, value);
    if (cache.size > MAX_CACHE_ENTRIES) {
        cache.delete(cache.keys().next().value);
    }
}

export function getCached(key) {
    return cache.has(key) ? cache.get(key) : null;
}

/**
 * Throw away everything.
 *
 * Called when the dataset changes, and after a classification is created -
 * that adds a derived column to the frame the pivot engine sees, so answers
 * computed before it are answers about a different table.
 */
export function invalidateCache() {
    cache.clear();
    inflight.clear();
}

export function cancelTile(tileId) {
    const controller = aborters.get(tileId);
    if (controller) {
        controller.abort();
        aborters.delete(tileId);
    }
}

export class SessionExpiredError extends Error {
    constructor() {
        super('The backend no longer holds this dataset');
        this.name = 'SessionExpiredError';
    }
}

/**
 * The server could not serialise its own answer.
 *
 * A group in which every row is missing the measure aggregates to NaN, and
 * NaN is not valid JSON - the response fails to encode and the whole request
 * comes back 500 with no body worth reading. Nothing about the question was
 * wrong, so this is not "your visual is broken": it is one combination of
 * field and grouping the backend cannot currently answer.
 *
 * Verified on chicagoland: grouping by zip (302 values) and averaging `beds`
 * returns 200, while averaging `sqft` - which is missing in 7.9% of rows -
 * returns 500. Fine groupings simply make an all-missing group likelier.
 * Counting never produces NaN, which is why the tile offers it as a way out.
 */
export class AggregationFailedError extends Error {
    constructor() {
        super('The server could not summarise this combination');
        this.name = 'AggregationFailedError';
    }
}

/**
 * A cancelled request is not a failure - it means the user moved on.
 * Callers check this rather than rendering an error for their own doing.
 */
export function isAbort(error) {
    return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError';
}

/**
 * Run a pivot, or reuse one already run.
 *
 * @param {string} key      from pivotKey(request)
 * @param {object} request  from buildPivotRequest()
 * @param {string} tileId   whose request this is, for cancellation
 */
export async function fetchPivot(key, request, tileId) {
    const hit = getCached(key);
    if (hit) return hit;

    const shared = inflight.get(key);
    if (shared) return shared;

    cancelTile(tileId);
    const controller = new AbortController();
    aborters.set(tileId, controller);

    const promise = analystApi
        .pivotQuery(request, { signal: controller.signal })
        .then((result) => {
            // create_pivot catches its own exceptions and answers 200 with an
            // {error} body, so the HTTP status says nothing about whether
            // this worked. The one error worth distinguishing is a session
            // the backend has forgotten, which is fixed by reloading the
            // dataset rather than by changing the question.
            if (result?.error && /not loaded|no dataset|session/i.test(result.error)) {
                throw new SessionExpiredError();
            }
            remember(key, result);
            return result;
        })
        .catch((error) => {
            if (isAbort(error)) throw error;
            // A 500 here is the NaN serialisation failure above, not a
            // network problem: the request was well-formed and the server
            // built an answer it then could not send.
            if (error?.response?.status === 500) throw new AggregationFailedError();
            throw error;
        })
        .finally(() => {
            inflight.delete(key);
            if (aborters.get(tileId) === controller) aborters.delete(tileId);
        });

    inflight.set(key, promise);
    return promise;
}

/** For the tests and the status bar. */
export function cacheStats() {
    return { cached: cache.size, inflight: inflight.size };
}
