import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Newspaper, Calendar, Search, ArrowRight, ExternalLink } from 'lucide-react'
import { newsApi } from '../services/api'

const NewsDashboard = () => {
    const [dates, setDates] = useState([])
    const [selectedDate, setSelectedDate] = useState('')
    const [newsData, setNewsData] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        const fetchDates = async () => {
            try {
                const datesList = await newsApi.getDates()
                setDates(datesList)
                if (datesList.length > 0) {
                    setSelectedDate(datesList[0])
                }
            } catch (err) {
                console.error('Error fetching dates:', err)
            }
        }
        fetchDates()
    }, [])

    useEffect(() => {
        if (selectedDate) {
            const fetchNews = async () => {
                setLoading(true)
                try {
                    const data = await newsApi.getDataByDate(selectedDate)
                    setNewsData(data)
                } catch (err) {
                    console.error('Error fetching news:', err)
                } finally {
                    setLoading(false)
                }
            }
            fetchNews()
        }
    }, [selectedDate])

    return (
        <div className="bg-slate-950 min-h-screen text-slate-100 font-sans tracking-tight">
            <main className="max-w-7xl mx-auto p-12 overflow-y-auto">
                <header className="flex justify-between items-center mb-16 border-b border-white/5 pb-10">
                    <div>
                        <h2 className="text-4xl font-extrabold tracking-tighter title-gradient drop-shadow-sm mb-2">MARKET INTELLIGENCE</h2>
                        <p className="text-sm opacity-50 font-bold uppercase tracking-widest leading-none">Archival Analysis & News Signal</p>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
                    {/* Date Selector */}
                    <aside className="lg:col-span-1">
                        <div className="glass-panel p-8 sticky top-12">
                            <h3 className="text-xs font-black uppercase tracking-widest opacity-40 mb-8 flex items-center gap-3">
                                <Calendar size={14} /> Historical Archives
                            </h3>
                            <div className="flex flex-col gap-2">
                                {dates.map(date => (
                                    <button 
                                        key={date}
                                        onClick={() => setSelectedDate(date)}
                                        className={`
                                            text-left px-5 py-4 rounded-2xl text-xs font-bold transition-all duration-300
                                            ${selectedDate === date ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'bg-white/5 opacity-60 hover:opacity-100 hover:bg-white/10'}
                                        `}
                                    >
                                        {date}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </aside>

                    {/* News Content */}
                    <section className="lg:col-span-3">
                        {loading ? (
                            <div className="flex flex-col items-center justify-center py-40 opacity-20">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-6"></div>
                                <p className="font-bold uppercase tracking-widest text-xs">Parsing Intelligence...</p>
                            </div>
                        ) : newsData ? (
                            <motion.div 
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-10"
                            >
                                <div className="glass-panel p-10 bg-gradient-to-br from-slate-900 to-transparent border border-white/10">
                                    <h3 className="text-3xl font-black mb-4 tracking-tighter">Daily Briefing: {selectedDate}</h3>
                                    <p className="text-sm opacity-60 leading-relaxed font-medium max-w-2xl">
                                        Synthesized market analysis and news aggregation for {selectedDate}. All data is retrieved from local secure archives.
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 gap-6">
                                    {newsData.articles?.map((article, i) => (
                                        <NewsCard key={i} article={article} />
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-40 opacity-20">
                                <Newspaper size={64} className="mb-6" />
                                <p className="font-bold uppercase tracking-widest text-xs">Select a date to view intelligence</p>
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    )
}

const NewsCard = ({ article }) => (
    <div className="glass-panel p-8 group hover:bg-white/10 transition-all duration-500 cursor-pointer border border-white/5 hover:border-white/20">
        <div className="flex justify-between items-start mb-6">
            <span className="px-4 py-1.5 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-black uppercase tracking-widest border border-blue-500/20">
                {article.category || 'General'}
            </span>
            <ExternalLink size={16} className="opacity-0 group-hover:opacity-40 transition" />
        </div>
        <h4 className="text-xl font-bold mb-4 leading-snug group-hover:text-blue-400 transition">{article.title}</h4>
        <p className="text-sm opacity-60 leading-relaxed line-clamp-2 mb-6 font-medium">
            {article.summary || article.description}
        </p>
        <div className="flex items-center gap-4 text-[10px] font-black uppercase tracking-widest opacity-40">
            <span>{article.source}</span>
            <span className="w-1 h-1 rounded-full bg-white/20"></span>
            <span>{article.time}</span>
        </div>
    </div>
)

export default NewsDashboard
