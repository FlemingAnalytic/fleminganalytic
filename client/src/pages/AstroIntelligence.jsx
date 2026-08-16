import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Calendar, MapPin, Search, Download, FileText, Info, Compass } from 'lucide-react'
import { astroApi } from '../services/api'

const AstroIntelligence = () => {
    const [formData, setFormData] = useState({
        name: '',
        year: 1990,
        month: 1,
        day: 1,
        hour: 12,
        minute: 0,
        city: 'New York',
        country: 'USA'
    })
    const [chart, setChart] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleGenerate = async (e) => {
        e.preventDefault()
        setLoading(true)
        try {
            const result = await astroApi.generateChart(formData)
            setChart(result)
        } catch (err) {
            console.error('Astro error:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadPdf = async () => {
         try {
            const result = await astroApi.generatePdf(formData)
            window.open(result.full_pdf_url, '_blank')
        } catch (err) {
            console.error('PDF error:', err)
        }
    }

    return (
        <div className="bg-[#050510] min-h-screen text-slate-100 font-sans tracking-tight">
            <main className="max-w-7xl mx-auto p-12 overflow-y-auto">
                <header className="flex justify-between items-center mb-16 border-b border-white/5 pb-10">
                    <div>
                        <h2 className="text-4xl font-black tracking-tighter bg-gradient-to-r from-amber-200 via-indigo-400 to-purple-600 bg-clip-text text-transparent drop-shadow-sm mb-2 uppercase">Astro-Intelligence</h2>
                        <p className="text-sm opacity-40 font-bold uppercase tracking-widest leading-none">Celestial Geolocation & Natal Signal Engine</p>
                    </div>
                </header>

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                    {/* Birth Data Input */}
                    <div className="xl:col-span-4 space-y-10">
                        <section className="glass-panel p-10 border-amber-500/10 bg-slate-900/40 relative overflow-hidden group">
                           <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-all duration-700">
                               <Compass size={120} className="rotate-12" />
                           </div>
                           
                           <h3 className="text-xs font-black uppercase tracking-widest text-amber-500/60 mb-8 flex items-center gap-3">
                               <Sparkles size={14} /> Natal Genesis Parameters
                           </h3>

                           <form onSubmit={handleGenerate} className="space-y-8 relative z-10">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1">Subject Name</label>
                                    <input 
                                        value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm font-bold outline-none focus:ring-2 focus:ring-amber-500/30 transition"
                                        placeholder="Enter subject name..." required
                                    />
                                </div>

                                <div className="grid grid-cols-3 gap-4">
                                    <InputGroup label="Year" value={formData.year} onChange={(v) => setFormData({...formData, year: parseInt(v)})} />
                                    <InputGroup label="Month" value={formData.month} onChange={(v) => setFormData({...formData, month: parseInt(v)})} />
                                    <InputGroup label="Day" value={formData.day} onChange={(v) => setFormData({...formData, day: parseInt(v)})} />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <InputGroup label="Hour (0-23)" value={formData.hour} onChange={(v) => setFormData({...formData, hour: parseInt(v)})} />
                                    <InputGroup label="Minute" value={formData.minute} onChange={(v) => setFormData({...formData, minute: parseInt(v)})} />
                                </div>

                                <div className="space-y-4">
                                    <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1">Coordinate Synthesis (City, Country)</label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} className="bg-white/5 border border-white/10 rounded-2xl p-5 text-sm font-bold outline-none" placeholder="City" />
                                        <input value={formData.country} onChange={(e) => setFormData({...formData, country: e.target.value})} className="bg-white/5 border border-white/10 rounded-2xl p-5 text-sm font-bold outline-none" placeholder="Country" />
                                    </div>
                                </div>

                                <button 
                                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 p-6 rounded-2xl font-black text-xs uppercase tracking-widest shadow-2xl shadow-indigo-500/20 transform hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-50"
                                    disabled={loading}
                                >
                                    {loading ? 'Synthesizing Celestial Data...' : 'Generate Natal Intelligence'}
                                </button>
                           </form>
                        </section>
                    </div>

                    {/* Chart & Interpretations */}
                    <div className="xl:col-span-8">
                        <AnimatePresence mode="wait">
                            {chart ? (
                                <motion.div 
                                    key={chart.chart_id}
                                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                                    className="space-y-12"
                                >
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                                        <div className="glass-panel p-10 bg-slate-900/60 border-amber-500/10 flex items-center justify-center min-h-[500px]">
                                            <img src={`${chart.chart_url}`} alt="Natal Chart" className="w-full h-auto drop-shadow-2xl" />
                                        </div>
                                        <div className="space-y-8">
                                            <div className="glass-panel p-10 bg-gradient-to-br from-indigo-950/40 to-transparent border-indigo-500/10">
                                                <h3 className="text-xl font-black mb-6 flex items-center gap-4 uppercase tracking-tighter">
                                                    <Compass size={24} className="text-amber-400" /> Rising Interpretation
                                                </h3>
                                                <p className="text-sm opacity-70 leading-relaxed font-medium">{chart.rising_interpretation}</p>
                                            </div>

                                            <div className="grid grid-cols-2 gap-6">
                                                <MiniCard label="Primary Element" value={chart.element_analysis.dominant_element} icon={<Sparkles size={16} />} />
                                                <MiniCard label="Modality Focus" value={chart.element_analysis.dominant_modality} icon={<Activity size={16} />} />
                                            </div>

                                            <button 
                                                onClick={handleDownloadPdf}
                                                className="w-full glass-panel p-6 border-white/10 hover:bg-white/5 flex items-center justify-center gap-4 text-xs font-black uppercase tracking-widest transition"
                                            >
                                                <FileText size={18} /> Download Comprehensive PDF Report
                                            </button>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="text-xs font-black uppercase tracking-widest opacity-40 mb-10 border-b border-white/5 pb-6">Natal Observations</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {chart.observations.map((obs, i) => (
                                                <div key={i} className="p-8 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all duration-300">
                                                    <p className="text-xs font-bold leading-relaxed">{obs}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </motion.div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center py-40 opacity-10">
                                    <Sparkles size={120} className="mb-8" />
                                    <p className="font-black text-sm uppercase tracking-widest">Awaiting Genesis Parameters</p>
                                </div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </main>
        </div>
    )
}

const InputGroup = ({ label, value, onChange }) => (
    <div className="space-y-4">
        <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1">{label}</label>
        <input 
            type="number" value={value} onChange={(e) => onChange(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-2xl p-5 text-sm font-bold outline-none"
        />
    </div>
)

const MiniCard = ({ label, value, icon }) => (
    <div className="glass-panel p-6 bg-slate-900/40 border-white/5 flex items-center gap-5">
        <div className="text-amber-400 bg-amber-400/10 p-3 rounded-xl">{icon}</div>
        <div>
            <p className="text-[9px] font-black uppercase tracking-widest opacity-30 leading-none mb-2">{label}</p>
            <p className="text-sm font-black uppercase tracking-wider">{value}</p>
        </div>
    </div>
)

export default AstroIntelligence
