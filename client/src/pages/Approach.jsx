import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

/**
 * The pitch.
 *
 * Written to the house voice that already exists in the white paper, the
 * Mars landing page and the data-centre explainer: lead with the
 * conclusion, dismantle a vendor's cliche rather than the reader, treat
 * verifiability as the product, concede a point to buy credibility, and
 * close by reframing rather than summarising.
 *
 * Every number on this page was checked by loading the page in a browser
 * and asserting that something renders - not by its status code. This site
 * is a single-page app, so it answers 200 on every path including ones with
 * no route behind them, and an earlier version of this file claimed nineteen
 * applications on the strength of exactly that. Two of the nineteen painted
 * a navbar over an empty page.
 *
 * Eleven applications render and their APIs answer. Eight research reports
 * and four dashboards render. Three external domains render and present a
 * valid certificate - two others were dropped because theirs had expired.
 * The manual claim was verified by opening the generated screenshots.
 */
const PHASES = [
    {
        name: 'Scope',
        body: 'A week with whoever runs the process and whoever pays for it. What breaks, who it breaks for, and what "fixed" looks like on a Tuesday. Written down before anything is built.',
    },
    {
        name: 'Draft',
        body: 'AI does the first pass, directed carefully by someone who already knows what the output is supposed to look like. This is the fast part, and it is the part everybody else is selling you.',
    },
    {
        name: 'Review',
        body: 'A person reads every line and is answerable for it. This is the expensive part, the part that gets skipped, and the reason the rest is worth anything.',
    },
    {
        name: 'Hand over',
        body: 'Into production, in your stack, with a manual generated from the running software rather than written from memory. Software nobody can use is not a delivery.',
    },
];

export default function Approach() {
    return (
        <div style={{ background: '#050505', minHeight: 'calc(100vh - 80px)' }}>
            <article style={{ maxWidth: 720, margin: '0 auto', padding: '80px 24px 110px' }}>

                <p style={eyebrow}>Fleming Analytic Resources · How we work</p>

                <h1 style={{ fontSize: 44, lineHeight: 1.12, fontWeight: 600, letterSpacing: '-0.03em',
                             color: '#fff', margin: '0 0 28px' }}>
                    Somebody still has to read it.
                </h1>

                <p style={lead}>
                    Here's the pitch you've heard all year: AI will do the work of ten people.
                    It will. It will also do the work of ten people who don't know they're
                    wrong. Somebody still has to read it.
                </p>

                <p style={body}>
                    AI didn't remove the work. It moved it. The hours you used to spend
                    producing a draft are the hours you now spend deciding whether the draft
                    is true — and almost nobody has rebudgeted for that.
                </p>

                <p style={body}>
                    Do all of it by hand and you pay ten times over for the same output. Ship
                    all of it unread and you find out what was wrong from a customer. The
                    saving is real. It just isn't where the brochure says it is.
                </p>

                <p style={{ ...body, color: '#fff', fontWeight: 500 }}>
                    So that's what we sell: the reading.
                </p>

                <h2 style={h2}>Four steps</h2>
                <div style={{ margin: '0 0 44px' }}>
                    {PHASES.map((p) => (
                        <div key={p.name} style={{ display: 'flex', gap: 20, padding: '18px 0',
                                                   borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                            <div style={{ flex: '0 0 96px', fontSize: 15, fontWeight: 600, color: '#3987e5' }}>
                                {p.name}
                            </div>
                            <p style={{ margin: 0, fontSize: 15, lineHeight: 1.7, color: '#c3c2b7' }}>{p.body}</p>
                        </div>
                    ))}
                </div>

                <h2 style={h2}>You don't have to take our word for it</h2>

                <p style={body}>
                    Eleven working applications run on this site right now and you can open
                    every one of them without talking to anybody: a parish that runs its own
                    bulletin and website, a restaurant platform, a chess engine that plays
                    you, a double-entry ledger, a machine-learning workbench you can load
                    your own data into. Alongside them are eight research reports and four
                    data dashboards, equally open. Three more applications run on client
                    domains — including a ticketing site built so fans pay what the venue set
                    and nothing else.
                </p>

                <p style={body}>
                    Two of the admin systems ship with a manual whose screenshots are
                    captured from the running software, so when the software changes the
                    manual is re-run rather than rewritten. Some of all this was drafted by
                    AI — that is rather the point — and every line of it was read by someone
                    who had to answer for it.
                </p>

                <div style={aside}>
                    <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.7, color: '#c3c2b7' }}>
                        <strong style={{ color: '#fff', fontWeight: 600 }}>Credit where it's due:</strong>{' '}
                        none of that is clever. It's ordinary work done in the open, where you
                        can check it. That's the whole argument — press the buttons before you
                        spend a dollar.
                    </p>
                </div>

                <p style={{ ...body, marginTop: 40 }}>
                    Doing none of it by hand is how you end up with something confident and
                    wrong. Doing all of it by hand is how you end up late. The work is in the
                    middle.
                </p>

                <div style={{ marginTop: 44, paddingTop: 36, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                    <h2 style={{ ...h2, marginTop: 0 }}>Bring us the job you can't afford to get wrong</h2>
                    <p style={{ ...body, marginBottom: 26 }}>
                        The job that eats a day a week. The report nobody trusts. The thing
                        you'd hand to AI tomorrow, if only you could be sure the answer was
                        right. That's the one we want.
                    </p>
                    <Link to="/contact" state={{ from: '/approach' }} style={cta}>
                        Tell us what's slow <ArrowRight size={16} />
                    </Link>
                    <p style={{ marginTop: 16, fontSize: 12.5, color: '#7a7975' }}>
                        One conversation, no charge, and a straight answer about whether this
                        is worth doing at all.
                    </p>
                    <p style={{ marginTop: 22, fontSize: 12.5, color: '#7a7975' }}>
                        Or take it with you:{' '}
                        <a href="/pitch/fleming-analytic-onepager.pdf"
                           style={{ color: '#3987e5', textDecoration: 'none', fontWeight: 600 }}>
                            the one-page version (PDF)
                        </a>
                        .
                    </p>
                </div>
            </article>
        </div>
    );
}

const eyebrow = {
    fontSize: 11, fontWeight: 600, letterSpacing: '0.18em', textTransform: 'uppercase',
    color: '#7a7975', margin: '0 0 22px',
};
const lead = { fontSize: 19, lineHeight: 1.65, color: '#fff', margin: '0 0 22px', fontWeight: 400 };
const body = { fontSize: 16, lineHeight: 1.75, color: '#c3c2b7', margin: '0 0 20px' };
const h2 = {
    fontSize: 13, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase',
    color: '#7a7975', margin: '52px 0 4px',
};
const aside = {
    marginTop: 8, padding: '18px 20px', borderLeft: '2px solid #3987e5',
    background: 'rgba(255,255,255,0.025)', borderRadius: '0 8px 8px 0',
};
const cta = {
    display: 'inline-flex', alignItems: 'center', gap: 9, padding: '13px 22px',
    borderRadius: 10, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    color: '#fff', fontSize: 14.5, fontWeight: 600, textDecoration: 'none',
};
