import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Coffee, MapPin, Phone, Info, Plus, Trash2, Edit3, Save, Search, ChevronRight, LayoutList } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { restaurantApi } from '../services/api'

const RestaurantManager = () => {
    const [restaurants, setRestaurants] = useState([])
    const [selected, setSelected] = useState(null)
    const [loading, setLoading] = useState(true)
    const [isEditing, setIsEditing] = useState(false)

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const data = await restaurantApi.list()
                setRestaurants(data)
                if (data.length > 0) setSelected(data[0])
            } catch (err) {
                console.error('Restaurant fetch error:', err)
            } finally {
                setLoading(false)
            }
        }
        fetchAll()
    }, [])

    const handleSave = async () => {
        try {
            await restaurantApi.update(selected.id, selected)
            setIsEditing(false)
            // Refresh list
            const data = await restaurantApi.list()
            setRestaurants(data)
        } catch (err) {
            console.error('Save error:', err)
        }
    }

    const addNewRestaurant = async () => {
        try {
            const name = prompt("Enter Restaurant Name:")
            if (!name) return
            const result = await restaurantApi.create({ name })
            setRestaurants([...restaurants, result])
            setSelected(result)
        } catch (err) {
             console.error('Create error:', err)
        }
    }

    return (
        <div className="flex bg-slate-950 min-h-screen text-slate-100 font-sans tracking-tight">
            <Sidebar />
            <main className="flex-1 ml-72 flex h-screen overflow-hidden">
                {/* List Pane */}
                <div className="w-80 border-r border-white/5 bg-slate-900/40 flex flex-col">
                    <div className="p-8 border-b border-white/5">
                        <h3 className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-6 flex items-center gap-2">
                           <LayoutList size={12} /> Managed Portfolios
                        </h3>
                        <button 
                            onClick={addNewRestaurant}
                            className="w-full p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center justify-center gap-3 text-[10px] font-black uppercase tracking-widest"
                        >
                            <Plus size={14} /> Register Entity
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-2">
                        {restaurants.map(r => (
                            <button 
                                key={r.id}
                                onClick={() => { setSelected(r); setIsEditing(false); }}
                                className={`w-full text-left p-5 rounded-2xl transition-all duration-300 flex justify-between items-center group ${selected?.id === r.id ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/10' : 'hover:bg-white/5 opacity-60 hover:opacity-100'}`}
                            >
                                <span className="text-xs font-bold truncate pr-4">{r.name}</span>
                                <ChevronRight size={14} className={`${selected?.id === r.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-40'} transition`} />
                            </button>
                        ))}
                    </div>
                </div>

                {/* Detail Pane */}
                <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-950 to-slate-900/50">
                    <header className="px-12 py-10 border-b border-white/5 flex justify-between items-center bg-slate-900/40 sticky top-0 z-50">
                        <div>
                            <h2 className="text-3xl font-black tracking-tighter title-gradient flex items-center gap-4">
                                <Coffee size={24} className="opacity-50" /> HOSPITALITY MANAGER
                            </h2>
                            <p className="text-[10px] opacity-40 font-black uppercase tracking-widest leading-none mt-1">Enterprise Operational Terminal</p>
                        </div>
                        {selected && (
                            <div className="flex gap-4">
                                {isEditing ? (
                                    <button onClick={handleSave} className="button-primary px-8 py-3.5 text-[10px] font-black uppercase tracking-widest flex items-center gap-3"><Save size={16} /> Deploy Changes</button>
                                ) : (
                                    <button onClick={() => setIsEditing(true)} className="glass-panel px-8 py-3.5 border-white/10 hover:bg-white/5 text-[10px] font-black uppercase tracking-widest flex items-center gap-3"><Edit3 size={16} /> Modify Profile</button>
                                )}
                            </div>
                        )}
                    </header>

                    <div className="p-16 max-w-5xl">
                        <AnimatePresence mode="wait">
                            {!selected ? (
                                <div className="h-full flex flex-col items-center justify-center opacity-10 gap-8 py-40">
                                    <Coffee size={80} className="stroke-[0.5px]" />
                                    <p className="font-black text-sm uppercase tracking-widest">Select an entity to manage profile and assets</p>
                                </div>
                            ) : (
                                <motion.div 
                                    key={selected.id}
                                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                    className="space-y-16"
                                >
                                    {/* Profile Data */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                        <DetailGroup label="Official Designation" value={selected.name} isEditing={isEditing} onChange={(v) => setSelected({...selected, name: v})} />
                                        <DetailGroup label="Contact Direct" value={selected.phone} isEditing={isEditing} onChange={(v) => setSelected({...selected, phone: v})} />
                                        <DetailGroup label="Operational Status" value={selected.status} isEditing={isEditing} onChange={(v) => setSelected({...selected, status: v})} />
                                        <DetailGroup label="Physical Address" value={selected.address} isEditing={isEditing} onChange={(v) => setSelected({...selected, address: v})} />
                                    </div>

                                    {/* Menu Section */}
                                    <div className="pt-10 border-t border-white/5">
                                        <h3 className="text-sm font-black uppercase tracking-widest opacity-40 mb-10 border-b border-white/5 pb-6 flex justify-between items-center">
                                            Asset Inventory (Menu)
                                            <button className="text-[10px] px-3 py-1 rounded bg-white/5 hover:bg-white/10 transition">+ Add Item</button>
                                        </h3>
                                        <div className="grid grid-cols-1 gap-4">
                                            {selected.menu?.length > 0 ? (
                                                selected.menu.map((item, i) => (
                                                    <div key={i} className="p-8 rounded-3xl bg-white/5 border border-white/5 flex justify-between items-center group">
                                                        <div>
                                                            <p className="text-sm font-bold text-white mb-1">{item.name}</p>
                                                            <p className="text-[10px] opacity-40 font-black uppercase tracking-widest">{item.category} — ${item.price}</p>
                                                        </div>
                                                        <Trash2 size={16} className="opacity-0 group-hover:opacity-40 text-red-400 hover:opacity-100 transition cursor-pointer" />
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="p-20 text-center opacity-20 italic text-xs border-2 border-dashed border-white/5 rounded-3xl">No menu inventory detected.</div>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </main>
        </div>
    )
}

const DetailGroup = ({ label, value, isEditing, onChange }) => (
    <div className="space-y-4">
        <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1">{label}</label>
        {isEditing ? (
            <input 
                value={value || ''} 
                onChange={(e) => onChange(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-sm font-bold outline-none focus:ring-2 focus:ring-blue-500/30 transition"
            />
        ) : (
            <div className="p-6 rounded-2xl bg-white/5 border border-transparent font-extrabold text-sm">{value || 'N/A'}</div>
        )}
    </div>
)

export default RestaurantManager
