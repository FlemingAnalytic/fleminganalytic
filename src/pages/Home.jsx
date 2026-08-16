import React from 'react'
import { Link } from 'react-router-dom'
import {
    Code,
    Database,
    Smartphone,
    Truck,
    BarChart3,
    Building2,
    ArrowRight,
    Github,
    Twitter,
    Linkedin,
    ExternalLink,
    ChevronRight,
    Cpu,
    Globe,
    Layers,
    Zap,
    LayoutGrid,
    List,
    Maximize2,
} from 'lucide-react'
import { useDashboardViewModel } from '../viewmodels/dashboardViewModel'
import '../styles/Home.css'

const PORTFOLIO_EXTERNAL = [
  { category: "Healthcare",       title: "DentalEDR.net",           desc: "Full dental practice management system. Patient records, scheduling, treatment plans, and billing integration.",                      href: "https://dentaledr.net",            isExternal: true, bg: "#dbeafe", color: "#2563eb" },
  { category: "Business Tools",   title: "Jobberhub",               desc: "Comprehensive administrative platform for job management and workflow. Includes user manuals for seamless adoption.",                  href: "https://jobberhub.net",            isExternal: true, bg: "#eff6ff", color: "#3b82f6" },
  { category: "Education",        title: "CodeQuest Academy",       desc: "Learning platform for computer science fundamentals. Interactive lessons, coding exercises, and progress tracking for students.",     href: "https://codequestacademy.net",     isExternal: true, bg: "#fef3c7", color: "#d97706" },
  { category: "Education / STEM", title: "STEM for 8th Graders",    desc: "STEM resources and interactive activities aimed at 8th-grade students. Curriculum-aligned content for science, tech, and math.",     href: "https://for8thgraders.top",        isExternal: true, bg: "#ecfdf5", color: "#10b981" },
  { category: "Ticketing",        title: "StubMe.net",                desc: "Honest-pricing ticketing platform for venues. True-to-scale seat picker, per-event fees from the venue payout, sales tax broken out at every step, real scannable QR tickets.", href: "https://stubme.net",            isExternal: true, bg: "#fff7ed", color: "#d94f3a" },
]

