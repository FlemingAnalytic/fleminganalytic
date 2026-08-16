import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ArrowLeft, Check, Send } from 'lucide-react';
import { contactApi } from '../services/api';

/**
 * Somewhere for the buttons to go.
 *
 * The server has had a working /contact endpoint the whole time. Every
 * call-to-action on this site was a bare <button> with no handler, so a
 * visitor who wanted to get in touch had no way to do it - which made the
 * wording of everything above it beside the point.
 *
 * The form asks for two things. Anything else is a field between somebody
 * wanting to talk and them talking.
 */
export default function Contact() {
    const location = useLocation();
    const [email, setEmail] = useState('');
    const [content, setContent] = useState('');
    const [website, setWebsite] = useState('');   // honeypot
    const [status, setStatus] = useState('idle'); // idle | sending | sent | error
    const [error, setError] = useState(null);

    const submit = async (e) => {
        e.preventDefault();
        if (!email || !content) return;
        setStatus('sending');
        setError(null);
        try {
            await contactApi.send({
                // Which page they came from arrives in the subject line, so a
                // reply has some context without the sender having to supply it.
                page: `fleminganalytic.com${location.state?.from || ''}`,
                email,
                content,
                website,
            });
            setStatus('sent');
        } catch (err) {
            setStatus('error');
            setError(
                err?.response?.status === 429
                    ? 'That is several messages in a short time. Try again in a little while.'
                    : 'That did not send. Email john.fleming@fleminganalytic.com directly and it will reach the same place.'
            );
        }
    };

    return (
        <div style={{ minHeight: 'calc(100vh - 80px)', background: '#050505' }}>
            <div style={{ maxWidth: 620, margin: '0 auto', padding: '72px 24px 96px' }}>
                <Link
                    to="/"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: '#7a7975',
                             fontSize: 13, textDecoration: 'none', marginBottom: 40 }}
                >
                    <ArrowLeft size={14} /> Back
                </Link>

                {status === 'sent' ? (
                    <div>
                        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                      width: 44, height: 44, borderRadius: 999,
                                      background: 'rgba(25,158,112,0.14)', color: '#199e70', marginBottom: 20 }}>
                            <Check size={20} />
                        </div>
                        <h1 style={{ fontSize: 30, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em', marginBottom: 12 }}>
                            That's arrived.
                        </h1>
                        <p style={{ fontSize: 15, lineHeight: 1.7, color: '#c3c2b7' }}>
                            You'll get a reply from a person, usually the same day. If it's urgent,
                            say so in a second message and it goes to the top.
                        </p>
                    </div>
                ) : (
                    <>
                        <h1 style={{ fontSize: 34, fontWeight: 600, color: '#fff', letterSpacing: '-0.02em', marginBottom: 12 }}>
                            Tell us what's slow.
                        </h1>
                        <p style={{ fontSize: 15, lineHeight: 1.7, color: '#c3c2b7', marginBottom: 32 }}>
                            The job that eats a day a week. The report nobody trusts. The thing you'd
                            hand to AI tomorrow, if only you could be sure the answer was right. One
                            conversation, no charge, and a straight answer about whether this is worth doing.
                        </p>

                        <form onSubmit={submit}>
                            <label style={labelStyle}>Your email</label>
                            <input
                                type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@yourcompany.com" style={inputStyle}
                            />

                            <label style={{ ...labelStyle, marginTop: 20 }}>What's the problem?</label>
                            <textarea
                                required rows={7} value={content} onChange={(e) => setContent(e.target.value)}
                                placeholder="A few sentences is plenty. What happens today, and what would better look like?"
                                style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.6 }}
                            />

                            {/* Honeypot. Hidden from people, off the tab order, and left
                                unlabelled for screen readers by aria-hidden - a bot fills it
                                in and the server quietly drops the message. */}
                            <div aria-hidden="true" style={{ position: 'absolute', left: '-9999px' }}>
                                <label>
                                    Website
                                    <input type="text" tabIndex={-1} autoComplete="off"
                                           value={website} onChange={(e) => setWebsite(e.target.value)} />
                                </label>
                            </div>

                            {error && (
                                <p style={{ marginTop: 16, fontSize: 13.5, color: '#e66767', lineHeight: 1.6 }}>{error}</p>
                            )}

                            <button
                                type="submit" disabled={status === 'sending'}
                                style={{
                                    marginTop: 24, display: 'inline-flex', alignItems: 'center', gap: 9,
                                    padding: '13px 22px', borderRadius: 10, border: 'none', cursor: 'pointer',
                                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', color: '#fff',
                                    fontSize: 14, fontWeight: 600,
                                    opacity: status === 'sending' ? 0.6 : 1,
                                }}
                            >
                                {status === 'sending' ? 'Sending…' : <>Send <Send size={15} /></>}
                            </button>
                        </form>

                        <p style={{ marginTop: 28, fontSize: 12.5, color: '#7a7975', lineHeight: 1.7 }}>
                            Or email <span style={{ color: '#c3c2b7' }}>john.fleming@fleminganalytic.com</span> —
                            it reaches the same inbox.
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}

const labelStyle = {
    display: 'block', fontSize: 12, fontWeight: 600, color: '#c3c2b7',
    textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8,
};

const inputStyle = {
    width: '100%', padding: '12px 14px', borderRadius: 10,
    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.10)',
    color: '#fff', fontSize: 14.5, outline: 'none', fontFamily: 'inherit',
};
