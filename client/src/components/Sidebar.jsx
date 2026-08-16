import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, Newspaper, MessageSquare, Settings, Share2, FlaskConical, Utensils, Sparkles } from 'lucide-react'

const SidebarItem = ({ to, icon: Icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) => `
      flex items-center gap-4 px-6 py-4 transition-all duration-300
      hover:bg-white/5 hover:translate-x-1 border-l-4 border-transparent
      ${isActive ? 'bg-white/10 border-blue-500 opacity-100 text-white shadow-lg' : 'opacity-60 text-slate-400'}
    `}
  >
    <Icon size={20} />
    <span className="font-semibold tracking-tight uppercase text-xs">{label}</span>
  </NavLink>
)

const Sidebar = () => {
  return (
    <aside className="w-72 h-screen glass-panel fixed left-0 top-0 border-r border-white/5 z-50 overflow-hidden flex flex-col rounded-none">
      <div className="p-8 border-b border-white/5 bg-gradient-to-br from-slate-900/50 to-transparent">
        <h1 className="text-xl font-black title-gradient tracking-tighter">FLEMING ANALYTIC</h1>
        <p className="text-[10px] opacity-40 font-bold uppercase tracking-widest mt-1">Intelligence Terminal</p>
      </div>

      <nav className="flex-1 py-8 flex flex-col">
        <SidebarItem to="/" icon={LayoutDashboard} label="Home" />
        <SidebarItem to="/trading" icon={TrendingUp} label="Trading Radar" />
        <SidebarItem to="/news" icon={Newspaper} label="Market News" />
        <SidebarItem to="/chat" icon={MessageSquare} label="AI Terminal" />
        <SidebarItem to="/analyst" icon={FlaskConical} label="Analyst Lab" />
        <SidebarItem to="/astro" icon={Sparkles} label="Celestial Intel" />
        <SidebarItem to="/restaurant" icon={Utensils} label="Hospitality" />
        <div className="mt-auto pb-8 border-t border-white/5 pt-8">
            <SidebarItem to="/stjohn" icon={Share2} label="CMS Admin" />
            <SidebarItem to="/settings" icon={Settings} label="Settings" />
        </div>
      </nav>

      <div className="p-8 border-t border-white/5 bg-slate-900/40">
        <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-sm shadow-md">SF</div>
            <div>
                <p className="text-xs font-bold text-white">Guest Account</p>
                <p className="text-[10px] opacity-40 uppercase font-black tracking-widest">Enterprise Access</p>
            </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
