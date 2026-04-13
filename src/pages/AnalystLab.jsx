import React, { useState } from 'react'
import DatasetSelector from '../components/analyst/DatasetSelector'
import DataProfile from '../components/analyst/DataProfile'
import Visualizer from '../components/analyst/Visualizer'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, FlaskConical, PieChart, Cpu, Sparkles, LayoutGrid } from 'lucide-react'
import { useAnalystViewModel } from '../viewmodels/analystViewModel'

const AnalystLab = () => {
    const { 
        dataset, 
        activeView, 
        handleDatasetLoaded, 
        switchView 
    } = useAnalystViewModel();

    return (
        <div className="bg-black min-h-screen text-slate-100 font-sans selection:bg-blue-500/30">
            {/* Ambient Background Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full animate-pulse" />
                <div className="absolute top-[60%] -right-[10%] w-[35%] h-[35%] bg-purple-600/10 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 contrast-150 brightness-100 mix-blend-overlay pointer-events-none" />
            </div>

            <main className="flex h-[calc(100vh-80px)] overflow-hidden relative z-10 font-outfit">
                {/* Unified Sidebar Container */}
                <div className="w-[380px] flex flex-col border-r border-white/5 bg-[#080808] shrink-0 shadow-2xl z-20">
                    <DatasetSelector onDatasetLoaded={handleDatasetLoaded} />
                </div>

                {/* Content Workspace */}
                <div className="flex-1 flex flex-col relative overflow-hidden bg-[#050505]">
                    {/* Header Workspace Bar */}
                    <header className="px-12 py-8 flex justify-between items-center bg-black/20 backdrop-blur-md border-b border-white/[0.03] z-50">
                        <div className="flex items-center gap-6">
                            <div className="p-3 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-600/20">
                                <FlaskConical size={24} className="text-white" />
                            </div>
                            <div>
                                <h2 className="text-3xl font-black tracking-tighter text-white drop-shadow-sm flex items-center gap-3">
                                    SMART ANALYST <span className="text-blue-500 italic font-medium opacity-80">LAB</span>
                                </h2>
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 drop-shadow-sm mt-1">Multi-Channel Strategic Inference Engine</p>
                            </div>
                        </div>

                        {dataset && (
                            <nav className="flex items-center gap-1 p-1 bg-white/[0.03] rounded-2xl border border-white/[0.05] shadow-inner">
                                <NavTab active={activeView === 'profile'} onClick={() => switchView('profile')} label="Insights" icon={<Sparkles size={14} />} />
                                <NavTab active={activeView === 'preview'} onClick={() => switchView('preview')} label="Assets" icon={<LayoutGrid size={14} />} />
                                <NavTab active={activeView === 'predict'} onClick={() => switchView('predict')} label="Inference" icon={<Cpu size={14} />} />
                                <NavTab active={activeView === 'visualize'} onClick={() => switchView('visualize')} label="Patterns" icon={<PieChart size={14} />} />
                            </nav>
                        )}
                    </header>

                    {/* Scrollable Workspace Container */}
                    <div className="flex-1 overflow-y-auto px-16 py-16 scrollbar-hide relative bg-transparent scroll-smooth">
                        <AnimatePresence mode="wait">
                            {!dataset ? (
                                <motion.div 
                                    className="h-full flex flex-col items-center justify-center gap-10"
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.8, ease: "easeOut" }}
                                >
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-blue-500/20 blur-3xl rounded-full" />
                                        <Database size={160} className="stroke-[0.3px] text-blue-500/40 relative z-10 animate-float" />
                                    </div>
                                    <div className="text-center max-w-md space-y-4">
                                        <h3 className="text-2xl font-black tracking-tight text-white/90">Awaiting Data Ingestion</h3>
                                        <p className="text-xs font-medium text-white/30 uppercase tracking-[0.15em] leading-relaxed">
                                            Select a specialized dataset from the library or import a remote CSV URL to begin high-fidelity strategic modeling.
                                        </p>
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.div 
                                    key={`${dataset.filename}-${activeView}`}
                                    initial={{ opacity: 0, y: 10, filter: 'blur(10px)' }}
                                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                                    exit={{ opacity: 0, y: -10, filter: 'blur(10px)' }}
                                    transition={{ duration: 0.5, ease: "anticipate" }}
                                    className="max-w-[1440px] mx-auto"
                                >
                                    {activeView === 'profile' && <DataProfile profile={dataset.profile} />}
                                    {activeView === 'preview' && <DataPreview data={dataset.preview} />}
                                    {activeView === 'predict' && <PredictiveTerminal dataset={dataset} />}
                                    {activeView === 'visualize' && <Visualizer dataset={dataset} />}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Bottom Status Ticker */}
                    <div className="h-8 border-t border-white/[0.03] bg-black/40 backdrop-blur-md px-12 flex items-center justify-between text-[9px] font-bold uppercase tracking-widest text-white/20">
                        <div className="flex gap-6 items-center">
                            <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Engine: Operational</span>
                            <span>Latency: 14ms</span>
                        </div>
                        <div className="italic opacity-50 font-black tracking-[0.2em]">Fleming Analytic Neural Core v3.1</div>
                    </div>
                </div>
            </main>
        </div>
    )
}

