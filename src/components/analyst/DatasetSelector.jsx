import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, Globe, Link, Search, ChevronRight, HardDrive, Share2, Layers, Cpu, Radio } from 'lucide-react'
import { useDatasetViewModel } from '../../viewmodels/datasetViewModel'

const DatasetSelector = ({ onDatasetLoaded }) => {
    const {
        savedDatasets,
        loading,
        activeTab,
        setActiveTab,
        url,
        setUrl,
        loadSaved,
        loadPublic,
        loadUrl
    } = useDatasetViewModel(onDatasetLoaded);

    const PUBLIC_SAMPLES = [
        // Foundation
        { id: 'titanic', label: 'Classic: Titanic Survivors', category: 'Foundation' },
        { id: 'tips', label: 'Retail: Restaurant Analytics', category: 'Foundation' },
        { id: 'iris', label: 'Biology: Iris Flower Species', category: 'Foundation' },
        { id: 'diamonds', label: 'Physical: Gemstone Grading', category: 'Foundation' },
        { id: 'mpg', label: 'Auto: Fuel Efficiency', category: 'Foundation' },
        
        // Strategic
        { id: 'sp500_companies', label: 'Finance: S&P 500 Matrix', category: 'Strategic' },
        { id: 'world_happiness', label: 'Society: Global Sentiment', category: 'Strategic' },
        { id: 'gapminder', label: 'Global: Health & Wealth', category: 'Strategic' },
        { id: 'us_car_dealerships', label: 'Retail: US Car Dealerships', category: 'Strategic' },
        
        // Research (Scientific & Demographic)
        { id: 'seattle_weather', label: 'Climate: Seattle Weather', category: 'Research' },
        { id: 'state_unemployment', label: 'Econ: US Job Matrix', category: 'Research' },
        { id: 'nyc_311_calls', label: 'Urban: NYC 311 Stream', category: 'Research' },
        { id: 'census_county_pop', label: 'Census: County Pop Growth', category: 'Research' }
    ]

    return (
        <div className="flex flex-col h-full bg-[#050505] overflow-hidden">
            {/* Header Area */}
            <div className="p-10 pb-6 space-y-8 bg-[#080808] border-b border-white/5">
                <div className="flex items-center justify-between">
                    <h3 className="text-[12px] font-black uppercase tracking-[0.3em] text-blue-500 flex items-center gap-3">
                        <Radio size={16} className="animate-pulse" /> DATA_INGESTION
                    </h3>
                    <div className="px-3 py-1 bg-blue-500/10 rounded border border-blue-500/20 text-[8px] font-black text-blue-400 uppercase tracking-widest">V3.1 CORE</div>
                </div>
                
                <div className="flex gap-2 p-1 bg-black rounded-lg border border-white/5 shadow-inner">
                    <TabBtn active={activeTab === 'saved'} onClick={() => setActiveTab('saved')} label="LOCAL" icon={<HardDrive size={14} />} />
                    <TabBtn active={activeTab === 'public'} onClick={() => setActiveTab('public')} label="GLOBAL" icon={<Globe size={14} />} />
                    <TabBtn active={activeTab === 'url'} onClick={() => setActiveTab('url')} label="LINK" icon={<Link size={14} />} />
                </div>
            </div>

            {/* List with Motion */}
            <div className="flex-1 overflow-y-auto px-6 py-10 space-y-4 scrollbar-hide">
                <AnimatePresence mode="wait">
                    {activeTab === 'saved' && (
                        <motion.div 
                            key="saved"
                            initial={{ opacity: 0, x: -5 }} 
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 5 }}
                            className="space-y-4"
                        >
                            {loading ? <SkeletonRows /> : 
                            savedDatasets.length > 0 ? (
                                savedDatasets.map(ds => (
                                    <DatasetItem key={ds.filename} title={ds.display_name} sub={ds.filename} onClick={() => loadSaved(ds.filename)} />
                                ))
                            ) : <EmptyState msg="NO NODES DETECTED" icon={<Database size={32} />} />}
                        </motion.div>
                    )}

                    {activeTab === 'public' && (
                        <motion.div key="public" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 px-2">
                             {['Foundation', 'Strategic', 'Research'].map(cat => (
                               <div key={cat} className="space-y-4">
                                   <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/20 border-l-2 border-blue-500 pl-4">{cat} Matrix</h4>
                                   <div className="space-y-2">
                                       {PUBLIC_SAMPLES.filter(p => p.category === cat).map(p => (
                                           <DatasetItem key={p.id} title={p.label} sub={p.category} onClick={() => loadPublic(p.id)} />
                                       ))}
                                   </div>
                               </div> 
                            ))}
                        </motion.div>
                    )}

                    {activeTab === 'url' && (
                        <motion.div key="url" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                            <div className="space-y-3">
                                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/20 border-l-2 border-blue-500 pl-4">Remote Data Stream</h4>
                                <div className="space-y-4">
                                    <div className="relative group">
                                        <input 
                                            type="text" 
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                            placeholder="https://example.com/data.csv"
                                            className="w-full bg-white/[0.02] border border-white/5 rounded-xl px-5 py-4 text-xs font-bold text-white placeholder:text-white/10 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/30 outline-none transition-all"
                                        />
                                    </div>
                                    <button 
                                        onClick={() => loadUrl()}
                                        disabled={!url || loading}
                                        className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] text-white hover:shadow-lg hover:shadow-blue-500/20 transition-all disabled:opacity-50 disabled:grayscale"
                                    >
                                        Establish Connection
                                    </button>
                                </div>
                            </div>
                            <div className="p-6 rounded-xl bg-blue-500/[0.03] border border-blue-500/10 space-y-3">
                                <p className="text-[8px] font-black text-blue-400/60 uppercase tracking-widest">Protocol Support:</p>
                                <div className="flex flex-wrap gap-2">
                                    {['CSV', 'JSON', 'XLSX'].map(f => (
                                        <span key={f} className="px-2 py-1 bg-blue-500/10 rounded text-[7px] font-black text-blue-400">{f}</span>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            
            <div className="p-8 border-t border-white/5 bg-[#080808] flex items-center gap-4">
                <Cpu size={24} className="text-white/10" />
                <p className="text-[9px] font-black uppercase tracking-[0.15em] text-white/20 italic leading-relaxed">
                    Fleming Analytic Neural Core v3.1<br/>Secure Multi-Feed Data Stream Ingestion
                </p>
            </div>
        </div>
    )
}

const TabBtn = ({ active, onClick, label, icon }) => (
    <button onClick={onClick} className={`flex-1 flex items-center justify-center gap-2 py-3 rounded text-[10px] font-black uppercase tracking-widest transition-all duration-300 ${active ? 'bg-blue-600 text-white shadow-lg' : 'text-white/20 hover:text-white/50 hover:bg-white/5'}`}>
        {icon} {label}
    </button>
)

const DatasetItem = ({ title, sub, onClick }) => (
    <button onClick={onClick} className="w-full text-left p-6 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] group border border-white/5 hover:border-blue-500/30 transition-all duration-300 shadow-sm">
        <div className="flex justify-between items-center mb-2">
            <span className="text-[13px] font-bold tracking-tight text-white/80 group-hover:text-blue-400">{title}</span>
            <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 text-blue-500 transition-all transform -translate-x-2 group-hover:translate-x-0" />
        </div>
        <p className="text-[9px] font-black uppercase tracking-widest text-white/10 group-hover:text-white/30 truncate">{sub}</p>
    </button>
)

const SkeletonRows = () => (
    <div className="space-y-4">
        {[1,2,3,4].map(i => <div key={i} className="h-24 bg-white/[0.01] rounded-xl border border-white/5" />)}
    </div>
)

const EmptyState = ({ msg, icon }) => (
    <div className="flex flex-col items-center justify-center p-12 space-y-6 opacity-20 filter grayscale">
        <div className="p-6 bg-white/5 rounded-full">{icon}</div>
        <p className="text-[10px] font-black uppercase tracking-[0.2em]">{msg}</p>
    </div>
)

export default DatasetSelector