const PORTFOLIO_INTERNAL = [
  { category: "Research / White Paper", title: "Unsupervised ML White Paper", desc: "How unsupervised machine learning extracts structure, outliers, and hidden signal from large unfamiliar datasets. Full case study across 20M SEC ABS-EE filings with four interactive reports.", href: "/whitepaper/", isExternal: true, bg: "#f4f1ff", color: "#7c5cff" },
  { category: "Space / Simulation", title: "Mars Exploration", desc: "Interactive Mars mission control — live operator API, telemetry, and mission media from a simulated Mars exploration program.", href: "/mars/", isExternal: true, bg: "#fff1f0", color: "#dc2626" },
  { category: "Data Analytics",   title: "Smart Analyst",        desc: "Upload datasets, run ML models, generate visualizations. Demonstrates file handling, data processing, and dynamic charting.",        to: "/analyst",     bg: "#f3e8ff", color: "#9333ea" },
  { category: "Finance",          title: "Stock Market Tools",   desc: "Real-time trading signal scans, Efficient Frontier modeling, and momentum tracking for S&P 500.",                                   to: "/trading",     bg: "#d1fae5", color: "#059669" },
  { category: "News & Data",      title: "News Analytics",       desc: "Automated news aggregation with historical archives. Scheduled tasks, JSON storage, and search functionality.",                      to: "/news",        bg: "#e0f2fe", color: "#0284c7" },
  { category: "AI Chat",          title: "AI Terminal",          desc: "Local LLM chat interface powered by Ollama. Query models, explore app code explanations, and test prompt engineering.",              to: "/chat",        bg: "#fef3c7", color: "#d97706" },
  { category: "Retail/POS",       title: "Restaurant Platform",  desc: "Menu management, order processing, and email notifications. Shows e-commerce patterns and workflow automation.",                     to: "/restaurant",  bg: "#ffe4e6", color: "#e11d48" },
  { category: "PDF Generation",   title: "Astrology Charts",     desc: "Birth chart generation with PDF export. Complex ephemeris calculations, SVG rendering, and document generation.",                    to: "/astro",       bg: "#fdf4ff", color: "#a855f7" },
  { category: "Government Data",  title: "Economic Indicators",  desc: "Federal Reserve data visualization. GDP, debt metrics, and time-series analysis from FRED API.",                                    href: "https://fleminganalytic.com/fred/gdp",           isExternal: true, bg: "#f0fdf4", color: "#16a34a" },
  { category: "Interactive App",  title: "Chess Game",           desc: "AI opponent with difficulty levels. Demonstrates game state management, move validation, and API-driven AI.",                       href: "https://fleminganalytic.com/chess/",             isExternal: true, bg: "#f1f5f9", color: "#475569" },
  { category: "SEC Filings",      title: "13F-HR Institutional Positioning", desc: "Quarterly analysis of institutional holdings. Manager rankings, crowding momentum, position rotation, and style clusters from SEC EDGAR 13F-HR filings.", href: "/13f/", isExternal: true, bg: "#e3f2fd", color: "#1565c0" },
  { category: "Finance",          title: "TreeView Accounting",    desc: "Double-entry bookkeeping system with hierarchical account visualization, journal entries, and real-time balance validation.",      href: "https://fleminganalytic.com/tvaa/",                   isExternal: true, bg: "#f5f3ff", color: "#7c3aed" },
  { category: "Government/Safety",title: "Nuclear AI Readiness",   desc: "Strategic assessment tool for nuclear facilities. Scores readiness across safety, infrastructure, and operational domains.",       href: "https://fleminganalytic.com/nuclear/",                isExternal: true, bg: "#fefce8", color: "#ca8a04" },
  { category: "Energy",           title: "Energy Forecast",        desc: "Predictive modeling for long-term energy consumption and cost trends. Statistical regression with scenario analysis.",              href: "https://fleminganalytic.com/energy/",                 isExternal: true, bg: "#ecfdf5", color: "#10b981" },
  { category: "Healthcare",       title: "ICU Monitoring System",  desc: "High-fidelity critical care dashboard simulation. Real-time vitals, alerts, and patient management workflow.",                    href: "https://fleminganalytic.com/intensive/",              isExternal: true, bg: "#fef2f2", color: "#dc2626" },
  { category: "Data Viz",         title: "S&P 500 Dashboard",      desc: "Equity market analysis and momentum tracking engine. Historical price data with interactive chart exploration.",                    href: "https://fleminganalytic.com/examples/sp500",          isExternal: true, bg: "#f0fdf4", color: "#22c55e" },
  { category: "Real-time Data",   title: "Weather Map",            desc: "Interactive Leaflet-based weather observation system. Live station data plotted on a zoomable map.",                               href: "https://fleminganalytic.com/examples/weather",        isExternal: true, bg: "#e0f2fe", color: "#0ea5e9" },
  { category: "Tools",            title: "Database Designer",      desc: "Visual schema design tool for relational databases. Drag-and-drop table builder with relationship mapping.",                       href: "https://fleminganalytic.com/examples/dbdesign",       isExternal: true, bg: "#fdf4ff", color: "#d946ef" },
  { category: "Content Management",title:"Church CMS",              desc: "Drag-and-drop bulletin and page builder for parishes. Client-side content management with localStorage persistence — no server required.", href: "https://fleminganalytic.com/church-cms/",             isExternal: true, bg: "#fff7ed", color: "#ea580c" },
]

