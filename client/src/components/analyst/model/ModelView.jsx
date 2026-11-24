import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Brain, Download, Loader2, Play, Search } from 'lucide-react';
import { useDataset } from '../../../state/DatasetContext';
import { analystApi } from '../../../services/api';
import { CANVAS, SURFACE, SURFACE_RAISED, BORDER, BORDER_STRONG, INK, ACCENT } from '../../../theme/vizTheme';

/**
 * The auto-learning view.
 *
 * The premise of the rest of the app is that the analyst knows what they want
 * to ask. The premise here is the opposite: they do not know which columns
 * relate to which, and should not have to. So the view opens by sweeping the
 * dataset for targets that are actually predictable and ranking them, and a
 * target is chosen from that list rather than guessed at. Everything after
 * the choice - regression or classification, which features, which estimator -
 * is decided for them and shown, not asked.
 *
 * The one thing it insists on saying out loud is leakage. A score of 1.00
 * against columns that are arithmetic restatements of the target looks like
 * the best result on the page and is worth nothing, and someone who does not
 * know the relationships is exactly the person who cannot see it coming.
 */
export default function ModelView() {
    const { filename, hasDataset, profile } = useDataset();

    const [scan, setScan] = useState(null);
    const [scanning, setScanning] = useState(false);
    const [error, setError] = useState(null);

    const [target, setTarget] = useState(null);
    const [features, setFeatures] = useState([]);
    const [testSize, setTestSize] = useState(0.2);
    const [timeSeries, setTimeSeries] = useState(false);
    const [timeCol, setTimeCol] = useState('');
    const [taskOverride, setTaskOverride] = useState('auto');

    const [training, setTraining] = useState(false);
    const [result, setResult] = useState(null);

    const columns = Object.keys(profile?.columns || {});
    const dateColumns = columns.filter((c) => {
        const t = profile?.columns?.[c]?.type || '';
        return /date|time/i.test(t) || /date|month|year|period/i.test(c);
    });

    const runScan = useCallback(async () => {
        if (!filename) return;
        setScanning(true);
        setError(null);
        setResult(null);
        try {
            setScan(await analystApi.discover(filename));
        } catch (err) {
            setError(err?.response?.data?.detail || 'Could not scan this dataset.');
        } finally {
            setScanning(false);
        }
    }, [filename]);

    // Scan on arrival: the view is useless until it knows what is predictable,
    // and making the analyst press a button first is asking them to opt in to
    // the only thing the screen does.
    useEffect(() => {
        if (hasDataset) runScan();
    }, [hasDataset, runScan]);

    const chooseTarget = (finding) => {
        setTarget(finding);
        setTaskOverride('auto');
        setResult(null);
        // Its own drivers are the sensible starting feature set - they are what
        // made it score in the first place.
        const drivers = finding.drivers.map((d) => d.column);
        setFeatures(drivers.length ? drivers : columns.filter((c) => c !== finding.target).slice(0, 8));
    };

    const toggleFeature = (col) => {
        setFeatures((f) => (f.includes(col) ? f.filter((c) => c !== col) : [...f, col]));
    };

    const train = async () => {
        if (!target || !features.length) return;
        setTraining(true);
        setError(null);
        try {
            setResult(await analystApi.trainModel(filename, {
                target: target.target,
                features,
                testSize,
                task: taskOverride,
                timeSeries,
                timeCol: timeSeries ? timeCol : '',
            }));
        } catch (err) {
            setError(err?.response?.data?.detail || 'Training failed.');
        } finally {
            setTraining(false);
        }
    };

    if (!hasDataset) {
        return <Empty message="Open a dataset to start." />;
    }

    return (
        <div className="flex-1 overflow-auto" style={{ background: CANVAS }}>
            <div className="max-w-5xl mx-auto p-5 flex flex-col gap-4">

                <Panel>
                    <div className="flex items-start gap-3">
                        <Brain size={16} style={{ color: ACCENT, marginTop: 2 }} />
                        <div className="flex-1 min-w-0">
                            <h2 className="text-[13px] font-semibold" style={{ color: INK.primary }}>
                                What this data can predict
                            </h2>
                            <p className="text-[11px] mt-0.5" style={{ color: INK.muted }}>
                                {scanning
                                    ? 'Testing every column against the others…'
                                    : scan?.headline || 'Not scanned yet.'}
                            </p>
                        </div>
                        <button
                            onClick={runScan}
                            disabled={scanning}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] disabled:opacity-50"
                            style={{ border: `1px solid ${BORDER_STRONG}`, color: INK.secondary }}
                        >
                            {scanning ? <Loader2 size={11} className="animate-spin" /> : <Search size={11} />}
                            Rescan
                        </button>
                    </div>

                    {scan?.findings?.length > 0 && (
                        <div className="mt-3 flex flex-col gap-1.5">
                            {scan.findings.map((f) => (
                                <TargetRow
                                    key={f.target}
                                    finding={f}
                                    selected={target?.target === f.target}
                                    onSelect={() => chooseTarget(f)}
                                />
                            ))}
                        </div>
                    )}

                    {scan?.columns_skipped?.length > 0 && (
                        <p className="text-[10px] mt-3 leading-relaxed" style={{ color: INK.faint }}>
                            Not offered as targets:{' '}
                            {scan.columns_skipped.map((s) => `${s.column} (${s.reason})`).join(' · ')}
                        </p>
                    )}
                </Panel>

                {target && (
                    <Panel>
                        <h2 className="text-[13px] font-semibold" style={{ color: INK.primary }}>
                            Predicting {target.target}
                        </h2>
                        <p className="text-[11px] mt-0.5" style={{ color: INK.muted }}>
                            Treated as {target.task}. Everything below has a working default — change it only if you want to.
                        </p>

                        <Field label="Columns to learn from">
                            <div className="flex flex-wrap gap-1.5">
                                {columns.filter((c) => c !== target.target).map((c) => (
                                    <button
                                        key={c}
                                        onClick={() => toggleFeature(c)}
                                        className="px-2 py-0.5 rounded text-[11px] transition-colors"
                                        style={features.includes(c)
                                            ? { background: 'rgba(79,150,234,0.20)', color: '#9dc6f5', border: `1px solid ${ACCENT}` }
                                            : { border: `1px solid ${BORDER}`, color: INK.muted }}
                                    >
                                        {c}
                                    </button>
                                ))}
                            </div>
                        </Field>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                            <Field label={`Hold back ${Math.round(testSize * 100)}% to test on`}>
                                <input
                                    type="range" min="5" max="50" step="5"
                                    value={testSize * 100}
                                    onChange={(e) => setTestSize(Number(e.target.value) / 100)}
                                    className="w-full"
                                />
                                <p className="text-[10px] mt-1" style={{ color: INK.faint }}>
                                    The model never sees these rows while learning, so its score on them is the honest one.
                                </p>
                            </Field>

                            <Field label="Task">
                                <select
                                    value={taskOverride}
                                    onChange={(e) => setTaskOverride(e.target.value)}
                                    className="w-full px-2 py-1 rounded text-[11px]"
                                    style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}`, color: INK.secondary }}
                                >
                                    <option value="auto">Decide for me ({target.task})</option>
                                    <option value="regression">Predict a number</option>
                                    <option value="classification">Predict a category</option>
                                </select>
                            </Field>
                        </div>

                        {dateColumns.length > 0 && (
                            <Field label="Time series">
                                <label className="flex items-center gap-2 text-[11px]" style={{ color: INK.secondary }}>
                                    <input type="checkbox" checked={timeSeries}
                                           onChange={(e) => { setTimeSeries(e.target.checked); if (!timeCol) setTimeCol(dateColumns[0]); }} />
                                    Test on the most recent rows, not a random sample
                                </label>
                                {timeSeries && (
                                    <select
                                        value={timeCol}
                                        onChange={(e) => setTimeCol(e.target.value)}
                                        className="mt-1.5 px-2 py-1 rounded text-[11px]"
                                        style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}`, color: INK.secondary }}
                                    >
                                        {dateColumns.map((c) => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                )}
                                <p className="text-[10px] mt-1" style={{ color: INK.faint }}>
                                    Splitting time-ordered data at random trains on the future to predict the past, which
                                    reports a score the model could never reach in use.
                                </p>
                            </Field>
                        )}

                        <button
                            onClick={train}
                            disabled={training || !features.length}
                            className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded text-[12px] font-medium disabled:opacity-50"
                            style={{ background: ACCENT, color: '#04121f' }}
                        >
                            {training ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                            {training ? 'Training…' : 'Train a model'}
                        </button>
                    </Panel>
                )}

                {error && (
                    <Panel>
                        <p className="text-[12px]" style={{ color: '#e66767' }}>{error}</p>
                    </Panel>
                )}

                {result?.stats && <Results stats={result.stats} filename={filename} saved={result.saved_model} />}
            </div>
        </div>
    );
}

