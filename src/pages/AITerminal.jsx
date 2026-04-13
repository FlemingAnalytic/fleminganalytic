import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Send, Bot, User, Trash2, Cpu, Zap, Activity } from 'lucide-react'
import { chatApi } from '../services/api'

const AITerminal = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Fleming Analytic Terminal V1.0 - All systems operational. How can I assist you today with market analysis or system queries?' }
    ])
    const [input, setInput] = useState('')
    const [isTyping, setIsTyping] = useState(false)
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async (e) => {
        e.preventDefault()
        if (!input.trim()) return

        const userMsg = { role: 'user', content: input }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setIsTyping(true)

        try {
            const result = await chatApi.query(input)
            const aiMsg = { 
                role: 'assistant', 
                content: result.response,
                model: result.model,
                stats: {
                    tokens: result.tokens,
                    tps: result.tokens_per_second,
                    duration: result.eval_duration_ms
                }
            }
            setMessages(prev => [...prev, aiMsg])
        } catch (err) {
            console.error('Chat error:', err)
            setMessages(prev => [...prev, { role: 'assistant', content: 'System Error: Error communicating with LLM engine. Please ensure the server is connected and Ollama is active.' }])
        } finally {
            setIsTyping(false)
        }
    }

    return (
        <div className="bg-slate-950 min-h-screen text-slate-100 font-sans tracking-tight">
            <main className="flex flex-col h-[calc(100vh-80px)] overflow-hidden">
                <header className="px-12 py-8 border-b border-white/5 flex justify-between items-center bg-slate-900/40">
                    <div>
                        <h2 className="text-2xl font-black tracking-tighter title-gradient flex items-center gap-4">
                            <Cpu size={24} className="opacity-50" /> AI INTELLIGENCE TERMINAL
                        </h2>
                        <p className="text-[10px] opacity-40 font-black uppercase tracking-widest leading-none mt-1">Llama 3.2:3b Core Active</p>
                    </div>
                    <div className="flex gap-6 items-center">
                        <TerminalStat icon={<Zap size={14} />} label="Response Time" value="1.2s" />
                        <TerminalStat icon={<Activity size={14} />} label="Signal Stability" value="100%" />
                        <button className="opacity-30 hover:opacity-100 transition p-2 hover:bg-white/5 rounded-xl">
                            <Trash2 size={20} onClick={() => setMessages([])} />
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto px-12 py-10 space-y-8 scrollbar-hide">
                    {messages.map((msg, i) => (
                        <motion.div 
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex gap-6 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center shrink-0 shadow-xl shadow-blue-500/10">
                                    <Bot size={24} className="text-white" />
                                </div>
                            )}
                            <div className={`max-w-3xl flex flex-col gap-3 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`px-8 py-6 rounded-3xl text-sm leading-relaxed shadow-lg font-medium ${
                                    msg.role === 'user' 
                                    ? 'bg-blue-600 text-white rounded-tr-sm' 
                                    : 'glass-panel bg-slate-900/60 rounded-tl-sm border border-white/10'
                                }`}>
                                    {msg.content}
                                </div>
                                {msg.stats && (
                                    <p className="text-[10px] opacity-20 font-black tracking-widest uppercase ml-4">
                                        Rendered: {msg.model || 'Unknown'} — {msg.stats.tokens || 0} tokens @ {msg.stats.tps || 0} tps
                                    </p>
                                )}
                            </div>
                            {msg.role === 'user' && (
                                <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center shrink-0 border border-white/10">
                                    <User size={24} className="text-white/60" />
                                </div>
                            )}
                        </motion.div>
                    ))}
                    {isTyping && (
                        <div className="flex gap-6 animate-pulse">
                             <div className="w-12 h-12 rounded-2xl bg-blue-600/20 flex items-center justify-center shrink-0">
                                    <Bot size={24} className="text-blue-400" />
                            </div>
                            <div className="glass-panel px-8 py-6 rounded-3xl rounded-tl-sm bg-blue-500/5 flex gap-2 items-center">
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60 animate-bounce"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60 animate-bounce delay-100"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-400/60 animate-bounce delay-200"></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <footer className="p-12 bg-slate-900/40 border-t border-white/5">
                    <form onSubmit={handleSend} className="relative group">
                        <input 
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Query the markets or system architecture..."
                            className="w-full bg-white/5 border border-white/10 rounded-3xl px-10 py-8 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500/40 transition-all duration-300 outline-none pr-32 font-bold text-sm tracking-tight shadow-inner placeholder:opacity-40"
                        />
                        <button 
                            type="submit" 
                            disabled={isTyping}
                            className="absolute right-4 top-4 bottom-4 px-8 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 font-black text-xs uppercase tracking-widest hover:shadow-xl hover:shadow-blue-500/20 transition-all duration-300 active:scale-95 disabled:opacity-50 flex items-center gap-3"
                        >
                            Analyze <Send size={16} />
                        </button>
                    </form>
                    <p className="text-center text-[10px] font-black uppercase tracking-widest opacity-20 mt-8">Intelligence Powered by Llama — Private Local Inference Mode Active</p>
                </footer>
            </main>
        </div>
    )
}

const TerminalStat = ({ icon, label, value }) => (
    <div className="flex items-center gap-4 border-r border-white/5 pr-6 last:border-0 last:pr-0">
        <div className="opacity-40">{icon}</div>
        <div>
            <p className="text-[9px] font-black uppercase tracking-widest opacity-30 leading-none">{label}</p>
            <p className="text-xs font-black tracking-tighter leading-none mt-1">{value}</p>
        </div>
    </div>
)

export default AITerminal
