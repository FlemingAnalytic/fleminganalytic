import React from 'react'
import { motion } from 'framer-motion'
import { Activity, BarChart2, PieChart, Info, AlertCircle, TrendingUp, Grid } from 'lucide-react'
import { useDataProfileViewModel } from '../../viewmodels/dataProfileViewModel'

const DataProfile = ({ profile }) => {
    const { 
        stats, 
        categorizedColumns, 
        insights, 
        correlationMatrix 
    } = useDataProfileViewModel(profile);

    if (!profile) return null

    return (
        <div className="space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-1000">
            {/* Header / Shapes */}
            <div className="flex gap-8 border-b border-white/5 pb-15 mb-15">
                <Stat icon={<Grid size={24} />} label="Total Records" value={stats.rows.toLocaleString()} color="blue" />
                <Stat icon={<Activity size={24} />} label="Data Features" value={stats.cols.toLocaleString()} color="purple" />
                <Stat icon={<AlertCircle size={24} />} label="Data Quality" value="High" color="emerald" />
            </div>

            {/* Smart Insights */}
            <div>
                <h3 className="text-sm font-black uppercase tracking-widest opacity-40 mb-10 flex items-center gap-4">
                    <Activity size={16} /> Intelligent Signal Observations
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
                    {insights.map((insight, i) => (
                        <InsightCard key={i} insight={insight} index={i} />
                    ))}
                </div>
            </div>

            {/* Feature Analysis */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-12">
                <div>
                     <h3 className="text-sm font-black uppercase tracking-widest opacity-40 mb-10 flex items-center gap-4">
                        <BarChart2 size={16} /> Continuous Distributions
                    </h3>
                    <div className="space-y-4">
                        {categorizedColumns.measures.slice(0, 6).map((meta) => (
                            <ColumnRow key={meta.name} name={meta.name} meta={meta} />
                        ))}
                    </div>
                </div>

                <div>
                    <h3 className="text-sm font-black uppercase tracking-widest opacity-40 mb-10 flex items-center gap-4">
                        <TrendingUp size={16} /> Global Correlations
                    </h3>
                    <div className="space-y-6">
                        {correlationMatrix?.strong_pairs?.length > 0 ? (
                           correlationMatrix.strong_pairs.map((pair, i) => (
                               <CorrelationRow key={i} pair={pair} />
                           ))
                        ) : (
                            <div className="p-10 rounded-3xl bg-white/5 opacity-40 italic text-xs text-center border border-white/5">No significant linear correlations detected within continuous features.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

const Stat = ({ icon, label, value, color }) => (
    <div className={`p-8 rounded-3xl border border-white/5 flex items-center gap-8 ${color === 'blue' ? 'bg-blue-600/5' : color === 'purple' ? 'bg-purple-600/5' : 'bg-emerald-600/5'}`}>
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${color === 'blue' ? 'text-blue-400 bg-blue-400/10' : color === 'purple' ? 'text-purple-400 bg-purple-400/10' : 'text-emerald-400 bg-emerald-400/10'}`}>{icon}</div>
        <div>
            <p className="text-[10px] font-black uppercase tracking-widest opacity-40 leading-none mb-2">{label}</p>
            <p className="text-3xl font-black leading-none">{value}</p>
        </div>
    </div>
)

const InsightCard = ({ insight, index }) => (
    <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className="glass-panel p-8 group border-white/10 hover:border-blue-500/30 transition-all duration-500 shadow-xl"
    >
        <div className={`w-12 h-12 rounded-xl mb-8 flex items-center justify-center font-black text-xs ${insight.type === 'overview' ? 'text-blue-400 bg-blue-400/10' : insight.type === 'correlation' ? 'text-purple-400 bg-purple-400/10' : 'text-emerald-400 bg-emerald-400/10'}`}>
            {insight.type[0].toUpperCase()}
        </div>
        <h4 className="text-lg font-extrabold tracking-tight mb-3 group-hover:text-blue-400 transition">{insight.title}</h4>
        <p className="text-sm opacity-50 font-medium leading-relaxed">{insight.detail}</p>
    </motion.div>
)

const ColumnRow = ({ name, meta }) => (
    <div className="p-6 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all duration-300">
        <div className="flex justify-between items-center mb-4">
            <span className="text-xs font-black uppercase tracking-widest text-white/80">{name}</span>
            <span className="text-[10px] font-black opacity-40 uppercase tracking-widest">Avg: {meta.stats?.mean || 'N/A'}</span>
        </div>
        <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
             <div className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full w-[70%]" />
        </div>
        <div className="flex justify-between mt-3 text-[9px] font-black uppercase tracking-widest opacity-30">
            <span>Range: {meta.stats?.min} — {meta.stats?.max}</span>
            <span>Uniqueness: {meta.unique_pct}%</span>
        </div>
    </div>
)

const CorrelationRow = ({ pair }) => (
    <div className="flex items-center justify-between p-6 rounded-3xl bg-white/5 border border-white/5 transform hover:scale-[1.02] transition shadow-md">
        <div className="flex items-center gap-6">
            <div className={`p-4 rounded-xl text-blue-400 font-black text-sm ${pair.strength === 'strong' ? 'bg-blue-400/20 shadow-blue-400/10 shadow-lg' : 'bg-blue-400/5 opacity-60'}`}>{pair.correlation}</div>
            <div>
                <p className="text-sm font-extrabold tracking-tighter text-white">{pair.col1} <span className="opacity-30 mx-2">&</span> {pair.col2}</p>
                <p className="text-[10px] font-black uppercase tracking-widest opacity-30">{pair.strength} Correlation Strength</p>
            </div>
        </div>
    </div>
)

export default DataProfile
