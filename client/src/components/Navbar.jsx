import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BarChart3, Menu, X } from 'lucide-react'
import '../styles/Home.css'

const NAV_LINKS = [
  { label: 'Trading',     to: '/trading' },
  { label: 'Analyst',    to: '/analyst' },
  { label: 'News',       to: '/news' },
  { label: 'AI Chat',    to: '/chat' },
  { label: 'Astro',      to: '/astro' },
  { label: 'Restaurant', to: '/restaurant' },
  { label: 'Portfolio',  to: '/' },
]

const Navbar = () => {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const isActive = (to) =>
    to === '/' ? location.pathname === '/' : location.pathname === to

  return (
    <nav className="main-nav">
      <div className="nav-container">
        <Link to="/" className="nav-logo" style={{ textDecoration: 'none', color: 'white' }}>
          <div className="logo-icon">
            <BarChart3 size={20} className="text-white" />
          </div>
          <span>Fleming Analytic</span>
        </Link>

        {/* Desktop nav */}
        <div className="nav-links">
          {NAV_LINKS.map(({ label, to }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link${isActive(to) ? ' nav-link-active' : ''}`}
            >
              {label}
            </Link>
          ))}
          <button className="btn-start">Start a Project</button>
        </div>

        {/* Mobile hamburger */}
        <button className="nav-hamburger" onClick={() => setMenuOpen(o => !o)}>
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="nav-mobile-menu">
          {NAV_LINKS.map(({ label, to }) => (
            <Link
              key={to}
              to={to}
              className={`nav-mobile-link${isActive(to) ? ' nav-link-active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  )
}

export default Navbar