const Home = () => {
  const { cardLayout, toggleLayout } = useDashboardViewModel();

  return (
    <div className="home-wrapper">
      {/* Hero Section */}
      <header className="hero-section">
        <div className="hero-gradient"></div>
        <div className="hero-container">
            <div className="hero-content animate-in">
                <h1 className="hero-title">
                    AI writes the first draft.
                    <span className="title-accent">Somebody still has to read it.</span>
                </h1>
                <p className="hero-desc">
                    AI didn't remove the work — it moved it. The hours you used to spend producing
                    a draft are the hours you now spend deciding whether it's true. We do both
                    halves: drafted at AI speed, then read line by line by a person who answers
                    for it.
                </p>
                <div className="hero-actions">
                    <Link to="/approach" className="btn-primary">
                       How we work <ArrowRight size={18} />
                    </Link>
                    <Link to="/contact" state={{ from: '/' }} className="btn-secondary">
                        Tell us what's slow
                    </Link>
                </div>
            </div>
        </div>
      </header>

      {/* Proof. Deliberately before the services pitch: the reason to keep
          reading is that the work exists and can be opened, not that we can
          list the things we do. Every figure here was checked against the
          thing it describes — 19 applications answer on this domain, 5 more
          run on client and partner domains, and the manual screenshots are
          captures of the running software. */}
      <section className="section-padding" style={{ paddingTop: '3rem', paddingBottom: '3rem' }}>
        <div className="section-header animate-in">
            <span className="section-tag">Before you spend a dollar</span>
            <h2 className="section-title">Press the buttons yourself</h2>
            <p className="section-desc">
                Nineteen working applications are on this site and you can open every one of
                them without talking to anybody — a parish running its own bulletin, a
                restaurant platform, an ICU dashboard, a ticketing site where fans pay what
                the venue set and nothing else. Five more run on client and partner domains.
                Each admin system ships with a manual whose screenshots come out of the
                running software, so when the software changes the manual is re-run rather
                than rewritten.
            </p>
            <p className="section-desc" style={{ marginTop: '1rem' }}>
                Some of it was drafted by AI. That is rather the point — and every line of it
                was read by someone who had to answer for it.{' '}
                <Link to="/approach" style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: 600 }}>
                    How we work →
                </Link>
            </p>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="section-padding">
        <div className="section-header animate-in">
            <span className="section-tag">What We Do</span>
            <h2 className="section-title">End-to-End Development Services</h2>
            <p className="section-desc">
                We specialize in building the complete data pipeline: from server-side APIs 
                that process data to web and mobile interfaces that present it.
            </p>
        </div>

        <div className="grid-container animate-in">
            <ServiceCard 
                icon={<Code />} 
                title="RESTful API Development" 
                desc="Custom server endpoints that deliver JSON data to any client. Built on Python/FastAPI for performance."
                features={['JSON data generation', 'Authentication & security', 'Third-party integrations']}
                color="#4f46e5"
            />
            <ServiceCard 
                icon={<Database />} 
                title="Database Design" 
                desc="Schema design, optimization, and data modeling for PostgreSQL, MySQL, and NoSQL databases."
                features={['Relational modeling', 'Query optimization', 'Data migration']}
                color="#3b82f6"
            />
            <ServiceCard 
                icon={<Smartphone />} 
                title="Web & Mobile Interfaces" 
                desc="Responsive HTML/JS frontends that consume your APIs and render data for any device."
                features={['Single-page applications', 'Mobile-responsive design', 'Real-time data updates']}
                color="#8b5cf6"
            />
            <ServiceCard 
                icon={<Truck />} 
                title="Supply Chain Interfaces" 
                desc="Connect your systems with vendors, inventory management, and logistics platforms."
                features={['EDI/API integrations', 'Inventory tracking', 'Order management']}
                color="#d97706"
            />
            <ServiceCard 
                icon={<BarChart3 />} 
                title="Data Analytics & ML" 
                desc="Transform raw data into insights with custom analytics dashboards and machine learning."
                features={['Custom dashboards', 'Predictive models', 'Automated reporting']}
                color="#10b981"
            />
            <ServiceCard 
                icon={<Building2 />} 
                title="Vertical Market Solutions" 
                desc="Industry-specific applications for healthcare, finance, retail, and professional services."
                features={['Healthcare systems', 'Financial platforms', 'Restaurant/retail POS']}
                color="#e11d48"
            />
        </div>
      </section>

      {/* Technology Hub & AI Banner */}
      <section id="technology" className="section-padding" style={{ background: '#f8fafc' }}>
        <div className="section-header animate-in">
            <span className="section-tag">Our Stack</span>
            <h2 className="section-title">Modern Technology Platform</h2>
            <p className="section-desc">
                Our primary stack centers on Linux-based Python servers delivering JSON to responsive web interfaces. 
                We adapt to your existing infrastructure and requirements.
            </p>
        </div>

        <div className="grid-container animate-in" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            <StackCard icon={<Cpu />} category="Backend" items={['Python', 'FastAPI', 'Postgres', 'Redis']} />
            <StackCard icon={<Globe />} category="Frontend" items={['React', 'Vite', 'Tailwind CSS', 'Vue.js']} />
            <StackCard icon={<Layers />} category="Infrastructure" items={['Linux', 'Docker', 'AWS', 'DigitalOcean']} />
            <StackCard icon={<Zap />} category="AI & ML" items={['scikit-learn', 'Pandas', 'Claude API', 'OpenAI']} />
        </div>

        {/* AI Integration Banner */}
        <div className="footer-container animate-in">
            <div className="ai-banner">
                <div className="ai-bg-icon">
                    <Zap size={240} />
                </div>
                <div className="ai-content">
                    <h3 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.2)', borderRadius: '16px' }}><Zap size={24} /></div>
                        Powered by State-of-the-Art AI
                    </h3>
                    <p style={{ opacity: 0.9, fontSize: '1.125rem', marginBottom: '2.5rem' }}>
                        We integrate the latest AI technologies into both our development workflow and your applications. 
                        From AI-assisted coding to intelligent search features, AI amplifies what we can deliver.
                    </p>
                    <div className="ai-grid">
                        <div>
                            <p className="ai-stat-label">Development</p>
                            <p className="ai-stat-val">Claude & GPT-4o expert generation</p>
                        </div>
                        <div>
                            <p className="ai-stat-label">Intelligence</p>
                            <p className="ai-stat-val">Natural language backend logic</p>
                        </div>
                        <div>
                            <p className="ai-stat-label">Analytics</p>
                            <p className="ai-stat-val">Predictive modeling pipelines</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </section>

      {/* Portfolio Section */}
      <section id="portfolio" className="section-padding">
        <div className="section-header animate-in">
            <div className="flex justify-between items-end mb-8">
                <div>
                  <span className="section-tag">Interactive Portfolio</span>
                  <h2 className="section-title">Internal Applications</h2>
                  <p className="section-desc max-w-2xl">
                      Working demonstrations of our capabilities across different industries and use cases. Each showcases client-server architecture with responsive frontends.
                  </p>
                </div>
                <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 shadow-sm transition-all hover:shadow-md">
                    <button
                      onClick={toggleLayout}
                      className="p-2.5 hover:bg-white rounded-xl transition-all duration-300 flex items-center gap-3 group border border-transparent hover:border-slate-100"
                      title="Toggle Formatting"
                    >
                      {cardLayout === 'grid' && <LayoutGrid size={18} className="text-blue-600" />}
                      {cardLayout === 'list' && <List size={18} className="text-purple-600" />}
                      {cardLayout === 'compact' && <Maximize2 size={18} className="text-emerald-600" />}
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:text-slate-600">View</span>
                    </button>
                </div>
            </div>
        </div>

        <div className={`grid-container animate-in layout-${cardLayout}`}>
            {PORTFOLIO_INTERNAL.map((item) => (
                <ProjectCard key={item.title} {...item} />
            ))}
        </div>

        {/* External Applications */}
        <div className="section-header animate-in" style={{ marginTop: '4rem' }}>
            <span className="section-tag">Partner & Client Sites</span>
            <h2 className="section-title">External Applications</h2>
            <p className="section-desc max-w-2xl">
                Applications hosted on partner and client domains outside of fleminganalytic.com.
            </p>
        </div>

        <div className={`grid-container animate-in layout-${cardLayout}`}>
            {PORTFOLIO_EXTERNAL.map((item) => (
                <ProjectCard key={item.title} {...item} />
            ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="main-footer">
        <div className="footer-container">
            <div className="footer-main animate-in">
                <div className="footer-cta">
                    <h3>Bring us the job you can't afford to get wrong</h3>
                    <p style={{ color: '#94a3b8', fontSize: '1.15rem', marginBottom: '3rem', opacity: 0.75 }}>
                        The job that eats a day a week. The report nobody trusts. One conversation,
                        no charge, and a straight answer about whether this is worth doing.
                    </p>
                    <Link to="/contact" state={{ from: '/' }} className="btn-primary" style={{ padding: '1.5rem 3rem' }}>
                        Tell us what's slow
                    </Link>
                </div>
                
                <div className="footer-links">
                    <FooterCol title="Start here" items={[
                        { label: 'How we work', to: '/approach' },
                        { label: "Tell us what's slow", to: '/contact' },
                    ]} />
                    <FooterCol title="See the work" items={[
                        { label: 'Smart Analyst', to: '/analyst' },
                        { label: 'Trading Radar', to: '/trading' },
                        { label: 'Restaurant POS', to: '/restaurant' },
                        { label: 'Astro Engine', to: '/astro' },
                    ]} />
                    <FooterCol title="Read" items={[
                        { label: 'Unsupervised ML white paper', href: '/whitepaper/' },
                        { label: 'Mars mission control', href: '/mars/' },
                        { label: 'Data centres explainer', href: '/datacenters/' },
                    ]} />
                </div>
            </div>

            <div className="footer-bottom">
                <div className="footer-copy">
                    <div style={{ width: '32px', height: '32px', background: '#4f46e5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifySelf: 'center', fontWeight: 900, fontSize: '0.75rem', justifyContent: 'center' }}>F</div>
                    <span>© 2026 Fleming Analytic. Built with High Fidelity.</span>
                </div>
                <div className="social-links">
                    {/* Add href="https://..." when the account exists. Until then
                        these render nothing rather than linking to "#". */}
                    <SocialLink icon={<Linkedin size={20} />} />
                    <SocialLink icon={<Github size={20} />} />
                </div>
            </div>
        </div>
      </footer>
    </div>
  )
}

const ServiceCard = ({ icon, title, desc, features, color }) => (
    <div className="service-card">
        <div className="service-icon" style={{ color: color }}>
            {React.cloneElement(icon, { size: 32 })}
        </div>
        <h3 className="card-title">{title}</h3>
        <p className="card-desc">{desc}</p>
        <div className="feature-list">
            {features.map(f => (
                <div key={f} className="feature-item">
                    <div className="feature-dot" /> {f}
                </div>
            ))}
        </div>
    </div>
)

const StackCard = ({ icon, category, items }) => (
    <div style={{ padding: '2.5rem', background: 'white', border: '1px solid #e2e8f0', borderRadius: '32px' }}>
        <div style={{ color: '#4f46e5', marginBottom: '1.5rem', background: '#f5f3ff', width: '48px', height: '48px', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{React.cloneElement(icon, { size: 20 })}</div>
        <h4 style={{ fontSize: '0.625rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.2em', color: '#94a3b8', marginBottom: '1.25rem' }}>{category}</h4>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {items.map(item => (
                <li key={item} style={{ fontSize: '0.875rem', fontWeight: 700, color: '#334155' }}>{item}</li>
            ))}
        </ul>
    </div>
)

const ProjectCard = ({ category, title, desc, to, href, isExternal, bg, color }) => {
    const Component = isExternal ? 'a' : Link
    const props = isExternal ? { href, target: '_blank', rel: 'noopener noreferrer' } : { to }
    
    return (
        <Component {...props} className="portfolio-card">
            <div className="project-tag" style={{ background: bg, color: color }}>
                {category}
            </div>
            <h3 className="project-title">
                {title}
                <ChevronRight size={20} className="chevron" />
            </h3>
            <p className="project-desc">{desc}</p>
            <div className="try-link">
                {isExternal ? (
                    <>View external site <ExternalLink size={14} /></>
                ) : (
                    <>Try it live <ArrowRight size={14} /></>
                )}
            </div>
        </Component>
    )
}

// Items are {label, to} for in-app routes or {label, href} for the static
// pages. They used to be bare strings rendered as <li>s, so the whole footer
// was a list of words that looked like links and did nothing - which reads,
// to somebody deciding whether to get in touch, like a site that was
// abandoned halfway.
const FooterCol = ({ title, items }) => (
    <div className="footer-col">
        <h4>{title}</h4>
        <ul className="footer-list">
            {items.map(item => (
                <li key={item.label} className="footer-item">
                    {item.to
                        ? <Link to={item.to} className="footer-link">{item.label}</Link>
                        : <a href={item.href} className="footer-link">{item.label}</a>}
                </li>
            ))}
        </ul>
    </div>
)

// Only rendered for accounts that exist. An icon linking to "#" is worse than
// no icon: it invites a click and then does nothing.
const SocialLink = ({ icon, href }) => (
    href ? <a href={href} className="social-icon" target="_blank" rel="noreferrer">{icon}</a> : null
)

export default Home