function TargetRow({ finding, selected, onSelect }) {
    const pct = Math.max(0, Math.min(1, finding.score));
    return (
        <button
            onClick={onSelect}
            className="w-full text-left px-3 py-2 rounded transition-colors"
            style={{
                background: selected ? 'rgba(79,150,234,0.12)' : SURFACE_RAISED,
                border: `1px solid ${selected ? ACCENT : BORDER}`,
            }}
        >
            <div className="flex items-center gap-2">
                <span className="text-[12px] font-medium truncate" style={{ color: INK.primary }}>
                    {finding.target}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.07)', color: INK.muted }}>
                    {finding.task === 'classification' ? 'category' : 'number'}
                </span>
                {finding.suspect_leakage && (
                    <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(201,133,0,0.18)', color: '#e0a838' }}>
                        <AlertTriangle size={9} /> check this
                    </span>
                )}
                <span className="flex-1" />
                <span className="text-[11px] tabular-nums" style={{ color: INK.secondary }}>
                    {finding.score.toFixed(2)}
                </span>
            </div>

            <div className="mt-1.5 h-1 rounded overflow-hidden" style={{ background: 'rgba(255,255,255,0.07)' }}>
                <div style={{ width: `${pct * 100}%`, height: '100%', background: finding.suspect_leakage ? '#c98500' : ACCENT }} />
            </div>

            <p className="text-[10px] mt-1.5" style={{ color: INK.muted }}>
                driven by {finding.drivers.slice(0, 4).map((d) => d.column).join(', ')}
            </p>
            {finding.leakage_note && (
                <p className="text-[10px] mt-1 leading-relaxed" style={{ color: '#e0a838' }}>
                    {finding.leakage_note}
                </p>
            )}
        </button>
    );
}

