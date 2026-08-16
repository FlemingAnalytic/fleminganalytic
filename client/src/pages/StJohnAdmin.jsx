import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LayoutDashboard, Calendar, Users, Church, Image as ImageIcon, Settings, Plus, Save, Trash2, Edit, ExternalLink } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { stJohnAdminApi } from '../services/api'

const StJohnAdmin = () => {
    const [activeSection, setActiveSection] = useState('dashboard') // 'dashboard', 'events', 'services', 'ministries', 'assets'
    const [stats, setStats] = useState(null)
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true)
            try {
                if (activeSection === 'dashboard') {
                    const s = await stJohnAdminApi.getStats()
                    setStats(s)
                } else if (activeSection === 'events') {
                    const e = await stJohnAdminApi.listEvents()
                    setData(e)
                } else if (activeSection === 'services') {
                    const s = await stJohnAdminApi.listServices()
                    setData(s)
                } else if (activeSection === 'ministries') {
                    const m = await stJohnAdminApi.listMinistries()
                    setData(m)
                }
            } catch (err) {
                console.error('Fetch error:', err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [activeSection])

    return (
        <div className="flex bg-[#0a0a0f] min-h-screen text-slate-100 font-sans tracking-tight">
            <Sidebar />
            <main className="flex-1 ml-72 flex h-screen overflow-hidden">
                {/* CMS Sidebar */}
                <div className="w-72 border-r border-white/5 bg-slate-900/20 flex flex-col">
                    <div className="p-8 border-b border-white/5 bg-slate-900/40">
                        <h3 className="text-[10px] font-black uppercase tracking-widest text-indigo-400 mb-1">CMS Control Origin</h3>
                        <p className="text-xl font-black tracking-tighter">ST. JOHN ADMIN</p>
                    </div>
                    <nav className="flex-1 py-6">
                        <CMSNavItem active={activeSection === 'dashboard'} onClick={() => setActiveSection('dashboard')} icon={<LayoutDashboard size={18} />} label="Stats & Health" />
                        <CMSNavItem active={activeSection === 'events'} onClick={() => setActiveSection('events')} icon={<Calendar size={18} />} label="Event Logistics" />
                        <CMSNavItem active={activeSection === 'services'} onClick={() => setActiveSection('services')} icon={<Church size={18} />} label="Worship Flow" />
                        <CMSNavItem active={activeSection === 'ministries'} onClick={() => setActiveSection('ministries')} icon={<Users size={18} />} label="Ministry Hubs" />
                        <CMSNavItem active={activeSection === 'assets'} onClick={() => setActiveSection('assets')} icon={<ImageIcon size={18} />} label="Media Library" />
                    </nav>
                </div>

                {/* Main CMS View */}
                <div className="flex-1 overflow-y-auto bg-slate-950/50">
                    <header className="px-12 py-10 border-b border-white/5 flex justify-between items-center bg-slate-900/40 sticky top-0 z-50">
                         <div>
                            <h2 className="text-2xl font-black tracking-tighter uppercase">{activeSection.replace('_', ' ')}</h2>
                            <p className="text-[10px] opacity-40 font-black uppercase tracking-widest mt-1">Enterprise Content Management</p>
                        </div>
                        <div className="flex gap-4">
                            <button className="glass-panel px-6 py-3 border-white/10 hover:bg-white/5 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                                <Plus size={14} /> New Entry
                            </button>
                        </div>
                    </header>

                    <div className="p-12">
                         <AnimatePresence mode="wait">
                            {activeSection === 'dashboard' && stats && (
                                <motion.div key="dash" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                                    <StatCard label="Active Events" value={stats.events} icon={<Calendar />} color="blue" />
                                    <StatCard label="Worship Services" value={stats.services} icon={<Church />} color="purple" />
                                    <StatCard label="Active Ministries" value={stats.ministries} icon={<Users />} color="emerald" />
                                    <StatCard label="Media Assets" value="248" icon={<ImageIcon />} color="orange" />
                                </motion.div>
                            )}

                            {activeSection !== 'dashboard' && (
                                <motion.div key="list" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                                     {data.map((item, i) => (
                                         <div key={item.id || i} className="p-8 rounded-3xl bg-white/5 border border-white/5 flex justify-between items-center group hover:bg-white/10 transition-all duration-300">
                                             <div>
                                                 <h4 className="text-sm font-bold text-white mb-2">{item.title || item.name}</h4>
                                                 <p className="text-[10px] opacity-40 font-black uppercase tracking-widest">{item.date || item.day} — {item.category || item.time}</p>
                                             </div>
                                             <div className="flex gap-4 opacity-0 group-hover:opacity-100 transition">
                                                 <button className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10"><Edit size={14} /></button>
                                                 <button className="p-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400"><Trash2 size={14} /></button>
                                             </div>
                                         </div>
                                     ))}
                                </motion.div>
                            )}
                         </AnimatePresence>
                    </div>
                </div>
            </main>
        </div>
    )
}

const CMSNavItem = ({ active, onClick, icon, label }) => (
    <button 
        onClick={onClick}
        className={`w-full flex items-center gap-4 px-8 py-5 transition-all relative ${active ? 'text-white' : 'text-slate-400 opacity-60 hover:opacity-100 hover:bg-white/5'}`}
    >
        {active && <motion.div layoutId="activeCMS" className="absolute left-0 w-1 h-8 bg-indigo-500 rounded-r-full" />}
        {icon}
        <span className="text-[11px] font-black uppercase tracking-widest">{label}</span>
    </button>
)

const StatCard = ({ label, value, icon, color }) => (
    <div className="glass-panel p-8 bg-slate-900/40 border-white/5">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${color === 'blue' ? 'text-blue-400 bg-blue-400/10' : color === 'purple' ? 'text-purple-400 bg-purple-400/10' : 'text-emerald-400 bg-emerald-400/10'}`}>
            {icon}
        </div>
        <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-1">{label}</p>
        <p className="text-3xl font-black">{value}</p>
    </div>
)

export default StJohnAdmin
