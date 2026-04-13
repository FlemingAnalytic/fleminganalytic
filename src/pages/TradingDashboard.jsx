import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, PieChart, Info, DollarSign, Download, Settings } from 'lucide-react'
import { stocksApi } from '../services/api'
import { useTradingPreferences } from '../hooks/useTradingPreferences'

const TradingDashboard = () => {
  const { preferences, updatePreference } = useTradingPreferences()
  
  const [marketStats, setMarketStats] = useState({
    sp500Data: null,
    recommendations: [],
    loading: true
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const sp500 = await stocksApi.getSp500()
        const efToday = await stocksApi.getEfToday()
        
        // Handle pandas orient='table' format if necessary
        const recommendationsList = efToday.data || efToday || []
        
        setMarketStats({
          sp500Data: sp500,
          recommendations: Array.isArray(recommendationsList) ? recommendationsList : [],
          loading: false
        })
      } catch (err) {
        console.error('Failed to fetch market data:', err)
        setMarketStats(prev => ({ ...prev, loading: false }))
      }
    }
    fetchData()
  }, [])

  return (
    <div className="bg-slate-950 min-h-screen text-slate-100 font-sans tracking-tight">
      <main className="max-w-7xl mx-auto p-12 overflow-y-auto">
        <header className="flex justify-between items-center mb-16 border-b border-white/5 pb-10">
          <div>
            <h2 className="text-4xl font-extrabold tracking-tighter title-gradient drop-shadow-sm mb-2">MODERN TRADING RADAR</h2>
            <p className="text-sm opacity-50 font-bold uppercase tracking-widest leading-none">Intelligence. Strategy. Alpha.</p>
          </div>
          <div className="flex gap-4 items-center">
            <button className="flex items-center gap-2 glass-panel px-6 py-3 text-xs font-bold uppercase tracking-widest hover:bg-white/10 transition shadow-inner">
                <Download size={16} /> Export Strategy
            </button>
            <button className="button-primary flex items-center gap-2 shadow-2xl px-8 py-3.5 text-xs font-black uppercase tracking-widest transform hover:scale-105 transition-all duration-300">
                Execute Radar Search
            </button>
          </div>
        </header>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-10 mb-20">
            <StatsCard title="S&P 500 Performance" value="+12.4%" delta="+2.1% Today" icon={<TrendingUp size={24} color="#3b82f6" />} color="blue" />
            <StatsCard title="Optimal Sharpe Ratio" value="1.82" delta="Historical Alpha" icon={<PieChart size={24} color="#8b5cf6" />} color="purple" />
            <StatsCard title="Total Exposure" value="$84.2K" delta="Strategic Reserve" icon={<DollarSign size={24} color="#10b981" />} color="green" />
        </section>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-12">
            <motion.div 
              className="glass-panel p-10 border border-white/10 shadow-2xl bg-gradient-to-br from-slate-900/60 to-transparent flex flex-col h-full"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
                <div className="flex justify-between items-center mb-10 pb-6 border-b border-white/5">
                    <h3 className="text-2xl font-black tracking-tight flex items-center gap-4">
                        <Settings size={24} className="opacity-50" /> Personal Strategy Assumptions
                    </h3>
                    <div className="px-4 py-1 rounded-full bg-blue-500/10 text-[10px] font-black uppercase tracking-widest text-blue-400 border border-blue-500/20">Local Storage Active</div>
                </div>
                
                <div className="space-y-10 flex-1">
                    <div>
                        <label className="block text-[11px] font-black uppercase tracking-widest opacity-40 mb-4 ml-1">Current Active Tickers & Allocation</label>
                        <textarea 
                            value={preferences.tickers}
                            onChange={(e) => updatePreference('tickers', e.target.value)}
                            className="w-full h-32 bg-slate-900/50 border border-white/10 rounded-2xl p-6 text-sm font-medium focus:ring-2 focus:ring-blue-500 transition outline-none resize-none font-mono"
                        ></textarea>
                    </div>

                    <div className="p-8 rounded-3xl bg-blue-500/5 border border-blue-500/10 flex items-start gap-5">
                       <Info size={24} className="text-blue-500 mt-1 flex-shrink-0" />
                       <p className="text-xs font-semibold opacity-70 leading-relaxed text-blue-100">Your personal strategy parameters no longer reside on the server, ensuring your financial assumptions remain private to your local browser session.</p>
                    </div>
                </div>

                <div className="mt-auto pt-10">
                    <button className="w-full p-5 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 font-extrabold text-sm uppercase tracking-widest hover:shadow-2xl hover:shadow-blue-500/20 transition-all duration-300">Synchronize Model</button>
                </div>
            </motion.div>

            <motion.div 
              className="flex flex-col gap-8 h-full"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
                <div className="glass-panel p-10 border border-white/10 bg-slate-900/40 flex-1 relative overflow-hidden group">
                    <h3 className="text-2xl font-black mb-10 pb-6 border-b border-white/5">Alpha Recommendations</h3>
                    <div className="space-y-6">
                        {marketStats.recommendations.length > 0 ? (
                            marketStats.recommendations.slice(0, 5).map((rec, i) => (
                                <RecommendationRow 
                                  key={i} 
                                  ticker={rec.Ticker || 'N/A'} 
                                  score={rec.Weight || 'N/A'} 
                                  change={rec.pe ? `PE: ${rec.pe}` : '+0.0%'} 
                                />
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center py-20 opacity-30">
                                <TrendingUp size={64} className="mb-4" />
                                <p className="font-extrabold text-xs uppercase tracking-widest">No Active Radar Feeds</p>
                            </div>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
      </main>
    </div>
  )
}

const StatsCard = ({ title, value, delta, icon, color }) => (
  <div className={`glass-panel p-10 border-l-8 ${color === 'blue' ? 'border-blue-500/30' : color === 'purple' ? 'border-purple-500/30' : 'border-emerald-500/30'} bg-slate-900/40 transform hover:-translate-y-1 transition-all duration-300`}>
    <div className="flex justify-between items-start mb-8">
      <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center shadow-lg border border-white/5">{icon}</div>
      <span className={`text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full ${color === 'blue' ? 'bg-blue-500/10 text-blue-400' : color === 'purple' ? 'bg-purple-500/10 text-purple-400' : 'bg-emerald-500/10 text-emerald-400'}`}>Live</span>
    </div>
    <p className="text-[10px] font-black uppercase tracking-widest opacity-40 mb-2">{title}</p>
    <h4 className="text-4xl font-extrabold mb-1 tracking-tighter">{value}</h4>
    <p className={`text-[10px] font-black uppercase tracking-widest ${delta.includes('+') ? 'text-emerald-400' : 'text-blue-400'}`}>{delta}</p>
  </div>
)

const RecommendationRow = ({ ticker, score, change }) => (
  <div className="flex items-center justify-between p-6 rounded-3xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-300 cursor-pointer">
    <div className="flex items-center gap-6">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center font-black text-blue-400">{ticker[0]}</div>
      <div>
        <p className="text-lg font-extrabold tracking-tighter">{ticker}</p>
        <p className="text-[9px] font-black uppercase tracking-widest opacity-40">Proprietary Signal</p>
      </div>
    </div>
    <div className="text-right">
        <span className="text-sm font-black title-gradient">{score}</span>
    </div>
  </div>
)

export default TradingDashboard
