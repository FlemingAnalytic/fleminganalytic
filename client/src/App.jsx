import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Navbar from './components/Navbar'

// Home stays eager - it is the landing page and belongs in the initial
// bundle. Every other page is split out and fetched on navigation, which is
// what production has always served: nine per-page chunks plus vendor splits,
// ~197 kB of initial JS. Importing these statically instead pulls all ten
// pages, the chart library and framer-motion into one 830 kB bundle.
const TradingDashboard = lazy(() => import('./pages/TradingDashboard'))
const NewsDashboard = lazy(() => import('./pages/NewsDashboard'))
const AITerminal = lazy(() => import('./pages/AITerminal'))
const AnalystLab = lazy(() => import('./pages/AnalystLab'))
const AstroIntelligence = lazy(() => import('./pages/AstroIntelligence'))
const RestaurantManager = lazy(() => import('./pages/RestaurantManager'))
const StJohnAdmin = lazy(() => import('./pages/StJohnAdmin'))
const Approach = lazy(() => import('./pages/Approach'))
const Contact = lazy(() => import('./pages/Contact'))

function App() {
  return (
    <Router>
      <div className="app-layout" style={{ minHeight: '100vh', background: '#050505' }}>
        <Navbar />
        {/* Main Content Area with padding for the fixed navbar */}
        <div style={{ paddingTop: '80px' }}>
          <Suspense fallback={<div style={{ minHeight: '60vh' }} />}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/trading" element={<TradingDashboard />} />
              <Route path="/news" element={<NewsDashboard />} />
              <Route path="/chat" element={<AITerminal />} />
              <Route path="/analyst" element={<AnalystLab />} />
              <Route path="/astro" element={<AstroIntelligence />} />
              <Route path="/restaurant" element={<RestaurantManager />} />
              <Route path="/stjohn" element={<StJohnAdmin />} />
              <Route path="/approach" element={<Approach />} />
              <Route path="/contact" element={<Contact />} />
            </Routes>
          </Suspense>
        </div>
      </div>
    </Router>
  )
}

export default App
