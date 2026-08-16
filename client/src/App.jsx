import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Navbar from './components/Navbar'
import TradingDashboard from './pages/TradingDashboard'
import NewsDashboard from './pages/NewsDashboard'
import AITerminal from './pages/AITerminal'
import AnalystLab from './pages/AnalystLab'
import AstroIntelligence from './pages/AstroIntelligence'
import RestaurantManager from './pages/RestaurantManager'
import StJohnAdmin from './pages/StJohnAdmin'

function App() {
  return (
    <Router>
      <div className="app-layout" style={{ minHeight: '100vh', background: '#050505' }}>
        <Navbar />
        {/* Main Content Area with padding for the fixed navbar */}
        <div style={{ paddingTop: '80px' }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/trading" element={<TradingDashboard />} />
            <Route path="/news" element={<NewsDashboard />} />
            <Route path="/chat" element={<AITerminal />} />
            <Route path="/analyst" element={<AnalystLab />} />
            <Route path="/astro" element={<AstroIntelligence />} />
            <Route path="/restaurant" element={<RestaurantManager />} />
            <Route path="/stjohn" element={<StJohnAdmin />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App