const NavTab = ({ active, onClick, label, icon }) => (
    <button 
        onClick={onClick} 
        className={`px-6 py-3 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] transition-all duration-500 flex items-center gap-3 border border-transparent
        ${active 
            ? 'bg-blue-600/10 text-blue-400 border-blue-500/20 shadow-[0_0_20px_rgba(37,99,235,0.1)]' 
            : 'text-white/30 hover:text-white/60 hover:bg-white/[0.02]'}`}
    >
        {icon} {label}
    </button>
)

const DataPreview = ({ data }) => {
    if (!data || data.length === 0) return null
    const headers = Object.keys(data[0])

    return (
        <div className="bg-[#0A0A0A] border border-white/[0.05] shadow-2xl rounded-[32px] overflow-hidden group">
            <div className="overflow-x-auto scrollbar-hide">
                <table className="w-full border-collapse">
                    <thead className="bg-white/[0.02] border-b border-white/[0.05]">
                        <tr>
                            {headers.map(h => (
                                <th key={h} className="px-8 py-8 text-left text-[10px] font-black uppercase tracking-[0.2em] text-white/30 whitespace-nowrap border-r border-white-[0.02] last:border-0">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.03]">
                        {data.slice(0, 50).map((row, i) => (
                            <tr key={i} className="hover:bg-blue-600/[0.03] transition duration-300 group/row">
                                {headers.map(h => (
                                    <td key={h} className="px-8 py-6 text-xs font-semibold text-white/60 border-r border-white/[0.02] last:border-0 whitespace-nowrap overflow-hidden text-ellipsis max-w-[240px] group-hover/row:text-white/90 transform transition-colors">
                                        {String(row[h])}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="p-8 bg-white/[0.01] border-t border-white/[0.03] text-[10px] font-bold uppercase tracking-[0.3em] text-white/10 text-center">
                Visualizing Top 50 Strategic Datapoints • Dynamic Content Stream Active
            </div>
        </div>
    )
}

const PredictiveTerminal = () => (
    <div className="flex flex-col items-center justify-center p-32 space-y-8 bg-white/[0.01] rounded-[40px] border border-dashed border-white/5">
        <Cpu size={64} className="text-blue-500/20" />
        <div className="text-center space-y-2">
            <p className="text-sm font-black uppercase tracking-[0.4em] text-blue-500/40">Inference Core Initialization</p>
            <p className="text-[10px] font-medium text-white/10 uppercase tracking-[0.2em]">Synthetic Strategy Prediction Module Booting...</p>
        </div>
    </div>
)

const VisualizationLab = () => (
    <div className="flex flex-col items-center justify-center p-32 space-y-8 bg-white/[0.01] rounded-[40px] border border-dashed border-white/5">
        <PieChart size={64} className="text-purple-500/20" />
        <div className="text-center space-y-2">
            <p className="text-sm font-black uppercase tracking-[0.4em] text-purple-500/40">Pattern Matrix Active</p>
            <p className="text-[10px] font-medium text-white/10 uppercase tracking-[0.2em]">Initializing 3D Spatial Geometry Rendering Engine...</p>
        </div>
    </div>
)

export default AnalystLab