function Results({ stats, filename, saved }) {
    const classification = stats.task === 'classification';
    const metrics = classification
        ? [['Accuracy', stats.test_accuracy], ['F1 (weighted)', stats.test_f1],
           ['Precision', stats.test_precision], ['Recall', stats.test_recall]]
        : [['R-squared', stats.test_r2], ['Avg error (MAE)', stats.test_mae],
           ['RMSE', stats.test_rmse], ['Target average', stats.target_mean]];

    return (
        <Panel>
            <div className="flex items-start gap-3">
                <div className="flex-1">
                    <h2 className="text-[13px] font-semibold" style={{ color: INK.primary }}>
                        {stats.model_type.replace(/_/g, ' ')} won
                    </h2>
                    <p className="text-[11px] mt-0.5" style={{ color: INK.muted }}>
                        Chosen on {stats.selected_by} · trained on {stats.train_samples.toLocaleString()} rows,
                        tested on {stats.test_samples.toLocaleString()} it had never seen
                        {stats.time_series ? ` · split in ${stats.time_col} order` : ''}
                    </p>
                </div>
                <a
                    href={analystApi.exportModelUrl(filename)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] shrink-0"
                    style={{ border: `1px solid ${BORDER_STRONG}`, color: INK.secondary }}
                >
                    <Download size={11} /> Download .pkl
                </a>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">
                {metrics.map(([label, value]) => (
                    <div key={label} className="px-2.5 py-2 rounded" style={{ background: SURFACE_RAISED, border: `1px solid ${BORDER}` }}>
                        <div className="text-[15px] font-semibold tabular-nums" style={{ color: INK.primary }}>
                            {value ?? '—'}
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: INK.muted }}>{label}</div>
                    </div>
                ))}
            </div>

            {classification && stats.classes && (
                <p className="text-[10px] mt-2.5" style={{ color: INK.muted }}>
                    Predicting {stats.n_classes} categories: {stats.classes.join(', ')}
                </p>
            )}

            {saved && (
                <p className="text-[10px] mt-2.5" style={{ color: INK.faint }}>
                    Saved on the server as {saved} — it survives a restart, so the download stays available.
                </p>
            )}
        </Panel>
    );
}

function Panel({ children }) {
    return (
        <section className="rounded p-4" style={{ background: SURFACE, border: `1px solid ${BORDER}` }}>
            {children}
        </section>
    );
}

function Field({ label, children }) {
    return (
        <div className="mt-3">
            <div className="text-[10px] uppercase tracking-wider mb-1.5" style={{ color: INK.muted }}>{label}</div>
            {children}
        </div>
    );
}

function Empty({ message }) {
    return (
        <div className="flex-1 flex items-center justify-center" style={{ background: CANVAS }}>
            <p className="text-[12px]" style={{ color: INK.muted }}>{message}</p>
        </div>
    );
}
